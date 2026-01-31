"""Run class for orchestrating experiment logging with background worker thread."""

import atexit
import logging
import os
import signal
import threading
from queue import Empty, Full, Queue
from typing import Any, cast

from expt_logger.buffer import Buffer
from expt_logger.client import APIClient
from expt_logger.config import Config
from expt_logger.env import (
    get_api_key,
    get_base_url,
    get_experiment_id,
    get_experiment_id_file_path,
)
from expt_logger.exceptions import APIError
from expt_logger.types import (
    CommitCommand,
    ConfigUpdateCommand,
    LogCommand,
    LogRolloutCommand,
    MessageItem,
    RewardItem,
    RolloutItem,
    ShutdownCommand,
)

logger = logging.getLogger(__name__)


class Run:
    """Orchestrates experiment logging with background worker thread.

    Manages:
    - API client for server communication
    - Command queue (bounded at 10,000 items)
    - Background worker thread for processing commands
    - Buffer for batching metrics/rollouts
    - Step counter (owned by worker thread)
    - Lifecycle management (signal handlers, atexit)
    """

    def __init__(
        self,
        name: str | None = None,
        config: dict[str, Any] | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        is_main_process: bool = True,
        experiment_id: str | None = None,
    ):
        """Initialize Run and start background worker.

        Args:
            name: Optional experiment name
            config: Optional experiment configuration
            api_key: Optional API key (defaults to EXPT_LOGGER_API_KEY env var)
            base_url: Optional base URL (defaults to EXPT_LOGGER_BASE_URL env var or https://app.cgft.io)
            is_main_process: Whether this is the main process creating the experiment.
        """
        # Resolve API key and base URL from environment if not provided
        resolved_api_key = get_api_key(override=api_key)
        resolved_base_url = get_base_url(override=base_url)

        # Create API client
        self._client = APIClient(base_url=resolved_base_url, api_key=resolved_api_key)
        self._base_url = resolved_base_url

        # Store whether this is the main process
        self._is_main_process = is_main_process

        if not is_main_process:
            # Subprocess: must attach to existing experiment
            # Uses cascading: override -> env var -> temp file
            resolved_experiment_id = get_experiment_id(experiment_id, is_main_process=False)
            if resolved_experiment_id is not None:
                self._experiment_id = resolved_experiment_id
                self._validate_and_attach_experiment(config=config)
                logger.info(
                    f"[expt_logger] Attached to experiment ID: {self._experiment_id} (subprocess)"
                )
            else:
                raise RuntimeError("Experiment ID not found in temp folder.")
        else:
            # Main process: check if we're attaching to an existing experiment or creating new
            # Uses cascading: override -> env var (skips temp file)
            existing_experiment_id = get_experiment_id(experiment_id, is_main_process=True)

            if existing_experiment_id is not None:
                # Attach to existing experiment
                self._experiment_id = existing_experiment_id
                self._validate_and_attach_experiment(config=config)
                logger.info(
                    f"[expt_logger] Attaching to existing experiment ID: {self._experiment_id}"
                )
            else:
                # Create new experiment on server
                self._experiment_id = self._client.create_experiment(name=name, config=config)
                logger.info(f"[expt_logger] Created new experiment ID: {self._experiment_id}")

            # Set expt id with envvar and folder for subprocess discovery
            os.environ["EXPT_LOGGER_EXPERIMENT_ID"] = self._experiment_id
            experiment_id_file = get_experiment_id_file_path()
            with open(experiment_id_file, "w") as f:
                f.write(self._experiment_id)

        # Create bounded command queue (10,000 items max)
        self._queue: Queue[tuple[str, Any]] = Queue(maxsize=10000)

        # Create Config instance with queue for auto-sync
        self._config = Config(initial_data=config, queue=self._queue)

        # Worker thread state (owned by worker)
        self._step = 0
        self._buffer = Buffer(step=self._step)

        # Shutdown flag
        self._shutdown_event = threading.Event()
        self._worker_thread: threading.Thread | None = None

        # Start worker thread
        self._start_worker()

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Register atexit handler
        atexit.register(self._atexit_handler)

    def _start_worker(self) -> None:
        """Start the background worker thread."""
        self._worker_thread = threading.Thread(
            target=self._worker_loop, daemon=True, name="expt-logger-worker"
        )
        self._worker_thread.start()

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, shutting down...")
        self.end()

    def _atexit_handler(self) -> None:
        """Handle process exit."""
        if not self._shutdown_event.is_set():
            logger.debug("atexit handler triggered, shutting down...")
            self.end()

    @property
    def experiment_url(self) -> str:
        """Get the URL for viewing this experiment.

        Returns:
            Full URL to experiment page
        """
        # Always use the production frontend URL
        return f"{self._base_url}/experiments/{self._experiment_id}"

    @property
    def base_url(self) -> str:
        """Get the base URL of the API server.

        Returns:
            Base URL string
        """
        return self._base_url

    @property
    def config(self) -> Config:
        """Get the configuration object. Only available in main process.

        Returns:
            Config instance
        """
        if self._is_main_process:
            return self._config
        raise RuntimeError("Config is only available in the main process.")

    def log(
        self,
        metrics: dict[str, float],
        step: int | None = None,
        mode: str | None = None,
        commit: bool = True,
    ) -> None:
        """Log scalar metrics.

        Args:
            metrics: Dictionary of metric name -> value
            step: Optional step number (overrides worker's step counter if provided)
            mode: Optional mode (e.g., "train", "eval")
            commit: Whether to flush buffer after logging
        """
        from expt_logger.validation import validate_metrics, validate_mode, validate_step

        # Validate inputs
        validate_metrics(metrics)
        validate_step(step)
        validate_mode(mode)

        # Enqueue log command for each metric
        for name, value in metrics.items():
            log_cmd: LogCommand = {"name": name, "value": value, "mode": mode, "step": step}
            try:
                self._queue.put_nowait(("log", log_cmd))
            except Full:
                logger.warning(f"Command queue full, dropping metric: {name}={value} (mode={mode})")

        if commit:
            self.commit()

    def log_rollout(
        self,
        prompt: str | dict[str, str],
        messages: list[dict[str, str]],
        rewards: dict[str, float],
        step: int | None = None,
        mode: str | None = None,
        commit: bool = True,
    ) -> None:
        """Log a rollout (conversation + rewards).

        Args:
            prompt: The prompt text (str) or dict with 'content' key
            messages: List of message dicts with 'role' and 'content'
            rewards: Dictionary of reward name -> value
            step: Optional step number (overrides worker's step counter if provided)
            mode: Optional mode (defaults to "train")
            commit: Whether to flush buffer after logging
        """
        from expt_logger.validation import (
            validate_messages,
            validate_mode,
            validate_prompt,
            validate_rewards,
            validate_step,
        )

        # Validate and process prompt
        prompt_text = validate_prompt(prompt)

        # Validate other inputs
        validate_messages(messages)
        validate_rewards(rewards)
        validate_step(step)
        validate_mode(mode)

        # Convert messages to MessageItem format
        message_items: list[MessageItem] = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]

        # Convert rewards to list of RewardItem
        reward_items: list[RewardItem] = [
            {"name": name, "value": value} for name, value in rewards.items()
        ]

        # Create LogRolloutCommand
        rollout_cmd: LogRolloutCommand = {
            "prompt": prompt_text,
            "messages": message_items,
            "rewards": reward_items,
            "mode": mode or "train",
            "step": step,
        }

        try:
            self._queue.put_nowait(("log_rollout", rollout_cmd))
        except Full:
            logger.warning(f"Command queue full, dropping rollout: {prompt_text[:50]}...")

        if commit:
            self.commit()

    def commit(self) -> None:
        """Explicitly commit (flush) the current buffer."""
        commit_cmd: CommitCommand = {}
        try:
            self._queue.put_nowait(("commit", commit_cmd))
        except Full:
            logger.warning("Command queue full, dropping commit command")

    def end(self, timeout: float = 20.0) -> None:
        """Gracefully shut down the run.

        Waits for all queued commands to be processed before shutdown.
        This ensures that all logged data is persisted to the server.

        Args:
            timeout: Maximum time to wait for queue to drain and worker to finish (seconds).
                    Default is 20 seconds. Set to 0 for immediate shutdown (may lose data).
        """
        if self._shutdown_event.is_set():
            return

        # Delete experiment ID file in temp folder
        experiment_id_file = get_experiment_id_file_path()
        if os.path.isfile(experiment_id_file):
            try:
                os.remove(experiment_id_file)
            except Exception as e:
                logger.warning(f"Error removing experiment ID file: {e}")

        # Wait for queue to drain (with timeout)
        import time

        start_time = time.time()
        queue_timeout = timeout * 0.8  # Use 80% of timeout for queue draining
        while not self._queue.empty() and (time.time() - start_time) < queue_timeout:
            time.sleep(0.05)  # Poll every 50ms

        # Warn if queue still has items
        remaining = self._queue.qsize()
        if remaining > 0:
            logger.warning(
                f"Shutting down with {remaining} commands still queued. "
                f"Some data may be lost. Consider increasing timeout (current: {timeout}s)"
            )

        # Signal shutdown
        self._shutdown_event.set()

        # Enqueue shutdown command
        shutdown_cmd: ShutdownCommand = {}
        try:
            self._queue.put_nowait(("shutdown", shutdown_cmd))
        except Full:
            logger.warning("Command queue full, forcing shutdown")

        # Wait for worker thread to finish (use remaining timeout)
        worker_timeout = max(0.1, timeout - (time.time() - start_time))
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=worker_timeout)
            if self._worker_thread.is_alive():
                logger.warning(f"Worker thread did not finish within {timeout}s")

        # Close API client session
        self._client.close()

    def _worker_loop(self) -> None:
        """Main worker thread loop.

        Processes commands from queue until shutdown.
        """
        try:
            while not self._shutdown_event.is_set():
                try:
                    # Block for up to 0.1s waiting for command
                    command, data = self._queue.get(timeout=0.1)

                    # Process command
                    try:
                        if command == "log":
                            self._handle_log(cast(LogCommand, data))
                        elif command == "log_rollout":
                            self._handle_log_rollout(cast(LogRolloutCommand, data))
                        elif command == "commit":
                            self._handle_commit()
                        elif command == "config_update":
                            self._handle_config_update(cast(ConfigUpdateCommand, data))
                        elif command == "shutdown":
                            logger.debug("Received shutdown command")
                            break
                        else:
                            logger.warning(f"Unknown command: {command}")
                    except Exception as e:
                        logger.error(f"Error processing command {command}: {e}", exc_info=True)

                except Empty:
                    # Timeout, loop again to check shutdown flag
                    continue

            # Shutdown: flush remaining buffer
            logger.debug("Worker shutting down, flushing buffer...")
            self._flush_buffer()

            # Mark experiment complete
            try:
                self._client.update_experiment(self._experiment_id, status="complete")
                logger.debug("Experiment marked complete")
            except Exception as e:
                logger.error(f"Error marking experiment complete: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Worker thread crashed: {e}", exc_info=True)

    def _validate_and_attach_experiment(
        self,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Validate experiment exists and activate it.

        Args:
            config: Optional config to sync to server

        Raises:
            APIError: If experiment doesn't exist or request fails
        """
        # Validate experiment exists
        try:
            experiment_data = self._client.get_experiment(self._experiment_id)
            logger.debug(f"Validated experiment exists: {experiment_data.get('name', 'unnamed')}")
        except APIError as e:
            if e.status_code == 404:
                raise APIError(
                    f"Experiment '{self._experiment_id}' not found. "
                    f"Cannot attach to non-existent experiment.",
                    status_code=404,
                )
            raise

        # Set status to active and optionally update config
        self._client.update_experiment(
            self._experiment_id,
            status="active",
            config=config,
        )
        logger.debug("Set experiment status to active")

    def _override_step(self, step: int) -> None:
        """Override the current step counter.

        Args:
            step: New step number
        """
        # Flush current buffer if not empty
        if not self._buffer.is_empty():
            self._flush_buffer()
        # Set new step and create new buffer
        self._step = step
        self._buffer = Buffer(step=self._step)

    def _handle_log(self, data: LogCommand) -> None:
        """Handle log command.

        Args:
            data: Log command data with name, value, mode, step, and commit
        """
        # If step override is provided and different from current step
        step = data["step"]
        if step is not None and step != self._step:
            self._override_step(step)

        self._buffer.add_scalar(data["name"], data["value"], data["mode"])

    def _handle_log_rollout(self, data: LogRolloutCommand) -> None:
        """Handle log_rollout command.

        Args:
            data: Log rollout command data with prompt, messages, rewards, mode, step, and commit
        """
        # If step override is provided and different from current step
        step = data["step"]
        if step is not None and step != self._step:
            self._override_step(step)

        # Create RolloutItem with current step and mode
        rollout: RolloutItem = {
            "step": self._step,
            "mode": data["mode"],
            "promptText": data["prompt"],
            "messages": data["messages"],
            "rewards": data["rewards"],
        }

        self._buffer.add_rollout(rollout)

    def _handle_commit(self) -> None:
        """Handle commit command. Flush buffer and increment step."""

        self._flush_buffer()
        self._step += 1
        self._buffer = Buffer(step=self._step)

    def _handle_config_update(self, data: ConfigUpdateCommand) -> None:
        """Handle config update command.

        Args:
            data: Config update command data with updates dict
        """
        try:
            self._client.update_experiment(self._experiment_id, config=data["updates"])
        except Exception as e:
            logger.error(f"Error updating config on server: {e}", exc_info=True)

    def _flush_buffer(self) -> None:
        """Flush current buffer to server."""
        if self._buffer.is_empty():
            return

        scalars, rollouts = self._buffer.get_and_clear()

        # Send scalars if any
        if scalars:
            try:
                self._client.log_scalars(self._experiment_id, scalars)
                logger.debug(f"Flushed {len(scalars)} scalars at step {self._step}")
            except Exception as e:
                logger.error(f"Error logging scalars: {e}", exc_info=True)

        # Send rollouts if any
        if rollouts:
            try:
                self._client.log_rollouts(self._experiment_id, rollouts)
                logger.debug(f"Flushed {len(rollouts)} rollouts at step {self._step}")
            except Exception as e:
                logger.error(f"Error logging rollouts: {e}", exc_info=True)

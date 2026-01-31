"""Buffer for batching metrics and rollouts before flushing to API."""

import logging

from expt_logger.types import RolloutItem, ScalarItem

logger = logging.getLogger(__name__)


class Buffer:
    """Buffer for accumulating metrics and rollouts at the current step."""

    def __init__(self, step: int = 0) -> None:
        """Initialize empty buffer.

        Args:
            step: The current step number for this buffer
        """
        self._step = step
        self._scalars: dict[str, float] = {}  # full_key (mode/metric) -> value
        self._rollouts: list[RolloutItem] = []

    def add_scalar(self, name: str, value: float, mode: str | None = None) -> None:
        """Add a scalar metric to the buffer.

        Handles mode and name de-conflicting:
        - If mode is provided, always use the provided mode
        - If mode is provided and name is "xxx/*", and xxx == mode, then name becomes *
        - If mode is provided and name is "xxx/*", and xxx != mode, name stays full
        - If mode is not provided and name is "xxx/*", then name becomes *
        - If mode is not provided and name has no "/", then mode defaults to "train"

        Args:
            key: Metric key (e.g., "loss" or "train/loss")
            value: Metric value
            mode: Optional mode (e.g., "train", "eval")
        """
        if mode is not None:
            # Mode is provided, always use it
            if "/" in name:
                name_mode, metric_name = name.split("/", 1)
                # If name mode matches provided mode, strip the prefix
                if name_mode == mode:
                    final_name = metric_name
                else:
                    # Mode mismatch, keep full name as name
                    final_name = name
            else:
                # No "/" in key, use key as-is
                final_name = name
            full_key = f"{mode}/{final_name}"
        else:
            # Mode is not provided
            if "/" in name:
                # Name is "xxx/*", extract and use * as name
                name_mode, metric_name = name.split("/", 1)
                mode = name_mode
                final_name = metric_name
                full_key = f"{mode}/{final_name}"
            else:
                # No "/" in key, default mode to "train"
                mode = "train"
                full_key = f"{mode}/{name}"

        # Last write wins - warn if overwriting
        if full_key in self._scalars:
            logger.warning(
                f"Overwriting metric '{full_key}' at same step "
                f"(old value: {self._scalars[full_key]}, new value: {value})"
            )

        self._scalars[full_key] = value

    def add_rollout(self, rollout: RolloutItem) -> None:
        """Add a rollout to the buffer.

        Args:
            rollout: Rollout item with step, mode, promptText, messages, and rewards
        """
        self._rollouts.append(rollout)

    def get_and_clear(self) -> tuple[list[ScalarItem], list[RolloutItem]]:
        """Get all buffered data and clear the buffer.

        Returns:
            Tuple of (list of ScalarItem, list of RolloutItem)
        """
        # Convert scalars dict to list of ScalarItem
        scalar_items: list[ScalarItem] = []
        for full_key, value in self._scalars.items():
            # Parse mode/name from full_key
            mode, name = full_key.split("/", 1)
            scalar_items.append(
                {
                    "step": self._step,
                    "mode": mode,
                    "name": name,
                    "value": value,
                }
            )

        rollouts = self._rollouts.copy()

        self._scalars.clear()
        self._rollouts.clear()

        return scalar_items, rollouts

    def is_empty(self) -> bool:
        """Check if buffer has any data.

        Returns:
            True if buffer is empty, False otherwise
        """
        return not self._scalars and not self._rollouts

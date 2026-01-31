"""Tests for Run class."""

import os
import queue
import signal
import tempfile
import threading
import time
from unittest.mock import Mock, patch

import pytest

from expt_logger.exceptions import APIError
from expt_logger.run import Run


@pytest.fixture
def mock_client(monkeypatch):
    """Create a mock APIClient that returns a fake experiment ID."""
    # Clear environment variable to prevent cross-test pollution
    monkeypatch.delenv("EXPT_LOGGER_EXPERIMENT_ID", raising=False)

    with patch("expt_logger.run.APIClient") as MockClient:
        client_instance = Mock()
        client_instance.create_experiment.return_value = "test-exp-id"
        MockClient.return_value = client_instance
        yield MockClient, client_instance


def test_run_initialization(mock_client):
    """Test Run initializes correctly and creates experiment."""
    MockClient, client_instance = mock_client

    run = Run(
        name="test-run",
        config={"lr": 0.001},
        api_key="test-key",
        base_url="https://test.example.com",
    )

    # Verify client was created with correct args
    MockClient.assert_called_once_with(base_url="https://test.example.com", api_key="test-key")

    # Verify experiment was created
    client_instance.create_experiment.assert_called_once()
    call_kwargs = client_instance.create_experiment.call_args.kwargs
    assert call_kwargs["name"] == "test-run"
    assert call_kwargs["config"] == {"lr": 0.001}

    # Verify worker thread started
    assert run._worker_thread is not None
    assert run._worker_thread.is_alive()
    assert run._worker_thread.daemon is True

    # Cleanup
    run.end()


def test_run_properties(mock_client):
    """Test Run properties return correct values."""
    _, _ = mock_client

    run = Run(
        name="test-run",
        config={"lr": 0.001, "batch_size": 32},
        api_key="test-key",
        base_url="https://test.example.com",
    )

    # Test experiment_url uses the base_url
    assert run.experiment_url == "https://test.example.com/experiments/test-exp-id"

    # Test base_url
    assert run.base_url == "https://test.example.com"

    # Test config
    assert run.config["lr"] == 0.001
    assert run.config["batch_size"] == 32

    run.end()


def test_log_enqueues_commands(mock_client):
    """Test log() enqueues log commands correctly."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log multiple metrics without committing
    run.log({"loss": 0.5, "accuracy": 0.9}, mode="train", commit=False)

    # Give worker time to process (but it shouldn't flush yet)
    time.sleep(0.05)

    # Worker processed commands, but shouldn't have flushed
    assert not client_instance.log_scalars.called

    # Now commit to verify data was buffered
    run.commit()
    time.sleep(0.1)

    # Now it should be flushed
    assert client_instance.log_scalars.called

    run.end()


def test_log_with_commit_enqueues_commit(mock_client):
    """Test log() with commit=True enqueues commit command."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log with commit
    run.log({"loss": 0.5}, commit=True)

    # Give worker time to process
    time.sleep(0.1)

    # Verify log_scalars was called
    assert client_instance.log_scalars.called

    run.end()


def test_log_rollout_enqueues_correctly(mock_client):
    """Test log_rollout() enqueues rollout command correctly."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log rollout
    run.log_rollout(
        prompt="Test prompt",
        messages=[{"role": "assistant", "content": "Response"}],
        rewards={"quality": 0.9},
        mode="train",
        commit=True,
    )

    # Give worker time to process
    time.sleep(0.1)

    # Verify log_rollouts was called
    assert client_instance.log_rollouts.called
    call_args = client_instance.log_rollouts.call_args
    rollouts = call_args[0][1]  # Second positional arg
    assert len(rollouts) == 1
    assert rollouts[0]["promptText"] == "Test prompt"
    assert rollouts[0]["mode"] == "train"
    assert rollouts[0]["step"] == 0
    assert len(rollouts[0]["rewards"]) == 1
    assert rollouts[0]["rewards"][0]["name"] == "quality"

    run.end()


def test_commit_flushes_buffer(mock_client):
    """Test commit() flushes buffered data."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log without commit
    run.log({"loss": 0.5}, commit=False)
    run.log({"accuracy": 0.9}, commit=False)

    # Commit explicitly
    run.commit()

    # Give worker time to process
    time.sleep(0.1)

    # Verify log_scalars was called with both metrics
    assert client_instance.log_scalars.called
    call_args = client_instance.log_scalars.call_args
    scalars = call_args[0][1]  # Second positional arg
    assert len(scalars) == 2

    run.end()


def test_buffer_accumulation_without_commit(mock_client):
    """Test that metrics accumulate in buffer without commit."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log multiple times without commit
    run.log({"metric1": 1.0}, commit=False)
    run.log({"metric2": 2.0}, commit=False)
    run.log({"metric3": 3.0}, commit=False)

    # Give worker time to process commands
    time.sleep(0.1)

    # log_scalars should not have been called yet
    # (or if called, only once when we commit)
    assert not client_instance.log_scalars.called

    # Now commit
    run.commit()
    time.sleep(0.1)

    # Now it should be called
    assert client_instance.log_scalars.called
    call_args = client_instance.log_scalars.call_args
    scalars = call_args[0][1]
    assert len(scalars) == 3

    run.end()


def test_queue_full_handling(mock_client):
    """Test that queue full is handled gracefully with warning."""
    _, _ = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Fill the queue (maxsize=10000)
    # We'll mock the queue to have a small maxsize for testing
    run._queue = queue.Queue(maxsize=2)

    with patch("expt_logger.run.logger") as mock_logger:
        # Fill queue
        run.log({"m1": 1.0}, commit=False)
        run.log({"m2": 2.0}, commit=False)

        # This should trigger queue full warning
        run.log({"m3": 3.0}, commit=False)

        # Check warning was logged
        assert mock_logger.warning.called
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "queue full" in warning_msg.lower()

    run.end()


def test_worker_processes_commands_in_order(mock_client):
    """Test worker thread processes commands in order."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log multiple metrics at different "steps"
    run.log({"step0": 0.0}, commit=True)  # Step 0, commit
    run.log({"step1": 1.0}, commit=True)  # Step 1, commit
    run.log({"step2": 2.0}, commit=True)  # Step 2, commit

    # Give worker time to process
    time.sleep(0.2)

    # Verify log_scalars was called 3 times
    assert client_instance.log_scalars.call_count >= 3

    # Check the step numbers in the calls
    calls = client_instance.log_scalars.call_args_list
    assert calls[0][0][1][0]["step"] == 0
    assert calls[1][0][1][0]["step"] == 1
    assert calls[2][0][1][0]["step"] == 2

    run.end()


def test_config_auto_sync(mock_client):
    """Test config changes are auto-synced to server."""
    _, client_instance = mock_client

    run = Run(
        name="test-run",
        config={"lr": 0.001},
        api_key="test-key",
        base_url="https://test.example.com",
    )

    # Update config
    run.config["batch_size"] = 64

    # Give worker time to process
    time.sleep(0.1)

    # Verify update_experiment was called with config updates
    client_instance.update_experiment.assert_called()
    # Check that one of the calls included config with batch_size
    calls_with_config = [
        call for call in client_instance.update_experiment.call_args_list
        if call.kwargs.get("config") and "batch_size" in call.kwargs["config"]
    ]
    assert len(calls_with_config) > 0

    run.end()


def test_graceful_shutdown_flushes_buffer(mock_client):
    """Test end() waits for buffer to flush."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log some data without committing
    run.log({"loss": 0.5}, commit=False)

    # End the run
    run.end()

    # Verify buffer was flushed (log_scalars called)
    assert client_instance.log_scalars.called

    # Verify experiment was marked complete
    client_instance.update_experiment.assert_called()
    call_kwargs = client_instance.update_experiment.call_args.kwargs
    assert call_kwargs.get("status") == "complete"


def test_end_marks_experiment_complete(mock_client):
    """Test end() marks experiment as complete."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")
    run.end()

    # Verify update_experiment was called with status="complete"
    client_instance.update_experiment.assert_called_once()
    call_kwargs = client_instance.update_experiment.call_args.kwargs
    assert call_kwargs.get("status") == "complete"


def test_end_closes_client_session(mock_client):
    """Test end() closes the API client session."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")
    run.end()

    # Verify client.close() was called
    client_instance.close.assert_called_once()


def test_end_is_idempotent(mock_client):
    """Test calling end() multiple times is safe."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Call end multiple times
    run.end()
    run.end()
    run.end()

    # Should only close once
    assert client_instance.close.call_count == 1


def test_worker_thread_error_handling(mock_client):
    """Test worker thread catches and logs exceptions without crashing."""
    _, client_instance = mock_client

    # Make log_scalars raise an error
    client_instance.log_scalars.side_effect = APIError("Server error")

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with patch("expt_logger.run.logger") as mock_logger:
        # Log something that will trigger the error
        run.log({"loss": 0.5}, commit=True)

        # Give worker time to process and handle error
        time.sleep(0.2)

        assert run._worker_thread is not None

        # Worker should still be alive
        assert run._worker_thread.is_alive()

        # Error should be logged
        assert mock_logger.error.called

    run.end()


def test_worker_continues_after_error(mock_client):
    """Test worker continues processing after an error."""
    _, client_instance = mock_client

    # Make first call fail, second succeed
    client_instance.log_scalars.side_effect = [
        APIError("Server error"),
        None,  # Success
    ]

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log twice
    run.log({"loss1": 0.5}, commit=True)
    run.log({"loss2": 0.3}, commit=True)

    # Give worker time to process
    time.sleep(0.2)

    # Both calls should have been attempted
    assert client_instance.log_scalars.call_count >= 2

    run.end()


def test_thread_safety_concurrent_logs(mock_client):
    """Test concurrent log calls from multiple threads."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    def log_worker(thread_id):
        for i in range(10):
            run.log({f"metric_{thread_id}_{i}": float(i)}, commit=False)

    # Start multiple threads logging concurrently
    threads = [threading.Thread(target=log_worker, args=(i,)) for i in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Commit all
    run.commit()
    time.sleep(0.2)

    # Should have logged all metrics
    assert client_instance.log_scalars.called

    run.end()


def test_signal_handler_registered(mock_client):
    """Test signal handlers are registered."""
    with patch("signal.signal") as mock_signal:
        _, client_instance = mock_client

        run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

        # Verify signal handlers were registered
        signal_calls = [call[0][0] for call in mock_signal.call_args_list]
        assert signal.SIGINT in signal_calls
        assert signal.SIGTERM in signal_calls

        run.end()


def test_atexit_handler_registered(mock_client):
    """Test atexit handler is registered."""
    with patch("atexit.register") as mock_atexit:
        _, client_instance = mock_client

        run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

        # Verify atexit handler was registered
        mock_atexit.assert_called_once()

        run.end()


def test_step_increment_on_commit(mock_client):
    """Test step counter increments on commit."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log and commit multiple times
    run.log({"m1": 1.0}, commit=True)
    run.log({"m2": 2.0}, commit=True)
    run.log({"m3": 3.0}, commit=True)

    time.sleep(0.2)

    # Check step numbers
    calls = client_instance.log_scalars.call_args_list
    assert len(calls) >= 3
    assert calls[0][0][1][0]["step"] == 0
    assert calls[1][0][1][0]["step"] == 1
    assert calls[2][0][1][0]["step"] == 2

    run.end()


def test_mixed_scalars_and_rollouts(mock_client):
    """Test logging both scalars and rollouts in same step."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log scalar
    run.log({"loss": 0.5}, commit=False)

    # Log rollout
    run.log_rollout(
        prompt="Test",
        messages=[{"role": "assistant", "content": "Response"}],
        rewards={"quality": 0.9},
        commit=False,
    )

    # Log another scalar
    run.log({"accuracy": 0.8}, commit=False)

    # Commit all
    run.commit()
    time.sleep(0.2)

    # Both should be called
    assert client_instance.log_scalars.called
    assert client_instance.log_rollouts.called

    # Check they have the same step
    scalar_step = client_instance.log_scalars.call_args[0][1][0]["step"]
    rollout_step = client_instance.log_rollouts.call_args[0][1][0]["step"]
    assert scalar_step == rollout_step == 0

    run.end()


def test_default_base_url(mock_client, monkeypatch):
    """Test default base URL is used when not provided."""
    MockClient, _ = mock_client

    # Remove base URL from environment to test default
    monkeypatch.delenv("EXPT_LOGGER_BASE_URL", raising=False)

    run = Run(name="test-run", api_key="test-key")

    # Check default base URL
    MockClient.assert_called_once_with(base_url="https://app.cgft.io", api_key="test-key")

    run.end()


def test_no_api_key(mock_client, monkeypatch):
    """Test Run raises ConfigurationError without API key."""
    from expt_logger.exceptions import ConfigurationError

    MockClient, _ = mock_client

    # Remove API key from environment
    monkeypatch.delenv("EXPT_LOGGER_API_KEY", raising=False)

    # Should raise ConfigurationError
    with pytest.raises(ConfigurationError) as exc_info:
        Run(name="test-run", base_url="https://test.example.com")

    assert "API key not found" in str(exc_info.value)


def test_api_key_from_env(mock_client, monkeypatch):
    """Test API key is loaded from environment variable."""
    MockClient, _ = mock_client

    # Set API key in environment
    monkeypatch.setenv("EXPT_LOGGER_API_KEY", "env-api-key")

    run = Run(name="test-run", base_url="https://test.example.com")

    # Check env API key was used
    MockClient.assert_called_once_with(base_url="https://test.example.com", api_key="env-api-key")

    run.end()


def test_api_key_override_takes_precedence(mock_client, monkeypatch):
    """Test explicit API key overrides environment variable."""
    MockClient, _ = mock_client

    # Set API key in environment
    monkeypatch.setenv("EXPT_LOGGER_API_KEY", "env-api-key")

    run = Run(name="test-run", api_key="override-key", base_url="https://test.example.com")

    # Check override key was used
    MockClient.assert_called_once_with(base_url="https://test.example.com", api_key="override-key")

    run.end()


def test_base_url_from_env(mock_client, monkeypatch):
    """Test base URL is loaded from environment variable."""
    MockClient, _ = mock_client

    # Set base URL in environment
    monkeypatch.setenv("EXPT_LOGGER_BASE_URL", "https://env.example.com")

    run = Run(name="test-run", api_key="test-key")

    # Check env base URL was used
    MockClient.assert_called_once_with(base_url="https://env.example.com", api_key="test-key")

    run.end()


def test_base_url_override_takes_precedence(mock_client, monkeypatch):
    """Test explicit base URL overrides environment variable."""
    MockClient, _ = mock_client

    # Set base URL in environment
    monkeypatch.setenv("EXPT_LOGGER_BASE_URL", "https://env.example.com")

    run = Run(name="test-run", api_key="test-key", base_url="https://override.example.com")

    # Check override URL was used
    MockClient.assert_called_once_with(base_url="https://override.example.com", api_key="test-key")

    run.end()


def test_empty_commit_does_not_flush(mock_client):
    """Test that committing with empty buffer doesn't call API."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Commit without logging anything
    run.commit()
    time.sleep(0.1)

    # Should not call log_scalars or log_rollouts
    assert not client_instance.log_scalars.called
    assert not client_instance.log_rollouts.called

    run.end()


def test_worker_shutdown_timeout(mock_client):
    """Test worker shutdown respects timeout."""
    _, client_instance = mock_client

    # Make worker slow to respond
    def slow_log(*args, **kwargs):
        time.sleep(5)

    client_instance.log_scalars.side_effect = slow_log

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Queue a long-running task
    run.log({"loss": 0.5}, commit=True)

    # End with short timeout
    start = time.time()
    run.end(timeout=0.5)
    elapsed = time.time() - start

    # Should timeout around 0.5s, not wait for full 5s
    assert elapsed < 2.0  # Give some buffer


def test_log_with_step_override(mock_client):
    """Test that providing step parameter overrides automatic step counter."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log at custom steps
    run.log({"metric1": 1.0}, step=10, commit=True)
    run.log({"metric2": 2.0}, step=20, commit=True)
    run.log({"metric3": 3.0}, step=15, commit=True)

    time.sleep(0.2)

    # Check the step numbers match what we provided
    calls = client_instance.log_scalars.call_args_list
    assert len(calls) >= 3
    assert calls[0][0][1][0]["step"] == 10
    assert calls[1][0][1][0]["step"] == 20
    assert calls[2][0][1][0]["step"] == 15

    run.end()


def test_log_rollout_with_step_override(mock_client):
    """Test that providing step parameter for rollout overrides automatic step counter."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Log rollout at custom step
    run.log_rollout(
        prompt="Test prompt",
        messages=[{"role": "assistant", "content": "Response"}],
        rewards={"quality": 0.9},
        step=42,
        mode="train",
        commit=True,
    )

    time.sleep(0.1)

    # Verify rollout has the custom step
    assert client_instance.log_rollouts.called
    call_args = client_instance.log_rollouts.call_args
    rollouts = call_args[0][1]
    assert rollouts[0]["step"] == 42

    run.end()


def test_mixed_auto_and_manual_steps(mock_client):
    """Test mixing automatic step increment with manual step overrides."""
    _, client_instance = mock_client

    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    # Auto step 0
    run.log({"m1": 1.0}, commit=True)
    # Auto step 1
    run.log({"m2": 2.0}, commit=True)
    # Override to step 100
    run.log({"m3": 3.0}, step=100, commit=True)
    # Continue from 100, so next auto step should be 101
    run.log({"m4": 4.0}, commit=True)

    time.sleep(0.2)

    calls = client_instance.log_scalars.call_args_list
    assert len(calls) >= 4
    assert calls[0][0][1][0]["step"] == 0
    assert calls[1][0][1][0]["step"] == 1
    assert calls[2][0][1][0]["step"] == 100
    assert calls[3][0][1][0]["step"] == 101

    run.end()


# ========== Validation Tests ==========


def test_log_with_invalid_metrics_not_dict(mock_client):
    """Test log() raises ValidationError when metrics is not a dict."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log([("loss", 0.5)])  # type: ignore

    assert "must be a dict" in str(exc_info.value)
    run.end()


def test_log_with_invalid_metric_value_string(mock_client):
    """Test log() raises ValidationError for string metric value."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log({"status": "good"})  # type: ignore

    assert "status" in str(exc_info.value)
    assert "expected int or float" in str(exc_info.value)
    run.end()


def test_log_with_invalid_metric_value_nan(mock_client):
    """Test log() raises ValidationError for NaN metric value."""
    import math

    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log({"loss": math.nan})

    assert "loss" in str(exc_info.value)
    assert "nan" in str(exc_info.value).lower()
    run.end()


def test_log_with_invalid_metric_value_inf(mock_client):
    """Test log() raises ValidationError for Inf metric value."""
    import math

    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log({"loss": math.inf})

    assert "loss" in str(exc_info.value)
    assert "inf" in str(exc_info.value).lower()
    run.end()


def test_log_with_invalid_metric_value_bool(mock_client):
    """Test log() raises ValidationError for boolean metric value."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log({"converged": True})

    assert "converged" in str(exc_info.value)
    assert "bool" in str(exc_info.value).lower()
    run.end()


def test_log_with_invalid_step_negative(mock_client):
    """Test log() raises ValidationError for negative step."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log({"loss": 0.5}, step=-1)

    assert "non-negative" in str(exc_info.value)
    run.end()


def test_log_with_invalid_mode_empty(mock_client):
    """Test log() raises ValidationError for empty string mode."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log({"loss": 0.5}, mode="")

    assert "non-empty" in str(exc_info.value)
    run.end()


def test_log_with_valid_int_metrics(mock_client):
    """Test log() accepts int metric values."""
    _, client_instance = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    run.log({"epoch": 10, "batch": 5}, commit=True)
    time.sleep(0.1)

    assert client_instance.log_scalars.called
    run.end()


def test_log_with_valid_float_metrics(mock_client):
    """Test log() accepts float metric values."""
    _, client_instance = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    run.log({"loss": 0.5, "accuracy": 0.95}, commit=True)
    time.sleep(0.1)

    assert client_instance.log_scalars.called
    run.end()


def test_log_rollout_with_dict_prompt(mock_client):
    """Test log_rollout() accepts dict prompt with 'content' key."""
    _, client_instance = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    run.log_rollout(
        prompt={"role": "user", "content": "What is 2+2?"},
        messages=[{"role": "assistant", "content": "4"}],
        rewards={"correctness": 1.0},
        commit=True,
    )
    time.sleep(0.1)

    assert client_instance.log_rollouts.called
    call_args = client_instance.log_rollouts.call_args
    rollouts = call_args[0][1]
    assert rollouts[0]["promptText"] == "What is 2+2?"
    run.end()


def test_log_rollout_with_string_prompt(mock_client):
    """Test log_rollout() still accepts string prompt (backward compatibility)."""
    _, client_instance = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    run.log_rollout(
        prompt="What is 2+2?",
        messages=[{"role": "assistant", "content": "4"}],
        rewards={"correctness": 1.0},
        commit=True,
    )
    time.sleep(0.1)

    assert client_instance.log_rollouts.called
    call_args = client_instance.log_rollouts.call_args
    rollouts = call_args[0][1]
    assert rollouts[0]["promptText"] == "What is 2+2?"
    run.end()


def test_log_rollout_with_dict_prompt_missing_content(mock_client):
    """Test log_rollout() raises ValidationError when dict missing 'content' key."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log_rollout(
            prompt={"role": "user", "text": "Wrong key"},
            messages=[{"role": "assistant", "content": "4"}],
            rewards={"correctness": 1.0},
        )

    assert "'content'" in str(exc_info.value)
    run.end()


def test_log_rollout_with_invalid_prompt_type(mock_client):
    """Test log_rollout() raises ValidationError for invalid prompt type."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log_rollout(
            prompt=123,  # type: ignore
            messages=[{"role": "assistant", "content": "4"}],
            rewards={"correctness": 1.0},
        )

    assert "must be str or dict" in str(exc_info.value)
    run.end()


def test_log_rollout_with_invalid_messages_not_list(mock_client):
    """Test log_rollout() raises ValidationError when messages is not a list."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log_rollout(
            prompt="Test",
            messages={"role": "assistant", "content": "4"},  # type: ignore
            rewards={"correctness": 1.0},
        )

    assert "must be a list" in str(exc_info.value)
    run.end()


def test_log_rollout_with_invalid_messages_missing_role(mock_client):
    """Test log_rollout() raises ValidationError when message missing 'role'."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log_rollout(
            prompt="Test",
            messages=[{"content": "4"}],
            rewards={"correctness": 1.0},
        )

    assert "missing required key 'role'" in str(exc_info.value)
    run.end()


def test_log_rollout_with_invalid_messages_missing_content(mock_client):
    """Test log_rollout() raises ValidationError when message missing 'content'."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log_rollout(
            prompt="Test",
            messages=[{"role": "assistant"}],
            rewards={"correctness": 1.0},
        )

    assert "missing required key 'content'" in str(exc_info.value)
    run.end()


def test_log_rollout_with_invalid_rewards_not_dict(mock_client):
    """Test log_rollout() raises ValidationError when rewards is not a dict."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log_rollout(
            prompt="Test",
            messages=[{"role": "assistant", "content": "4"}],
            rewards=[("correctness", 1.0)],  # type: ignore
        )

    assert "must be a dict" in str(exc_info.value)
    run.end()


def test_log_rollout_with_invalid_rewards_nan(mock_client):
    """Test log_rollout() raises ValidationError for NaN reward."""
    import math

    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log_rollout(
            prompt="Test",
            messages=[{"role": "assistant", "content": "4"}],
            rewards={"score": math.nan},
        )

    assert "score" in str(exc_info.value)
    assert "nan" in str(exc_info.value).lower()
    run.end()


def test_log_rollout_with_invalid_rewards_inf(mock_client):
    """Test log_rollout() raises ValidationError for Inf reward."""
    import math

    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log_rollout(
            prompt="Test",
            messages=[{"role": "assistant", "content": "4"}],
            rewards={"score": math.inf},
        )

    assert "score" in str(exc_info.value)
    assert "inf" in str(exc_info.value).lower()
    run.end()


def test_log_rollout_with_invalid_step_negative(mock_client):
    """Test log_rollout() raises ValidationError for negative step."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log_rollout(
            prompt="Test",
            messages=[{"role": "assistant", "content": "4"}],
            rewards={"score": 1.0},
            step=-1,
        )

    assert "non-negative" in str(exc_info.value)
    run.end()


def test_log_rollout_with_invalid_mode_empty(mock_client):
    """Test log_rollout() raises ValidationError for empty string mode."""
    from expt_logger.exceptions import ValidationError

    _, _ = mock_client
    run = Run(name="test-run", api_key="test-key", base_url="https://test.example.com")

    with pytest.raises(ValidationError) as exc_info:
        run.log_rollout(
            prompt="Test",
            messages=[{"role": "assistant", "content": "4"}],
            rewards={"score": 1.0},
            mode="",
        )

    assert "non-empty" in str(exc_info.value)
    run.end()


# ========== Experiment ID from Environment Tests ==========


def test_run_with_experiment_id_from_temp_file(mock_client, monkeypatch, tmp_path):
    """Test Run uses experiment ID from temp file when is_main_process=False."""
    _, client_instance = mock_client

    # Write experiment ID to temp file
    temp_dir = tempfile.gettempdir()
    experiment_id_file = os.path.join(temp_dir, "expt-logger-experiment-id.txt")
    with open(experiment_id_file, "w") as f:
        f.write("env-exp-123")

    try:
        run = Run(
            api_key="test-key",
            base_url="https://test.example.com",
            is_main_process=False,
        )

        # Should use temp file experiment ID
        assert run._experiment_id == "env-exp-123"

        # Should NOT create a new experiment
        assert not client_instance.create_experiment.called

        run.end()
    finally:
        # Cleanup
        if os.path.isfile(experiment_id_file):
            os.remove(experiment_id_file)


def test_run_with_is_main_process_false_raises_error_when_no_file(mock_client, monkeypatch):
    """Test Run raises error when is_main_process=False but temp file not set."""
    _, client_instance = mock_client

    # Ensure temp file is not created
    import os
    import tempfile

    temp_dir = tempfile.gettempdir()
    experiment_id_file = os.path.join(temp_dir, "expt-logger-experiment-id.txt")
    if os.path.isfile(experiment_id_file):
        os.remove(experiment_id_file)

    # Should raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        Run(
            name="test-run",
            api_key="test-key",
            base_url="https://test.example.com",
            is_main_process=False,
        )

    assert "Experiment ID not found" in str(exc_info.value)


def test_run_main_process_creates_new_experiment_and_writes_temp_file(mock_client):
    """Test Run (main process) creates new experiment and writes to temp file."""
    import os
    import tempfile

    _, client_instance = mock_client

    # Ensure temp file doesn't exist initially
    temp_dir = tempfile.gettempdir()
    experiment_id_file = os.path.join(temp_dir, "expt-logger-experiment-id.txt")
    if os.path.isfile(experiment_id_file):
        os.remove(experiment_id_file)

    try:
        run = Run(
            name="test-run",
            api_key="test-key",
            base_url="https://test.example.com",
            is_main_process=True,
        )

        # Should create a new experiment
        assert client_instance.create_experiment.called
        assert run._experiment_id == "test-exp-id"

        # Temp file should be created with the new experiment ID
        assert os.path.isfile(experiment_id_file)
        with open(experiment_id_file) as f:
            assert f.read().strip() == "test-exp-id"

        run.end()
    finally:
        # Cleanup
        if os.path.isfile(experiment_id_file):
            os.remove(experiment_id_file)


def test_run_main_process_overwrites_existing_temp_file(mock_client):
    """Test Run (main process) creates new experiment and overwrites existing temp file."""
    import os
    import tempfile

    _, client_instance = mock_client

    # Create temp file with existing experiment ID
    temp_dir = tempfile.gettempdir()
    experiment_id_file = os.path.join(temp_dir, "expt-logger-experiment-id.txt")
    with open(experiment_id_file, "w") as f:
        f.write("env-exp-should-overwrite")

    try:
        run = Run(
            name="test-run",
            api_key="test-key",
            base_url="https://test.example.com",
            is_main_process=True,
        )

        # Should create a new experiment, NOT use existing file
        assert client_instance.create_experiment.called
        assert run._experiment_id == "test-exp-id"
        assert run._experiment_id != "env-exp-should-overwrite"

        # Temp file should be overwritten with the new experiment ID
        with open(experiment_id_file) as f:
            assert f.read().strip() == "test-exp-id"

        run.end()
    finally:
        # Cleanup
        if os.path.isfile(experiment_id_file):
            os.remove(experiment_id_file)


def test_run_logging_works_with_experiment_id_from_temp_file(mock_client):
    """Test that logging works when using experiment ID from temp file (is_main_process=False)."""
    import os
    import tempfile

    _, client_instance = mock_client

    # Write experiment ID to temp file
    temp_dir = tempfile.gettempdir()
    experiment_id_file = os.path.join(temp_dir, "expt-logger-experiment-id.txt")
    with open(experiment_id_file, "w") as f:
        f.write("env-exp-789")

    try:
        run = Run(
            api_key="test-key",
            base_url="https://test.example.com",
            is_main_process=False,
        )

        # Log metrics
        run.log({"loss": 0.5}, commit=True)
        time.sleep(0.1)

        # Verify metrics were logged to the existing experiment
        assert client_instance.log_scalars.called
        call_args = client_instance.log_scalars.call_args
        assert call_args[0][0] == "env-exp-789"

        run.end()
    finally:
        # Cleanup
        if os.path.isfile(experiment_id_file):
            os.remove(experiment_id_file)

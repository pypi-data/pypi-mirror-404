"""Tests for global API functions."""

from unittest.mock import Mock, patch

import pytest

import expt_logger


@pytest.fixture
def mock_run():
    """Mock the Run class."""
    with patch("expt_logger.Run") as MockRun:
        run_instance = Mock()
        run_instance.experiment_url = "https://example.com/experiments/test-id"
        run_instance.base_url = "https://example.com"
        run_instance.config = Mock()
        MockRun.return_value = run_instance
        yield MockRun, run_instance


@pytest.fixture(autouse=True)
def cleanup_global_state():
    """Clean up global state before and after each test."""
    # Clear state before test
    expt_logger._active_run = None
    yield
    # Clear state after test
    if expt_logger._active_run is not None:
        try:
            expt_logger._active_run.end()
        except Exception:
            pass
    expt_logger._active_run = None


def test_init_creates_run(mock_run):
    """Test init() creates a Run instance."""
    MockRun, run_instance = mock_run

    run = expt_logger.init(
        name="test-run",
        config={"lr": 0.001},
        api_key="test-key",
        base_url="https://test.example.com",
    )

    # Verify Run was created with correct args
    MockRun.assert_called_once()
    call_kwargs = MockRun.call_args.kwargs
    assert call_kwargs["name"] == "test-run"
    assert call_kwargs["config"] == {"lr": 0.001}
    assert call_kwargs["api_key"] == "test-key"
    assert call_kwargs["base_url"] == "https://test.example.com"

    # Verify returned run is the instance
    assert run is run_instance


def test_init_stores_active_run(mock_run):
    """Test init() stores run in global state."""
    _, run_instance = mock_run

    expt_logger.init(name="test-run")

    # Verify global state was updated
    assert expt_logger._active_run is run_instance


def test_init_warns_if_already_initialized(mock_run, caplog):
    """Test init() warns if run already exists."""
    _, run_instance = mock_run

    # First init
    run1 = expt_logger.init(name="run1")

    # Second init should warn and return existing run
    run2 = expt_logger.init(name="run2")

    assert run1 is run2
    assert "already initialized" in caplog.text.lower()


def test_log_delegates_to_run(mock_run):
    """Test log() delegates to the active run."""
    _, run_instance = mock_run

    expt_logger.init()
    expt_logger.log({"loss": 0.5, "accuracy": 0.9}, step=10, mode="train", commit=True)

    run_instance.log.assert_called_once_with(
        {"loss": 0.5, "accuracy": 0.9}, step=10, mode="train", commit=True
    )


def test_log_raises_if_no_active_run(mock_run):
    """Test log() raises RuntimeError if no active run."""
    with pytest.raises(RuntimeError) as exc_info:
        expt_logger.log({"loss": 0.5})

    assert "No active run" in str(exc_info.value)
    assert "init()" in str(exc_info.value)


def test_log_rollout_delegates_to_run(mock_run):
    """Test log_rollout() delegates to the active run."""
    _, run_instance = mock_run

    expt_logger.init()
    expt_logger.log_rollout(
        prompt="Test prompt",
        messages=[{"role": "assistant", "content": "Response"}],
        rewards={"quality": 0.9},
        step=5,
        mode="eval",
        commit=False,
    )

    run_instance.log_rollout.assert_called_once_with(
        prompt="Test prompt",
        messages=[{"role": "assistant", "content": "Response"}],
        rewards={"quality": 0.9},
        step=5,
        mode="eval",
        commit=False,
    )


def test_log_rollout_raises_if_no_active_run(mock_run):
    """Test log_rollout() raises RuntimeError if no active run."""
    with pytest.raises(RuntimeError) as exc_info:
        expt_logger.log_rollout(prompt="Test", messages=[], rewards={"quality": 0.9})

    assert "No active run" in str(exc_info.value)


def test_commit_delegates_to_run(mock_run):
    """Test commit() delegates to the active run."""
    _, run_instance = mock_run

    expt_logger.init()
    expt_logger.commit()

    run_instance.commit.assert_called_once()


def test_commit_raises_if_no_active_run(mock_run):
    """Test commit() raises RuntimeError if no active run."""
    with pytest.raises(RuntimeError) as exc_info:
        expt_logger.commit()

    assert "No active run" in str(exc_info.value)


def test_end_calls_run_end(mock_run):
    """Test end() calls run.end()."""
    _, run_instance = mock_run

    expt_logger.init()
    expt_logger.end()

    run_instance.end.assert_called_once()


def test_end_clears_global_state(mock_run):
    """Test end() clears the global _active_run."""
    _, run_instance = mock_run

    expt_logger.init()
    expt_logger.end()

    assert expt_logger._active_run is None


def test_end_is_idempotent(mock_run):
    """Test calling end() multiple times is safe."""
    _, run_instance = mock_run

    expt_logger.init()

    # Call end multiple times
    expt_logger.end()
    expt_logger.end()
    expt_logger.end()

    # Should only call run.end() once
    run_instance.end.assert_called_once()


def test_end_does_nothing_if_no_active_run(mock_run):
    """Test end() is safe to call with no active run."""
    # Should not raise
    expt_logger.end()


def test_experiment_url_returns_run_url(mock_run):
    """Test experiment_url() returns the run's URL."""
    _, run_instance = mock_run

    expt_logger.init()
    url = expt_logger.experiment_url()

    assert url == "https://example.com/experiments/test-id"


def test_experiment_url_raises_if_no_active_run(mock_run):
    """Test experiment_url() raises RuntimeError if no active run."""
    with pytest.raises(RuntimeError) as exc_info:
        expt_logger.experiment_url()

    assert "No active run" in str(exc_info.value)


def test_base_url_returns_run_base_url(mock_run):
    """Test base_url() returns the run's base URL."""
    _, run_instance = mock_run

    expt_logger.init()
    url = expt_logger.base_url()

    assert url == "https://example.com"


def test_base_url_raises_if_no_active_run(mock_run):
    """Test base_url() raises RuntimeError if no active run."""
    with pytest.raises(RuntimeError) as exc_info:
        expt_logger.base_url()

    assert "No active run" in str(exc_info.value)


def test_config_returns_run_config(mock_run):
    """Test config() returns the run's config object."""
    _, run_instance = mock_run

    expt_logger.init()
    cfg = expt_logger.config()

    assert cfg is run_instance.config


def test_config_raises_if_no_active_run(mock_run):
    """Test config() raises RuntimeError if no active run."""
    with pytest.raises(RuntimeError) as exc_info:
        expt_logger.config()

    assert "No active run" in str(exc_info.value)


def test_workflow_init_log_end(mock_run):
    """Test complete workflow: init -> log -> end."""
    _, run_instance = mock_run

    # Initialize
    run = expt_logger.init(name="test-run", config={"lr": 0.001})
    assert run is not None

    # Log some metrics
    expt_logger.log({"loss": 0.5}, commit=False)
    expt_logger.log({"accuracy": 0.9}, commit=False)
    expt_logger.commit()

    # Verify log was called
    assert run_instance.log.call_count == 2
    assert run_instance.commit.call_count == 1

    # End the run
    expt_logger.end()
    assert expt_logger._active_run is None


def test_workflow_with_rollouts(mock_run):
    """Test workflow with rollouts."""
    _, run_instance = mock_run

    expt_logger.init()

    # Log rollout
    expt_logger.log_rollout(
        prompt="What is 2+2?",
        messages=[{"role": "assistant", "content": "4"}],
        rewards={"correctness": 1.0},
    )

    run_instance.log_rollout.assert_called_once()

    expt_logger.end()


def test_default_parameters(mock_run):
    """Test functions work with default parameters."""
    MockRun, run_instance = mock_run

    # Init with no args
    expt_logger.init()
    MockRun.assert_called_once()
    call_kwargs = MockRun.call_args.kwargs
    assert call_kwargs["name"] is None
    assert call_kwargs["config"] is None
    assert call_kwargs["api_key"] is None
    assert call_kwargs["base_url"] is None

    # Log with minimal args
    expt_logger.log({"loss": 0.5})
    run_instance.log.assert_called_once_with({"loss": 0.5}, step=None, mode=None, commit=True)

    # Log rollout with minimal args
    expt_logger.log_rollout(prompt="test", messages=[], rewards={"r": 1.0})
    run_instance.log_rollout.assert_called_once_with(
        prompt="test",
        messages=[],
        rewards={"r": 1.0},
        step=None,
        mode=None,
        commit=True,
    )

    expt_logger.end()


def test_all_exports():
    """Test that __all__ contains expected exports."""
    expected = [
        "init",
        "log",
        "log_rollout",
        "commit",
        "end",
        "experiment_url",
        "base_url",
        "config",
        "ValidationError",
    ]

    assert set(expt_logger.__all__) == set(expected)


def test_sequential_runs(mock_run):
    """Test creating sequential runs after ending previous one."""
    MockRun, run_instance = mock_run

    # First run
    expt_logger.init(name="run1")
    expt_logger.log({"loss": 0.5})
    expt_logger.end()

    # Should be able to create second run
    expt_logger.init(name="run2")
    expt_logger.log({"loss": 0.3})
    expt_logger.end()

    # Verify two runs were created
    assert MockRun.call_count == 2


def test_config_modification(mock_run):
    """Test modifying config through global API."""
    _, run_instance = mock_run

    expt_logger.init(config={"lr": 0.001})

    # Get config
    cfg = expt_logger.config()

    # Verify we got the config object
    assert cfg is run_instance.config

    expt_logger.end()


def test_readme_example():
    """Test the example from the README works."""
    with patch("expt_logger.Run") as MockRun:
        run_instance = Mock()
        run_instance.experiment_url = "https://app.cgft.io/experiments/test-id"
        run_instance.base_url = "https://app.cgft.io"
        MockRun.return_value = run_instance

        # Example from README
        expt_logger.init(name="grpo-math", config={"lr": 3e-6, "batch_size": 8})

        # Get experiment URLs
        url = expt_logger.experiment_url()
        base = expt_logger.base_url()

        assert url == "https://app.cgft.io/experiments/test-id"
        assert base == "https://app.cgft.io"

        # Log scalar metrics
        expt_logger.log({"train/loss": 0.45, "train/kl": 0.02, "train/reward": 0.85}, commit=False)

        # Log RL rollouts
        expt_logger.log_rollout(
            prompt="What is 2+2?",
            messages=[{"role": "assistant", "content": "The answer is 4."}],
            rewards={"correctness": 1.0, "format": 0.9},
            mode="train",
            commit=True,
        )

        expt_logger.end()

        # Verify calls
        run_instance.log.assert_called()
        run_instance.log_rollout.assert_called()
        run_instance.end.assert_called()

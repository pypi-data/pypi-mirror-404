"""End-to-end integration tests for expt-logger.

Tests the complete stack: Global API → Run → Buffer → APIClient → Server

Requirements:
- Running server at EXPT_LOGGER_BASE_URL or http://localhost:3000
- Tests marked with @pytest.mark.integration
- Skips gracefully if server unavailable

Run: uv run pytest tests/test_integration_e2e.py -v
"""

import multiprocessing
import os
import time

import pytest
import requests

import expt_logger
from expt_logger.client import APIClient

# Note: Common fixtures (server_available, shared_api_key, base_url) are imported from conftest.py


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def cleanup_global_state():
    """Clean up global state before and after each test."""
    expt_logger._active_run = None
    yield
    if expt_logger._active_run is not None:
        try:
            expt_logger._active_run.end(timeout=5)
        except Exception:
            pass
    expt_logger._active_run = None


@pytest.fixture
def cleanup_experiments(shared_api_key: str, base_url: str):
    """Track and cleanup experiments created during test."""
    experiment_ids = []
    yield experiment_ids

    # Cleanup after test
    if experiment_ids:
        client = APIClient(base_url=base_url, api_key=shared_api_key)
        try:
            deleted = client.delete_experiments(experiment_ids)
            print(f"\nCleaned up {deleted} test experiments")
        except Exception as e:
            print(f"\nWarning: Failed to cleanup experiments: {e}")
        finally:
            client.close()


@pytest.fixture
def env_with_api_key(shared_api_key: str, monkeypatch):
    """Set API key in environment."""
    monkeypatch.setenv("EXPT_LOGGER_API_KEY", shared_api_key)


@pytest.fixture
def env_with_base_url(base_url: str, monkeypatch):
    """Set base URL in environment."""
    monkeypatch.setenv("EXPT_LOGGER_BASE_URL", base_url)


@pytest.fixture
def fetch_experiment_data(shared_api_key: str, base_url: str):
    """Factory fixture for fetching experiment details from server."""

    def _fetch(experiment_id: str):
        response = requests.get(
            f"{base_url}/api/experiments/{experiment_id}/details",
            headers={"Authorization": f"Bearer {shared_api_key}"},
        )
        assert response.status_code == 200
        return response.json()

    return _fetch


@pytest.fixture
def fetch_scalars(shared_api_key: str, base_url: str):
    """Factory fixture for fetching scalar data."""

    def _fetch(experiment_id: str, mode: str = "train"):
        response = requests.get(
            f"{base_url}/api/experiments/{experiment_id}/scalars",
            params={"mode": mode},
            headers={"Authorization": f"Bearer {shared_api_key}"},
        )
        assert response.status_code == 200
        return response.json()

    return _fetch


@pytest.fixture
def fetch_rollouts(shared_api_key: str, base_url: str):
    """Factory fixture for fetching rollout data."""

    def _fetch(experiment_id: str, mode: str = "train"):
        response = requests.get(
            f"{base_url}/api/experiments/{experiment_id}/rollouts/summary",
            params={"mode": mode, "page": 1, "limit": 100},
            headers={"Authorization": f"Bearer {shared_api_key}"},
        )
        assert response.status_code == 200
        return response.json()

    return _fetch


# ============================================================================
# Test Class 1: Basic Workflow Tests
# ============================================================================


@pytest.mark.integration
class TestBasicWorkflow:
    """Basic initialization, logging, and cleanup."""

    def test_init_log_end_basic_workflow(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test basic init → log → end flow."""
        # Initialize
        run = expt_logger.init(
            name="test-basic-workflow",
            api_key=shared_api_key,
            base_url=base_url,
        )
        exp_id = run._experiment_id
        cleanup_experiments.append(exp_id)

        # Log and commit
        expt_logger.log({"loss": 0.5}, commit=True)
        time.sleep(0.5)  # Allow worker to process

        # End
        expt_logger.end()

        # Verify on server
        scalars = fetch_scalars(exp_id, "train")
        assert "loss" in scalars
        assert len(scalars["loss"]) == 1
        assert scalars["loss"][0]["step"] == 0
        assert abs(scalars["loss"][0]["value"] - 0.5) < 1e-6

    def test_sequential_runs(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test multiple sequential runs with no state leakage."""
        # First run
        run1 = expt_logger.init(name="test-run-1", api_key=shared_api_key, base_url=base_url)
        exp_id1 = run1._experiment_id
        cleanup_experiments.append(exp_id1)
        expt_logger.log({"metric1": 1.0}, commit=True)
        time.sleep(0.3)
        expt_logger.end()

        # Second run
        run2 = expt_logger.init(name="test-run-2", api_key=shared_api_key, base_url=base_url)
        exp_id2 = run2._experiment_id
        cleanup_experiments.append(exp_id2)
        expt_logger.log({"metric2": 2.0}, commit=True)
        time.sleep(0.3)
        expt_logger.end()

        # Verify independence
        assert exp_id1 != exp_id2

        scalars1 = fetch_scalars(exp_id1, "train")
        assert "metric1" in scalars1
        assert "metric2" not in scalars1

        scalars2 = fetch_scalars(exp_id2, "train")
        assert "metric2" in scalars2
        assert "metric1" not in scalars2

    def test_properties_accessible(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
    ) -> None:
        """Test accessing experiment_url, base_url, config properties."""
        run = expt_logger.init(
            name="test-properties",
            config={"test": True},
            api_key=shared_api_key,
            base_url=base_url,
        )
        cleanup_experiments.append(run._experiment_id)

        # Access properties
        assert expt_logger.experiment_url is not None
        assert run._experiment_id in expt_logger.experiment_url()
        assert expt_logger.base_url() == base_url
        assert expt_logger.config() is not None
        assert expt_logger.config().test is True

        expt_logger.end()


# ============================================================================
# Test Class 2: Buffering and Commit Pattern Tests
# ============================================================================


@pytest.mark.integration
class TestBufferingAndCommit:
    """Buffering behavior and commit patterns."""

    def test_buffering_without_commit(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test that commit=False buffers data until explicit commit."""
        run = expt_logger.init(name="test-buffering", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        # Log without committing
        expt_logger.log({"loss": 0.5}, commit=False)
        expt_logger.log({"accuracy": 0.9}, commit=False)
        time.sleep(0.3)

        # Data should not be on server yet (step hasn't been committed)
        # Note: This is hard to verify since data might be in flight
        # Instead verify both appear at same step after commit

        # Now commit
        expt_logger.commit()
        time.sleep(0.5)

        # Verify both at step 0
        scalars = fetch_scalars(run._experiment_id, "train")
        assert "loss" in scalars
        assert "accuracy" in scalars
        assert scalars["loss"][0]["step"] == 0
        assert scalars["accuracy"][0]["step"] == 0

        expt_logger.end()

    def test_buffering_last_write_wins(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test that duplicate keys at same step use last write wins."""
        run = expt_logger.init(name="test-last-write", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        # Log same key twice before commit
        expt_logger.log({"loss": 0.5}, commit=False)
        expt_logger.log({"loss": 0.3}, commit=False)  # Should overwrite
        expt_logger.commit()
        time.sleep(0.5)

        # Verify only last value persists
        scalars = fetch_scalars(run._experiment_id, "train")
        assert "loss" in scalars
        assert len(scalars["loss"]) == 1
        assert abs(scalars["loss"][0]["value"] - 0.3) < 1e-6

        expt_logger.end()

    def test_commit_true_immediate_flush(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test that commit=True immediately flushes and increments step."""
        run = expt_logger.init(name="test-immediate", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        # Log with immediate commit
        expt_logger.log({"metric1": 1.0}, commit=True)
        time.sleep(0.3)
        expt_logger.log({"metric2": 2.0}, commit=True)
        time.sleep(0.5)

        # Verify at different steps
        scalars = fetch_scalars(run._experiment_id, "train")
        assert "metric1" in scalars
        assert "metric2" in scalars
        assert scalars["metric1"][0]["step"] == 0
        assert scalars["metric2"][0]["step"] == 1

        expt_logger.end()

    def test_mixed_commit_patterns(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test mixing commit=True and commit=False."""
        run = expt_logger.init(name="test-mixed", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        # Buffer two at step 0
        expt_logger.log({"a": 1.0}, commit=False)
        expt_logger.log({"b": 2.0}, commit=False)

        # Commit with third metric
        expt_logger.log({"c": 3.0}, commit=True)
        time.sleep(0.3)

        # Fourth metric at step 1
        expt_logger.log({"d": 4.0}, commit=True)
        time.sleep(0.5)

        # Verify step assignment
        scalars = fetch_scalars(run._experiment_id, "train")
        assert scalars["a"][0]["step"] == 0
        assert scalars["b"][0]["step"] == 0
        assert scalars["c"][0]["step"] == 0
        assert scalars["d"][0]["step"] == 1

        expt_logger.end()

    def test_batch_scalars_and_rollouts_same_step(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
        fetch_rollouts,
    ) -> None:
        """Test logging both scalars and rollouts at same step."""
        run = expt_logger.init(name="test-batch-both", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        # Log both types without commit
        expt_logger.log({"loss": 0.5}, commit=False)
        expt_logger.log_rollout(
            prompt="test prompt",
            messages=[{"role": "assistant", "content": "response"}],
            rewards={"quality": 0.8},
            commit=True,  # Commits both
        )
        time.sleep(0.5)

        # Verify both at step 0
        scalars = fetch_scalars(run._experiment_id, "train")
        assert "loss" in scalars
        assert scalars["loss"][0]["step"] == 0

        rollouts = fetch_rollouts(run._experiment_id, "train")
        assert len(rollouts["groups"]) > 0

        expt_logger.end()


# ============================================================================
# Test Class 3: Mode System Tests
# ============================================================================


@pytest.mark.integration
class TestModeSystem:
    """Train/eval modes and slash prefix handling."""

    def test_mode_defaults_to_train(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test that metrics default to train mode."""
        run = expt_logger.init(name="test-default-mode", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        expt_logger.log({"loss": 0.5}, commit=True)
        time.sleep(0.5)

        # Should appear in train mode
        scalars = fetch_scalars(run._experiment_id, "train")
        assert "loss" in scalars

        expt_logger.end()

    def test_explicit_mode_parameter(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test explicit mode parameter."""
        run = expt_logger.init(name="test-explicit-mode", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        expt_logger.log({"loss": 0.5, "accuracy": 0.9}, mode="eval", commit=True)
        time.sleep(0.5)

        # Should appear in eval mode
        scalars = fetch_scalars(run._experiment_id, "eval")
        assert "loss" in scalars
        assert "accuracy" in scalars

        expt_logger.end()

    def test_slash_prefix_detection(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test slash prefix mode detection."""
        run = expt_logger.init(name="test-slash-prefix", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        expt_logger.log({"train/loss": 0.5, "eval/loss": 0.6}, commit=True)
        time.sleep(0.5)

        # Verify mode separation
        train_scalars = fetch_scalars(run._experiment_id, "train")
        eval_scalars = fetch_scalars(run._experiment_id, "eval")

        assert "loss" in train_scalars
        assert abs(train_scalars["loss"][0]["value"] - 0.5) < 1e-6

        assert "loss" in eval_scalars
        assert abs(eval_scalars["loss"][0]["value"] - 0.6) < 1e-6

        expt_logger.end()


# ============================================================================
# Test Class 4: Configuration Tests
# ============================================================================


@pytest.mark.integration
class TestConfiguration:
    """Config initialization and dynamic updates."""

    def test_init_with_config(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_experiment_data,
    ) -> None:
        """Test initial config persists to server."""
        run = expt_logger.init(
            name="test-init-config",
            config={"lr": 0.001, "batch_size": 32},
            api_key=shared_api_key,
            base_url=base_url,
        )
        cleanup_experiments.append(run._experiment_id)

        time.sleep(0.3)
        data = fetch_experiment_data(run._experiment_id)

        assert data["config"]["lr"] == 0.001
        assert data["config"]["batch_size"] == 32

        expt_logger.end()

    def test_config_attribute_update(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_experiment_data,
    ) -> None:
        """Test attribute-style config updates."""
        run = expt_logger.init(
            name="test-config-attr",
            config={"lr": 0.001},
            api_key=shared_api_key,
            base_url=base_url,
        )
        cleanup_experiments.append(run._experiment_id)

        # Update config
        run.config.lr = 0.0005
        time.sleep(0.5)

        data = fetch_experiment_data(run._experiment_id)
        assert data["config"]["lr"] == 0.0005

        expt_logger.end()

    def test_config_bulk_update(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_experiment_data,
    ) -> None:
        """Test bulk config updates."""
        run = expt_logger.init(
            name="test-config-bulk",
            config={"lr": 0.001},
            api_key=shared_api_key,
            base_url=base_url,
        )
        cleanup_experiments.append(run._experiment_id)

        # Bulk update
        run.config.update({"lr": 0.002, "model": "gpt2"})
        time.sleep(0.5)

        data = fetch_experiment_data(run._experiment_id)
        assert data["config"]["lr"] == 0.002
        assert data["config"]["model"] == "gpt2"

        expt_logger.end()


# ============================================================================
# Test Class 5: Rollout Tests
# ============================================================================


@pytest.mark.integration
class TestRollouts:
    """RL rollout logging functionality."""

    def test_log_rollout_basic(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_rollouts,
    ) -> None:
        """Test basic rollout logging."""
        run = expt_logger.init(name="test-rollout-basic", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        expt_logger.log_rollout(
            prompt="What is 2+2?",
            messages=[{"role": "assistant", "content": "The answer is 4."}],
            rewards={"correctness": 1.0},
            commit=True,
        )
        time.sleep(0.5)

        rollouts = fetch_rollouts(run._experiment_id, "train")
        assert len(rollouts["groups"]) > 0

        expt_logger.end()

    def test_log_rollout_multiple_rewards(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_rollouts,
    ) -> None:
        """Test rollout with multiple rewards."""
        run = expt_logger.init(
            name="test-rollout-multi-reward", api_key=shared_api_key, base_url=base_url
        )
        cleanup_experiments.append(run._experiment_id)

        expt_logger.log_rollout(
            prompt="Test prompt",
            messages=[{"role": "assistant", "content": "Test response"}],
            rewards={"quality": 0.8, "correctness": 1.0, "clarity": 0.9},
            commit=True,
        )
        time.sleep(0.5)

        rollouts = fetch_rollouts(run._experiment_id, "train")
        assert len(rollouts["groups"]) > 0

        expt_logger.end()


# ============================================================================
# Test Class 6: Environment Configuration Tests
# ============================================================================


@pytest.mark.integration
class TestEnvironmentConfiguration:
    """Environment variable handling."""

    def test_api_key_from_env(
        self,
        env_with_api_key,
        base_url: str,
        cleanup_experiments: list[str],
    ) -> None:
        """Test API key from environment variable."""
        run = expt_logger.init(name="test-env-api-key", base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        expt_logger.log({"test": 1.0}, commit=True)
        time.sleep(0.3)
        expt_logger.end()

    def test_base_url_from_env(
        self,
        shared_api_key: str,
        env_with_base_url,
        cleanup_experiments: list[str],
    ) -> None:
        """Test base URL from environment variable."""
        run = expt_logger.init(name="test-env-base-url", api_key=shared_api_key)
        cleanup_experiments.append(run._experiment_id)

        expt_logger.log({"test": 1.0}, commit=True)
        time.sleep(0.3)
        expt_logger.end()


# ============================================================================
# Test Class 7: Experiment ID Override Tests
# ============================================================================


@pytest.mark.integration
class TestExperimentIdOverride:
    """Test attaching to existing experiments via experiment_id parameter or env var."""

    def test_attach_to_existing_experiment_via_parameter(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test attaching to an existing experiment using experiment_id parameter."""
        # First, create an experiment
        run1 = expt_logger.init(name="test-attach-param", api_key=shared_api_key, base_url=base_url)
        exp_id = run1._experiment_id
        cleanup_experiments.append(exp_id)
        expt_logger.log({"metric1": 1.0}, commit=True)
        time.sleep(0.3)
        expt_logger.end()

        # Now attach to the same experiment using experiment_id parameter
        run2 = expt_logger.init(
            experiment_id=exp_id,
            api_key=shared_api_key,
            base_url=base_url,
        )
        assert run2._experiment_id == exp_id
        expt_logger.log({"metric2": 2.0}, commit=True)
        time.sleep(0.3)
        expt_logger.end()

        # Verify both metrics are in the same experiment
        scalars = fetch_scalars(exp_id, "train")
        assert "metric1" in scalars
        assert "metric2" in scalars

    def test_attach_to_existing_experiment_via_env_var(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
        monkeypatch,
    ) -> None:
        """Test attaching to an existing experiment using EXPT_LOGGER_EXPERIMENT_ID env var."""
        # First, create an experiment
        run1 = expt_logger.init(name="test-attach-env", api_key=shared_api_key, base_url=base_url)
        exp_id = run1._experiment_id
        cleanup_experiments.append(exp_id)
        expt_logger.log({"metric1": 1.0}, commit=True)
        time.sleep(0.3)
        expt_logger.end()

        # Set env var and attach to the same experiment
        monkeypatch.setenv("EXPT_LOGGER_EXPERIMENT_ID", exp_id)
        run2 = expt_logger.init(api_key=shared_api_key, base_url=base_url)
        assert run2._experiment_id == exp_id
        expt_logger.log({"metric2": 2.0}, commit=True)
        time.sleep(0.3)
        expt_logger.end()

        # Verify both metrics are in the same experiment
        scalars = fetch_scalars(exp_id, "train")
        assert "metric1" in scalars
        assert "metric2" in scalars

    def test_parameter_overrides_env_var(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
        monkeypatch,
    ) -> None:
        """Test that experiment_id parameter takes precedence over env var."""
        # Create two experiments
        run1 = expt_logger.init(name="test-override-1", api_key=shared_api_key, base_url=base_url)
        exp_id1 = run1._experiment_id
        cleanup_experiments.append(exp_id1)
        expt_logger.end()

        run2 = expt_logger.init(name="test-override-2", api_key=shared_api_key, base_url=base_url)
        exp_id2 = run2._experiment_id
        cleanup_experiments.append(exp_id2)
        expt_logger.end()

        # Set env var to exp_id1, but pass exp_id2 as parameter
        monkeypatch.setenv("EXPT_LOGGER_EXPERIMENT_ID", exp_id1)
        run3 = expt_logger.init(
            experiment_id=exp_id2,
            api_key=shared_api_key,
            base_url=base_url,
        )
        # Parameter should win
        assert run3._experiment_id == exp_id2
        expt_logger.log({"metric": 1.0}, commit=True)
        time.sleep(0.3)
        expt_logger.end()

        # Verify metric went to exp_id2, not exp_id1
        scalars1 = fetch_scalars(exp_id1, "train")
        scalars2 = fetch_scalars(exp_id2, "train")
        assert "metric" not in scalars1
        assert "metric" in scalars2

    def test_attach_to_nonexistent_experiment_fails(
        self,
        shared_api_key: str,
        base_url: str,
    ) -> None:
        """Test that attaching to a non-existent experiment raises an error."""
        fake_exp_id = "00000000-0000-0000-0000-000000000000"
        with pytest.raises(Exception) as exc_info:
            expt_logger.init(
                experiment_id=fake_exp_id,
                api_key=shared_api_key,
                base_url=base_url,
            )
        assert "not found" in str(exc_info.value).lower()


# ============================================================================
# Test Class 8: Error Handling Tests
# ============================================================================


@pytest.mark.integration
class TestErrorHandling:
    """Error scenarios and recovery."""

    def test_no_active_run_errors(self) -> None:
        """Test that calling log() before init() raises RuntimeError."""
        # Ensure no active run
        assert expt_logger._active_run is None

        with pytest.raises(RuntimeError) as exc_info:
            expt_logger.log({"test": 1.0})

        assert "No active run" in str(exc_info.value)
        assert "init()" in str(exc_info.value)


# ============================================================================
# Test Class 8: Graceful Shutdown Tests
# ============================================================================


@pytest.mark.integration
class TestGracefulShutdown:
    """Cleanup and shutdown behavior."""

    def test_end_flushes_buffered_data(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test that end() flushes buffered data."""
        run = expt_logger.init(name="test-end-flush", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        # Log without commit
        expt_logger.log({"loss": 0.5}, commit=False)

        # End immediately
        expt_logger.end()
        time.sleep(0.5)

        # Verify data still persisted
        scalars = fetch_scalars(run._experiment_id, "train")
        assert "loss" in scalars

    def test_end_is_idempotent(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
    ) -> None:
        """Test that end() can be called multiple times safely."""
        run = expt_logger.init(
            name="test-end-idempotent", api_key=shared_api_key, base_url=base_url
        )
        cleanup_experiments.append(run._experiment_id)

        # Call end multiple times
        expt_logger.end()
        expt_logger.end()  # Should not raise


# ============================================================================
# Test Class 9: Complete Workflow Tests
# ============================================================================


@pytest.mark.integration
class TestCompleteWorkflows:
    """Realistic end-to-end scenarios."""

    def test_realistic_training_loop(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
        fetch_rollouts,
    ) -> None:
        """Simulate realistic RL training workflow."""
        # Initialize
        run = expt_logger.init(
            name="test-training-loop",
            config={"lr": 0.001, "episodes": 5},
            api_key=shared_api_key,
            base_url=base_url,
        )
        cleanup_experiments.append(run._experiment_id)

        # Training loop
        for episode in range(5):
            # Log episode metrics without commit
            expt_logger.log({"train/loss": 1.0 - episode * 0.1}, commit=False)
            expt_logger.log({"train/reward": episode * 0.2}, commit=False)

            # Log rollout
            expt_logger.log_rollout(
                prompt=f"Episode {episode}",
                messages=[{"role": "assistant", "content": f"Response {episode}"}],
                rewards={"quality": episode * 0.15},
                commit=True,  # Commit episode data
            )

            # Update config mid-training
            if episode == 2:
                run.config.lr = 0.0005

        # End training
        expt_logger.end()
        time.sleep(0.5)

        # Verify all data
        scalars = fetch_scalars(run._experiment_id, "train")

        # Should have 5 data points for each metric
        assert len(scalars["loss"]) == 5
        assert len(scalars["reward"]) == 5

        # Verify steps are 0-4
        assert [s["step"] for s in scalars["loss"]] == [0, 1, 2, 3, 4]

        # Verify rollouts
        rollouts = fetch_rollouts(run._experiment_id, "train")
        assert len(rollouts["groups"]) > 0


# ============================================================================
# Test Class 10: Stress Testing (marked slow)
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestStressTesting:
    """System behavior under heavy load."""

    def test_rapid_logging_stress(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test rapid logging of many metrics."""
        run = expt_logger.init(name="test-stress-rapid", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        # Log 1000 unique metrics rapidly
        for i in range(1000):
            expt_logger.log({f"metric_{i}": float(i)}, commit=False)

        # Single commit
        expt_logger.commit()
        time.sleep(2.0)  # Allow processing

        # Verify all persisted
        scalars = fetch_scalars(run._experiment_id, "train")
        assert len(scalars) == 1000

        expt_logger.end()

    def test_large_batch_scalars(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test large batch of scalars in single call."""
        run = expt_logger.init(name="test-stress-batch", api_key=shared_api_key, base_url=base_url)
        cleanup_experiments.append(run._experiment_id)

        # Log 100 metrics in one call
        metrics = {f"metric_{i}": float(i) for i in range(100)}
        expt_logger.log(metrics, commit=True)
        time.sleep(1.0)

        # Verify all on server
        scalars = fetch_scalars(run._experiment_id, "train")
        assert len(scalars) == 100

        expt_logger.end()

    def test_large_rollout_messages(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_rollouts,
    ) -> None:
        """Test rollout with many messages."""
        run = expt_logger.init(
            name="test-stress-rollout", api_key=shared_api_key, base_url=base_url
        )
        cleanup_experiments.append(run._experiment_id)

        # Create rollout with 50 messages
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(50)
        ]

        expt_logger.log_rollout(
            prompt="Long conversation",
            messages=messages,
            rewards={"quality": 0.8},
            commit=True,
        )
        time.sleep(1.0)

        # Verify structure preserved
        rollouts = fetch_rollouts(run._experiment_id, "train")
        assert len(rollouts["groups"]) > 0

        expt_logger.end()


# ============================================================================
# Test Class 11: Multi-process Tests
# ============================================================================


def _worker_process_log_metrics(
    worker_id: int,
    result_queue: multiprocessing.Queue,
) -> None:
    """Worker process that logs metrics using EXPT_LOGGER_EXPERIMENT_ID from environment.

    Environment variables (EXPT_LOGGER_EXPERIMENT_ID, EXPT_LOGGER_API_KEY,
    EXPT_LOGGER_BASE_URL) are inherited from parent process.
    """
    try:
        # Get experiment_id from env (should be set by parent)
        exp_id = os.environ.get("EXPT_LOGGER_EXPERIMENT_ID")
        if not exp_id:
            result_queue.put(("error", worker_id, "EXPT_LOGGER_EXPERIMENT_ID not set"))
            return

        # Initialize with is_main_process=False (reads from temp file)
        run = expt_logger.init(is_main_process=False)

        # Verify we got the same experiment ID from env
        assert run._experiment_id == exp_id

        # Log some worker-specific metrics
        expt_logger.log(
            {f"worker-{worker_id}-metric": float(worker_id)}, step=worker_id + 3, commit=True
        )
        time.sleep(0.2)

        expt_logger.end()
        result_queue.put(("success", worker_id, exp_id))
    except Exception as e:
        result_queue.put(("error", worker_id, str(e)))


@pytest.mark.integration
class TestMultiProcess:
    """Multi-process experiment logging scenarios."""

    def test_multiprocess_with_env_var(
        self,
        shared_api_key: str,
        base_url: str,
        cleanup_experiments: list[str],
        fetch_scalars,
    ) -> None:
        """Test multiple processes logging to same experiment via auto-set env var."""
        # Main process creates the experiment
        # init() automatically sets EXPT_LOGGER_EXPERIMENT_ID env var
        run = expt_logger.init(
            name="test-multiprocess-env",
            api_key=shared_api_key,
            base_url=base_url,
        )
        experiment_id = run._experiment_id
        cleanup_experiments.append(experiment_id)

        # Verify env var was auto-set
        assert os.environ.get("EXPT_LOGGER_EXPERIMENT_ID") == experiment_id

        # Log from main process
        expt_logger.log({"main-metric": 0.0}, step=1, commit=True)
        time.sleep(0.2)

        # Set API key and base URL for child processes (experiment ID already set)
        os.environ["EXPT_LOGGER_API_KEY"] = shared_api_key
        os.environ["EXPT_LOGGER_BASE_URL"] = base_url

        # Spawn worker processes that log to the same experiment
        num_workers = 3
        result_queue: multiprocessing.Queue = multiprocessing.Queue()
        processes = []

        for i in range(num_workers):
            p = multiprocessing.Process(
                target=_worker_process_log_metrics,
                args=(i + 1, result_queue),
            )
            processes.append(p)
            p.start()

        # Wait for all workers to complete
        for p in processes:
            p.join(timeout=10)

        # Check results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        # All workers should succeed
        for status, worker_id, result_exp_id in results:
            assert status == "success", f"Worker {worker_id} failed: {result_exp_id}"
            assert result_exp_id == experiment_id

        assert len(results) == num_workers
        expt_logger.end()

        # Verify all metrics are logged to the same experiment
        time.sleep(0.5)
        scalars = fetch_scalars(experiment_id, "train")

        # Main process metric
        assert "main-metric" in scalars

        # Worker metrics
        for i in range(num_workers):
            assert f"worker-{i + 1}-metric" in scalars

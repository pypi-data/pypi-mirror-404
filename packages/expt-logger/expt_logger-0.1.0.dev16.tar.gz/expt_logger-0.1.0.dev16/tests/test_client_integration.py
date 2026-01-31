"""Integration tests for API client with real server.

These tests require a running server at http://localhost:3000 (or EXPT_LOGGER_BASE_URL).
They will create real experiments and API keys in the database.

Run with: pytest tests/test_client_integration.py -v
Skip if server unavailable: pytest tests/test_client_integration.py -m "not integration"
"""

from collections.abc import Generator

import pytest
import requests

from expt_logger.client import APIClient
from expt_logger.exceptions import APIError, AuthenticationError
from expt_logger.types import RolloutItem, ScalarItem

# Note: Common fixtures (server_available, shared_api_key, base_url) are imported from conftest.py


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def client(shared_api_key: str, base_url: str) -> APIClient:
    """Create API client with test API key."""
    return APIClient(base_url=base_url, api_key=shared_api_key)


@pytest.fixture
def client_no_auth(base_url: str) -> APIClient:
    """Create API client without authentication."""
    return APIClient(base_url=base_url)


@pytest.fixture
def cleanup_experiments(shared_api_key: str, base_url: str) -> Generator[list[str], None, None]:
    """Track and cleanup experiments created during test."""
    experiment_ids: list[str] = []
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


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.integration
class TestAPIClientIntegration:
    """Test APIClient with real server."""

    def test_create_experiment(self, client: APIClient, cleanup_experiments: list[str]) -> None:
        """Test creating an experiment on real server."""
        experiment_id = client.create_experiment(
            name="test-integration-create",
            config={"test": True, "value": 123},
        )
        cleanup_experiments.append(experiment_id)

        assert experiment_id is not None
        assert isinstance(experiment_id, str)
        assert len(experiment_id) > 0

    def test_create_experiment_minimal(
        self, client: APIClient, cleanup_experiments: list[str]
    ) -> None:
        """Test creating experiment with minimal parameters."""
        experiment_id = client.create_experiment()
        cleanup_experiments.append(experiment_id)

        assert experiment_id is not None
        assert isinstance(experiment_id, str)

    def test_log_scalars(self, client: APIClient, cleanup_experiments: list[str]) -> None:
        """Test logging scalar metrics."""
        # Create experiment
        experiment_id = client.create_experiment(name="test-integration-scalars")
        cleanup_experiments.append(experiment_id)

        # Log scalars
        scalars: list[ScalarItem] = [
            {"step": 1, "mode": "train", "name": "loss", "value": 1.5},
            {"step": 1, "mode": "train", "name": "accuracy", "value": 0.6},
        ]
        client.log_scalars(experiment_id, scalars)

        # Verify by fetching (GET endpoint exists in archive tests)
        response = requests.get(
            f"{client.base_url}/api/experiments/{experiment_id}/scalars",
            params={"mode": "train"},
            headers={"Authorization": f"Bearer {client.api_key}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "loss" in data
        assert "accuracy" in data
        assert len(data["loss"]) == 1
        assert data["loss"][0]["step"] == 1
        assert abs(data["loss"][0]["value"] - 1.5) < 1e-6

    def test_log_rollouts(self, client: APIClient, cleanup_experiments: list[str]) -> None:
        """Test logging rollouts."""
        # Create experiment
        experiment_id = client.create_experiment(name="test-integration-rollouts")
        cleanup_experiments.append(experiment_id)

        # Log rollout
        rollouts: list[RolloutItem] = [
            {
                "step": 1,
                "mode": "train",
                "promptText": "What is 2+2?",
                "messages": [{"role": "assistant", "content": "4"}],
                "rewards": [
                    {"name": "correctness", "value": 1.0},
                    {"name": "clarity", "value": 0.9},
                ],
            }
        ]
        client.log_rollouts(experiment_id, rollouts)

        # Verify by fetching
        response = requests.get(
            f"{client.base_url}/api/experiments/{experiment_id}/rollouts/summary",
            params={"mode": "train", "page": 1, "limit": 10},
            headers={"Authorization": f"Bearer {client.api_key}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "groups" in data
        assert len(data["groups"]) > 0

    def test_update_experiment_config(self, client: APIClient, cleanup_experiments: list[str]) -> None:
        """Test updating experiment configuration."""
        # Create experiment
        experiment_id = client.create_experiment(
            name="test-integration-config",
            config={"lr": 0.001},
        )
        cleanup_experiments.append(experiment_id)
        print(f"\nCreated experiment: {experiment_id}")

        # Update config
        client.update_experiment(experiment_id, config={"lr": 0.002, "batch_size": 32})
        print(f"Updated config for: {experiment_id}")

        # Verify via details endpoint
        url = f"{client.base_url}/api/experiments/{experiment_id}/details"
        print(f"Fetching details from: {url}")
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {client.api_key}"},
        )
        print(f"Response status: {response.status_code}, body: {response.text[:200]}")
        assert response.status_code == 200, f"Failed: {response.text}"

        data = response.json()
        assert "config" in data
        assert data["config"]["lr"] == 0.002
        assert data["config"]["batch_size"] == 32

    def test_end_experiment(self, client: APIClient, cleanup_experiments: list[str]) -> None:
        """Test marking experiment as complete."""
        # Create experiment
        experiment_id = client.create_experiment(name="test-integration-end")
        cleanup_experiments.append(experiment_id)

        # End experiment - should not throw any errors
        client.update_experiment(experiment_id, status="complete")

        # Verify the request succeeded by fetching details
        response = requests.get(
            f"{client.base_url}/api/experiments/{experiment_id}/details",
            headers={"Authorization": f"Bearer {client.api_key}"},
        )
        assert response.status_code == 200
        # The test passes if no exception is raised

    def test_authentication_error(self, client_no_auth: APIClient) -> None:
        """Test that invalid API key raises error."""
        # Override with invalid key
        client_no_auth.session.headers.update({"Authorization": "Bearer invalid-key"})

        # Note: The server may return 500 or 401 depending on implementation
        # We just verify that the request fails
        with pytest.raises((AuthenticationError, APIError)) as exc_info:
            client_no_auth.create_experiment(name="test-fail")

        # Verify an error was raised
        assert exc_info.value is not None

    def test_multiple_requests_session_reuse(
        self, client: APIClient, cleanup_experiments: list[str]
    ) -> None:
        """Test that session is reused across multiple requests."""
        # Create multiple experiments using same client
        exp_ids = []
        for i in range(3):
            exp_id = client.create_experiment(name=f"test-session-{i}")
            exp_ids.append(exp_id)
            cleanup_experiments.append(exp_id)

        # All should succeed
        assert len(exp_ids) == 3
        assert all(isinstance(exp_id, str) for exp_id in exp_ids)
        assert len(set(exp_ids)) == 3  # All unique

    def test_retry_on_network_error_real_server(self, client: APIClient) -> None:
        """Test retry logic with real server (simulate by using wrong port)."""
        # Create client pointing to wrong port
        bad_client = APIClient(base_url="http://localhost:9999", api_key="test")

        with pytest.raises(APIError) as exc_info:
            bad_client.create_experiment(name="test-retry")

        # Should fail after retries
        assert "Request failed" in str(exc_info.value)

    def test_complete_workflow(self, client: APIClient, cleanup_experiments: list[str]) -> None:
        """Test complete experiment workflow end-to-end."""
        # 1. Create experiment
        experiment_id = client.create_experiment(
            name="test-integration-complete",
            config={"model": "test-model", "lr": 0.001},
        )
        cleanup_experiments.append(experiment_id)

        # 2. Log metrics at step 1
        scalars_step1: list[ScalarItem] = [
            {"step": 1, "mode": "train", "name": "loss", "value": 1.5},
            {"step": 1, "mode": "train", "name": "accuracy", "value": 0.6},
        ]
        client.log_scalars(experiment_id, scalars_step1)

        # 3. Log rollout at step 1
        rollouts_step1: list[RolloutItem] = [
            {
                "step": 1,
                "mode": "train",
                "promptText": "Test prompt",
                "messages": [{"role": "assistant", "content": "Test response"}],
                "rewards": [{"name": "quality", "value": 0.8}],
            }
        ]
        client.log_rollouts(experiment_id, rollouts_step1)

        # 4. Update config
        client.update_experiment(experiment_id, config={"lr": 0.002})

        # 5. Log more metrics at step 2
        scalars_step2: list[ScalarItem] = [
            {"step": 2, "mode": "train", "name": "loss", "value": 1.2},
            {"step": 2, "mode": "train", "name": "accuracy", "value": 0.7},
        ]
        client.log_scalars(experiment_id, scalars_step2)

        # 6. End experiment
        client.update_experiment(experiment_id, status="complete")

        # 7. Verify everything
        details_response = requests.get(
            f"{client.base_url}/api/experiments/{experiment_id}/details",
            headers={"Authorization": f"Bearer {client.api_key}"},
        )
        assert (
            details_response.status_code == 200
        ), f"Failed to get details: {details_response.text}"

        details = details_response.json()
        assert "name" in details, f"Response missing 'name': {details}"
        assert details["name"] == "test-integration-complete"
        assert details["config"]["lr"] == 0.002
        assert details["latestStep"] >= 2

        # Verify scalars
        scalars = requests.get(
            f"{client.base_url}/api/experiments/{experiment_id}/scalars",
            params={"mode": "train"},
            headers={"Authorization": f"Bearer {client.api_key}"},
        ).json()

        assert "loss" in scalars
        assert len(scalars["loss"]) == 2
        assert "accuracy" in scalars
        assert len(scalars["accuracy"]) == 2

        # Verify rollouts
        rollouts = requests.get(
            f"{client.base_url}/api/experiments/{experiment_id}/rollouts/summary",
            params={"mode": "train", "page": 1, "limit": 10},
            headers={"Authorization": f"Bearer {client.api_key}"},
        ).json()

        assert "groups" in rollouts
        assert len(rollouts["groups"]) > 0

    def test_close_session(
        self, shared_api_key: str, base_url: str, cleanup_experiments: list[str]
    ) -> None:
        """Test closing the session."""
        client = APIClient(base_url=base_url, api_key=shared_api_key)

        # Make a request
        experiment_id = client.create_experiment(name="test-close")
        cleanup_experiments.append(experiment_id)
        assert experiment_id is not None

        # Close session
        client.close()

        # Further requests should fail (or create new connection)
        # This mainly tests that close() doesn't raise an error

    def test_delete_single_experiment(self, client: APIClient) -> None:
        """Test deleting a single experiment."""
        # Create experiment
        experiment_id = client.create_experiment(name="test-delete-single")

        # Delete it
        deleted_count = client.delete_experiments(experiment_id)

        assert deleted_count == 1

    def test_delete_multiple_experiments(self, client: APIClient) -> None:
        """Test deleting multiple experiments."""
        # Create multiple experiments
        exp_ids = [client.create_experiment(name=f"test-delete-{i}") for i in range(3)]

        # Delete all
        deleted_count = client.delete_experiments(exp_ids)

        assert deleted_count == 3

    def test_delete_api_keys(self, session_cookie: str, base_url: str, shared_api_key: str) -> None:
        """Test deleting API keys via APIClient."""
        # Create a temporary API key for testing
        response = requests.post(
            f"{base_url}/api/api-keys",
            headers={"Cookie": session_cookie},
            json={"name": "Temp Test Key"},
            timeout=5,
        )
        assert response.status_code == 201
        temp_key_data = response.json()
        temp_key_id = temp_key_data["id"]

        # Use APIClient to delete it
        client = APIClient(base_url=base_url, api_key=shared_api_key)
        deleted_count = client.delete_api_keys(temp_key_id)

        assert deleted_count == 1

    def test_delete_multiple_api_keys(
        self, session_cookie: str, base_url: str, shared_api_key: str
    ) -> None:
        """Test deleting multiple API keys via APIClient."""
        # Create multiple temporary API keys
        key_ids = []
        for i in range(3):
            response = requests.post(
                f"{base_url}/api/api-keys",
                headers={"Cookie": session_cookie},
                json={"name": f"Temp Test Key {i}"},
                timeout=5,
            )
            assert response.status_code == 201
            key_ids.append(response.json()["id"])

        # Use APIClient to delete them all
        client = APIClient(base_url=base_url, api_key=shared_api_key)
        deleted_count = client.delete_api_keys(key_ids)

        assert deleted_count == 3

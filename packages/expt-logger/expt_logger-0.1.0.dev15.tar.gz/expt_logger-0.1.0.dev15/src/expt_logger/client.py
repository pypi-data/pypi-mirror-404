"""API client for communicating with the experiment tracking server."""

import logging
import time
from typing import Any

import requests

from expt_logger.exceptions import APIError, AuthenticationError
from expt_logger.types import RolloutItem, ScalarItem, ScalarValue

logger = logging.getLogger(__name__)

# Max estimated payload size per request (1 MB)
MAX_PAYLOAD_SIZE_BYTES = 1_000_000


def _estimate_rollout_size(rollout: RolloutItem) -> int:
    """Estimate the size of a rollout in bytes based on text content."""
    size = len(rollout["promptText"])
    for msg in rollout["messages"]:
        size += len(msg["content"])
    return size


def _chunk_rollouts(rollouts: list[RolloutItem]) -> list[list[RolloutItem]]:
    """Split rollouts into chunks that each stay under MAX_PAYLOAD_SIZE_BYTES.

    Each chunk will contain at least one rollout, even if that single
    rollout exceeds the size limit.
    """
    chunks: list[list[RolloutItem]] = []
    current_chunk: list[RolloutItem] = []
    current_size = 0

    for rollout in rollouts:
        rollout_size = _estimate_rollout_size(rollout)

        if current_chunk and current_size + rollout_size > MAX_PAYLOAD_SIZE_BYTES:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0

        current_chunk.append(rollout)
        current_size += rollout_size

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


class APIClient:
    """HTTP client for experiment tracking API with retry logic."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize API client.

        Args:
            base_url: Base URL of the API server (without trailing slash)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        # Create session for connection pooling
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> requests.Response:
        """Execute HTTP request with retry logic and exponential backoff.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            url: Full URL to request
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            APIError: If request fails after all retries
            AuthenticationError: If request fails with 401 status
        """
        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)

                # Check for authentication errors
                if response.status_code == 401:
                    raise AuthenticationError(
                        self._parse_error_message(response) or "Authentication failed"
                    )

                # Raise for other HTTP errors
                response.raise_for_status()
                return response

            except requests.RequestException as e:
                last_exception = e

                # Don't retry on authentication errors
                if isinstance(e, AuthenticationError):
                    raise

                # On last attempt, raise the error
                if attempt == self.max_retries - 1:
                    # Extract status code from response if available
                    status_code = None
                    error_response: requests.Response | None = getattr(e, "response", None)
                    if error_response is not None:
                        status_code = getattr(error_response, "status_code", None)

                    error_msg = self._parse_error_message(error_response) or str(e)
                    raise APIError(f"Request failed: {error_msg}", status_code=status_code)

                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2**attempt
                time.sleep(wait_time)

        # Should never reach here, but just in case
        raise APIError(f"Request failed after {self.max_retries} retries: {last_exception}")

    def _parse_error_message(self, response: requests.Response | None) -> str | None:
        """Extract error message from response.

        Args:
            response: HTTP response object

        Returns:
            Error message string or None
        """
        if response is None:
            return None

        try:
            data = response.json()
            # Try common error message fields
            error: str | None = data.get("error") or data.get("message") or data.get("detail")
            return error
        except (ValueError, KeyError):
            # Fall back to response text
            return response.text if response.text else None

    def create_experiment(
        self,
        name: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> str:
        """Create a new experiment.

        Args:
            name: Optional experiment name
            config: Optional experiment configuration

        Returns:
            Experiment ID string

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}/api/experiments"
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if config is not None:
            payload["config"] = config

        response = self._request("POST", url, json=payload)
        data = response.json()
        experiment_id: str = data["experimentId"]
        return experiment_id

    def get_experiment(self, experiment_id: str) -> dict[str, Any]:
        """Get experiment details by ID.

        Args:
            experiment_id: Experiment ID

        Returns:
            Dict with experiment details (id, name, createdAt, config, status)

        Raises:
            APIError: If experiment not found or request fails
        """
        url = f"{self.base_url}/api/experiments/{experiment_id}"
        response = self._request("GET", url)
        return response.json()

    def log_scalars(
        self,
        experiment_id: str,
        scalars: list[ScalarItem],
    ) -> None:
        """Log scalar metrics for an experiment.

        Args:
            experiment_id: Experiment ID
            scalars: List of scalar metrics with step, mode, name, and value

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}/api/experiments/{experiment_id}/scalars"
        payload = {"scalars": scalars}
        self._request("POST", url, json=payload)

    def get_scalars(
        self,
        experiment_id: str,
        mode: str,
    ) -> dict[str, list[ScalarValue]]:
        """Get scalars for an experiment filtered by mode.

        Args:
            experiment_id: Experiment ID
            mode: Mode to filter by (e.g., "train", "eval")

        Returns:
            Dictionary mapping scalar types to lists of {step, value} dicts.
            Example: {
                "KL_divergence": [{"step": 1, "value": 0.52}, ...],
                "reward": [{"step": 1, "value": 0.85}, ...]
            }

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}/api/experiments/{experiment_id}/scalars"
        params = {"mode": mode}
        response = self._request("GET", url, params=params)
        result: dict[str, list[ScalarValue]] = response.json()
        return result

    def log_rollouts(
        self,
        experiment_id: str,
        rollouts: list[RolloutItem],
    ) -> None:
        """Log rollouts for an experiment.

        Rollouts are automatically chunked into multiple requests if the
        estimated payload size exceeds MAX_PAYLOAD_SIZE_BYTES (1 MB).

        Args:
            experiment_id: Experiment ID
            rollouts: List of rollouts with step, mode, promptText, messages, and rewards

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}/api/experiments/{experiment_id}/rollouts"
        chunks = _chunk_rollouts(rollouts)
        if len(chunks) > 1:
            logger.debug(
                f"Splitting {len(rollouts)} rollouts into {len(chunks)} chunks"
            )
        for chunk in chunks:
            payload = {"rollouts": chunk}
            self._request("POST", url, json=payload)

    def update_experiment(
        self,
        experiment_id: str,
        config: dict[str, Any] | None = None,
        name: str | None = None,
        status: str | None = None,
    ) -> None:
        """Update experiment config, name, and/or status.

        Args:
            experiment_id: Experiment ID
            config: Optional configuration updates
            name: Optional name update
            status: Optional status update ("active" or "complete")

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}/api/experiments/{experiment_id}"
        payload: dict[str, Any] = {}
        if config is not None:
            payload["config"] = config
        if name is not None:
            payload["name"] = name
        if status is not None:
            payload["status"] = status

        self._request("PUT", url, json=payload)

    def delete_experiments(
        self,
        experiment_ids: list[str] | str,
    ) -> int:
        """Delete one or more experiments.

        Args:
            experiment_ids: Single experiment ID or list of IDs to delete

        Returns:
            Number of experiments deleted

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}/api/experiments"

        # Handle both single ID and list of IDs
        payload: dict[str, Any]
        if isinstance(experiment_ids, str):
            payload = {"id": experiment_ids}
        else:
            payload = {"ids": experiment_ids}

        response = self._request("DELETE", url, json=payload)
        data = response.json()
        return int(data.get("deletedCount", 0))

    def delete_api_keys(
        self,
        api_key_ids: list[str] | str,
    ) -> int:
        """Delete one or more API keys.

        Args:
            api_key_ids: Single API key ID or list of IDs to delete

        Returns:
            Number of API keys deleted

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}/api/api-keys"

        # Handle both single ID and list of IDs
        payload: dict[str, Any]
        if isinstance(api_key_ids, str):
            payload = {"id": api_key_ids}
        else:
            payload = {"ids": api_key_ids}

        response = self._request("DELETE", url, json=payload)
        data = response.json()
        return int(data.get("deletedCount", 0))

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

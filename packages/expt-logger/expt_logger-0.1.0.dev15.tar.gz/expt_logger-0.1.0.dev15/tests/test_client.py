"""Tests for API client."""

import time
from unittest.mock import Mock, patch

import pytest
import requests

from expt_logger.client import APIClient
from expt_logger.exceptions import APIError, AuthenticationError


@pytest.fixture
def client():
    """Create a test API client."""
    return APIClient(base_url="https://test.example.com", api_key="test-key")


@pytest.fixture
def client_no_auth():
    """Create a test API client without authentication."""
    return APIClient(base_url="https://test.example.com")


def test_client_initialization(client):
    """Test client initialization with API key."""
    assert client.base_url == "https://test.example.com"
    assert client.api_key == "test-key"
    assert client.timeout == 30
    assert client.max_retries == 3
    assert "Authorization" in client.session.headers
    assert client.session.headers["Authorization"] == "Bearer test-key"


def test_client_initialization_without_api_key(client_no_auth):
    """Test client initialization without API key."""
    assert client_no_auth.base_url == "https://test.example.com"
    assert client_no_auth.api_key is None
    assert "Authorization" not in client_no_auth.session.headers


def test_successful_request(client):
    """Test successful HTTP request."""
    with patch.object(client.session, "request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        response = client._request("GET", "https://test.example.com/api/test")

        assert response.status_code == 200
        assert response.json() == {"data": "test"}
        mock_request.assert_called_once()


def test_retry_on_network_error(client):
    """Test retry logic on network errors."""
    with patch.object(client.session, "request") as mock_request:
        # First two attempts fail, third succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.side_effect = [
            requests.ConnectionError("Network error"),
            requests.Timeout("Request timeout"),
            mock_response,
        ]

        start_time = time.time()
        response = client._request("GET", "https://test.example.com/api/test")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert mock_request.call_count == 3
        # Should wait 1s + 2s = 3s total (with some tolerance)
        assert elapsed >= 3.0
        assert elapsed < 4.0


def test_exponential_backoff_timing(client):
    """Test exponential backoff timing (1s, 2s, 4s)."""
    with patch.object(client.session, "request") as mock_request, patch("time.sleep") as mock_sleep:
        # All attempts fail
        mock_request.side_effect = requests.ConnectionError("Network error")

        with pytest.raises(APIError):
            client._request("GET", "https://test.example.com/api/test")

        # Should have 3 attempts
        assert mock_request.call_count == 3
        # Should sleep 1s, then 2s (not 4s because we fail after 3rd attempt)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)  # First retry: 2^0 = 1s
        mock_sleep.assert_any_call(2)  # Second retry: 2^1 = 2s


def test_final_failure_after_retries(client):
    """Test that APIError is raised after max retries."""
    with patch.object(client.session, "request") as mock_request:
        mock_request.side_effect = requests.ConnectionError("Network error")

        with pytest.raises(APIError) as exc_info:
            client._request("GET", "https://test.example.com/api/test")

        assert "Request failed" in str(exc_info.value)
        assert mock_request.call_count == 3


def test_http_500_error_with_retry(client):
    """Test retry on HTTP 500 error."""
    with patch.object(client.session, "request") as mock_request:
        # First attempt fails with 500, second succeeds
        error_response = Mock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = requests.HTTPError("Server error")

        success_response = Mock()
        success_response.status_code = 200

        mock_request.side_effect = [
            error_response,
            success_response,
        ]

        response = client._request("GET", "https://test.example.com/api/test")

        assert response.status_code == 200
        assert mock_request.call_count == 2


def test_authentication_error_no_retry(client):
    """Test that 401 errors don't retry."""
    with patch.object(client.session, "request") as mock_request:
        error_response = Mock()
        error_response.status_code = 401
        error_response.json.return_value = {"error": "Invalid API key"}
        mock_request.return_value = error_response

        with pytest.raises(AuthenticationError) as exc_info:
            client._request("GET", "https://test.example.com/api/test")

        assert "Invalid API key" in str(exc_info.value)
        assert exc_info.value.status_code == 401
        # Should not retry on auth errors
        assert mock_request.call_count == 1


def test_parse_error_message_json(client):
    """Test parsing error message from JSON response."""
    response = Mock()
    response.json.return_value = {"error": "Something went wrong"}
    response.text = "fallback text"

    message = client._parse_error_message(response)
    assert message == "Something went wrong"


def test_parse_error_message_alternative_fields(client):
    """Test parsing error message from alternative JSON fields."""
    # Test "message" field
    response = Mock()
    response.json.return_value = {"message": "Error message"}
    assert client._parse_error_message(response) == "Error message"

    # Test "detail" field
    response.json.return_value = {"detail": "Error detail"}
    assert client._parse_error_message(response) == "Error detail"


def test_parse_error_message_fallback_to_text(client):
    """Test fallback to response text when JSON parsing fails."""
    response = Mock()
    response.json.side_effect = ValueError("Invalid JSON")
    response.text = "Plain text error"

    message = client._parse_error_message(response)
    assert message == "Plain text error"


def test_parse_error_message_none_response(client):
    """Test parsing error message with None response."""
    message = client._parse_error_message(None)
    assert message is None


def test_create_experiment(client):
    """Test creating an experiment."""
    with patch.object(client, "_request") as mock_request:
        mock_response = Mock()
        mock_response.json.return_value = {"experimentId": "exp-123"}
        mock_request.return_value = mock_response

        experiment_id = client.create_experiment(
            name="test-experiment",
            config={"lr": 0.001},
        )

        assert experiment_id == "exp-123"
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "https://test.example.com/api/experiments"
        assert call_args[1]["json"] == {
            "name": "test-experiment",
            "config": {"lr": 0.001},
        }


def test_create_experiment_minimal(client):
    """Test creating an experiment with minimal parameters."""
    with patch.object(client, "_request") as mock_request:
        mock_response = Mock()
        mock_response.json.return_value = {"experimentId": "exp-456"}
        mock_request.return_value = mock_response

        experiment_id = client.create_experiment()

        assert experiment_id == "exp-456"
        call_args = mock_request.call_args
        assert call_args[1]["json"] == {}


def test_log_scalars(client):
    """Test logging scalar metrics."""
    with patch.object(client, "_request") as mock_request:
        scalars = [
            {"step": 1, "mode": "train", "name": "loss", "value": 0.5},
            {"step": 1, "mode": "train", "name": "accuracy", "value": 0.9},
        ]

        client.log_scalars("exp-123", scalars)

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "https://test.example.com/api/experiments/exp-123/scalars"
        assert call_args[1]["json"] == {"scalars": scalars}


def test_get_scalars(client):
    """Test getting scalar metrics filtered by mode."""
    with patch.object(client, "_request") as mock_request:
        mock_response = Mock()
        mock_response.json.return_value = {
            "KL_divergence": [
                {"step": 1, "value": 0.52},
                {"step": 2, "value": 0.48},
            ],
            "reward": [
                {"step": 1, "value": 0.85},
                {"step": 2, "value": 0.90},
            ],
        }
        mock_request.return_value = mock_response

        result = client.get_scalars("exp-123", "train")

        assert result == {
            "KL_divergence": [
                {"step": 1, "value": 0.52},
                {"step": 2, "value": 0.48},
            ],
            "reward": [
                {"step": 1, "value": 0.85},
                {"step": 2, "value": 0.90},
            ],
        }
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "https://test.example.com/api/experiments/exp-123/scalars"
        assert call_args[1]["params"] == {"mode": "train"}


def test_log_rollouts(client):
    """Test logging rollouts."""
    with patch.object(client, "_request") as mock_request:
        rollouts = [
            {
                "step": 1,
                "mode": "train",
                "promptText": "What is 2+2?",
                "messages": [{"role": "assistant", "content": "4"}],
                "rewards": [{"name": "correctness", "value": 1.0}],
            }
        ]

        client.log_rollouts("exp-123", rollouts)

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "https://test.example.com/api/experiments/exp-123/rollouts"
        assert call_args[1]["json"] == {"rollouts": rollouts}


def test_log_rollouts_chunked(client):
    """Test that rollouts with many messages are split into multiple requests."""
    # Each rollout has many small messages totaling ~600KB
    def make_rollout(step):
        return {
            "step": step,
            "mode": "train",
            "promptText": "What is machine learning?",
            "messages": [
                {"role": "user" if i % 2 == 0 else "assistant", "content": "x" * 500}
                for i in range(1200)  # 1200 messages * 500 bytes = ~600KB
            ],
            "rewards": [{"name": "correctness", "value": 1.0}],
        }

    rollouts = [make_rollout(1), make_rollout(2)]

    with patch.object(client, "_request") as mock_request:
        client.log_rollouts("exp-123", rollouts)

        # Should be split into 2 requests since ~600KB + ~600KB > 1MB
        assert mock_request.call_count == 2
        first_call = mock_request.call_args_list[0]
        second_call = mock_request.call_args_list[1]
        assert first_call[1]["json"] == {"rollouts": [rollouts[0]]}
        assert second_call[1]["json"] == {"rollouts": [rollouts[1]]}


def test_log_rollouts_single_oversized(client):
    """Test that a single rollout with a huge conversation is still sent."""
    rollouts = [
        {
            "step": 1,
            "mode": "train",
            "promptText": "Summarize this book",
            "messages": [
                {"role": "user" if i % 2 == 0 else "assistant", "content": "x" * 1000}
                for i in range(2000)  # 2000 messages * 1000 bytes = ~2MB
            ],
            "rewards": [{"name": "r", "value": 1.0}],
        },
    ]

    with patch.object(client, "_request") as mock_request:
        client.log_rollouts("exp-123", rollouts)

        # Should still send it in a single request (can't split further)
        mock_request.assert_called_once()
        assert mock_request.call_args[1]["json"] == {"rollouts": rollouts}


def test_log_rollouts_small_not_chunked(client):
    """Test that small rollouts are sent in a single request."""
    rollouts = [
        {
            "step": i,
            "mode": "train",
            "promptText": "short prompt",
            "messages": [{"role": "assistant", "content": "short"}],
            "rewards": [{"name": "r", "value": 1.0}],
        }
        for i in range(10)
    ]

    with patch.object(client, "_request") as mock_request:
        client.log_rollouts("exp-123", rollouts)

        # All small, should be a single request
        mock_request.assert_called_once()
        assert mock_request.call_args[1]["json"] == {"rollouts": rollouts}


def test_update_config(client):
    """Test updating experiment configuration."""
    with patch.object(client, "_request") as mock_request:
        updates = {"lr": 0.002, "batch_size": 64}

        client.update_experiment("exp-123", config=updates)

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "https://test.example.com/api/experiments/exp-123"
        assert call_args[1]["json"] == {"config": updates}


def test_end_experiment(client):
    """Test ending an experiment."""
    with patch.object(client, "_request") as mock_request:
        client.update_experiment("exp-123", status="complete")

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "https://test.example.com/api/experiments/exp-123"
        assert call_args[1]["json"] == {"status": "complete"}


def test_close_session(client):
    """Test closing the HTTP session."""
    with patch.object(client.session, "close") as mock_close:
        client.close()
        mock_close.assert_called_once()


def test_default_timeout(client):
    """Test that default timeout is set."""
    with patch.object(client.session, "request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        client._request("GET", "https://test.example.com/api/test")

        call_args = mock_request.call_args
        assert call_args[1]["timeout"] == 30


def test_custom_timeout(client):
    """Test custom timeout parameter."""
    with patch.object(client.session, "request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        client._request("GET", "https://test.example.com/api/test", timeout=60)

        call_args = mock_request.call_args
        assert call_args[1]["timeout"] == 60


def test_session_reuse(client):
    """Test that session is reused across requests."""
    with patch.object(client.session, "request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Make multiple requests
        client._request("GET", "https://test.example.com/api/test1")
        client._request("GET", "https://test.example.com/api/test2")

        # Should use the same session
        assert mock_request.call_count == 2
        # Verify headers are still set
        assert client.session.headers["Authorization"] == "Bearer test-key"


def test_http_error_with_status_code(client):
    """Test that HTTP errors include status code."""
    with patch.object(client.session, "request") as mock_request:
        error_response = Mock()
        error_response.status_code = 503
        error_response.json.return_value = {"error": "Service unavailable"}

        # Create HTTPError with response attached
        http_error = requests.HTTPError("503 Error")
        http_error.response = error_response
        error_response.raise_for_status.side_effect = http_error

        mock_request.return_value = error_response

        with pytest.raises(APIError) as exc_info:
            client._request("GET", "https://test.example.com/api/test")

        assert exc_info.value.status_code == 503
        assert "Service unavailable" in str(exc_info.value)

"""Tests for environment configuration."""

import pytest

from expt_logger.env import DEFAULT_BASE_URL, get_api_key, get_base_url, get_experiment_id
from expt_logger.exceptions import ConfigurationError


def test_get_api_key_from_override():
    """Test get_api_key with explicit override."""
    api_key = get_api_key(override="test-key-123")
    assert api_key == "test-key-123"


def test_get_api_key_from_env(monkeypatch):
    """Test get_api_key from environment variable."""
    monkeypatch.setenv("EXPT_LOGGER_API_KEY", "env-key-456")
    api_key = get_api_key()
    assert api_key == "env-key-456"


def test_get_api_key_override_takes_precedence(monkeypatch):
    """Test that override takes precedence over environment variable."""
    monkeypatch.setenv("EXPT_LOGGER_API_KEY", "env-key")
    api_key = get_api_key(override="override-key")
    assert api_key == "override-key"


def test_get_api_key_missing_raises_error(monkeypatch):
    """Test that missing API key raises ConfigurationError."""
    monkeypatch.delenv("EXPT_LOGGER_API_KEY", raising=False)
    with pytest.raises(ConfigurationError) as exc_info:
        get_api_key()
    assert "API key not found" in str(exc_info.value)


def test_get_base_url_from_override():
    """Test get_base_url with explicit override."""
    base_url = get_base_url(override="https://custom.example.com")
    assert base_url == "https://custom.example.com"


def test_get_base_url_from_env(monkeypatch):
    """Test get_base_url from environment variable."""
    monkeypatch.setenv("EXPT_LOGGER_BASE_URL", "https://test.example.com")
    base_url = get_base_url()
    assert base_url == "https://test.example.com"


def test_get_base_url_default(monkeypatch):
    """Test get_base_url returns default when not set."""
    monkeypatch.delenv("EXPT_LOGGER_BASE_URL", raising=False)
    base_url = get_base_url()
    assert base_url == DEFAULT_BASE_URL


def test_get_base_url_override_takes_precedence(monkeypatch):
    """Test that override takes precedence over environment variable."""
    monkeypatch.setenv("EXPT_LOGGER_BASE_URL", "https://env.example.com")
    base_url = get_base_url(override="https://override.example.com")
    assert base_url == "https://override.example.com"


def test_get_base_url_strips_trailing_slash():
    """Test that trailing slashes are removed from base URL."""
    base_url = get_base_url(override="https://example.com/")
    assert base_url == "https://example.com"

    base_url = get_base_url(override="https://example.com///")
    assert base_url == "https://example.com"


def test_get_base_url_strips_trailing_slash_from_env(monkeypatch):
    """Test that trailing slashes are removed from environment variable."""
    monkeypatch.setenv("EXPT_LOGGER_BASE_URL", "https://test.example.com/")
    base_url = get_base_url()
    assert base_url == "https://test.example.com"


def test_get_experiment_id_from_override():
    """Test get_experiment_id returns override value."""
    experiment_id = get_experiment_id(override="override-exp-123")
    assert experiment_id == "override-exp-123"


def test_get_experiment_id_override_takes_precedence(monkeypatch):
    """Test override takes precedence over environment variable."""
    monkeypatch.setenv("EXPT_LOGGER_EXPERIMENT_ID", "env-exp-456")
    experiment_id = get_experiment_id(override="override-exp-789")
    assert experiment_id == "override-exp-789"


def test_get_experiment_id_from_temp_file():
    """Test get_experiment_id reads from temp file."""
    import os

    from expt_logger.env import get_experiment_id_file_path

    # Create temp file with experiment ID
    experiment_id_file = get_experiment_id_file_path()
    with open(experiment_id_file, "w") as f:
        f.write("env-exp-456")

    try:
        experiment_id = get_experiment_id(is_main_process=False)
        assert experiment_id == "env-exp-456"
    finally:
        # Cleanup
        if os.path.isfile(experiment_id_file):
            os.remove(experiment_id_file)


def test_get_experiment_id_returns_none_when_file_not_found():
    """Test get_experiment_id returns None when temp file doesn't exist."""
    import os

    from expt_logger.env import get_experiment_id_file_path

    # Ensure temp file doesn't exist
    experiment_id_file = get_experiment_id_file_path()
    if os.path.isfile(experiment_id_file):
        os.remove(experiment_id_file)

    experiment_id = get_experiment_id()
    assert experiment_id is None


def test_get_experiment_id_strips_whitespace():
    """Test get_experiment_id strips whitespace from file content."""
    import os

    from expt_logger.env import get_experiment_id_file_path

    # Create temp file with whitespace
    experiment_id_file = get_experiment_id_file_path()
    with open(experiment_id_file, "w") as f:
        f.write("  test-exp-id  \n")

    try:
        experiment_id = get_experiment_id(is_main_process=False)
        assert experiment_id == "test-exp-id"
    finally:
        # Cleanup
        if os.path.isfile(experiment_id_file):
            os.remove(experiment_id_file)

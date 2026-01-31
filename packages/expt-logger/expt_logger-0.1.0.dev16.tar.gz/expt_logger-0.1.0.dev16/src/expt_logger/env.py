"""Environment configuration for expt-logger."""

import os
import tempfile

from expt_logger.exceptions import ConfigurationError

DEFAULT_BASE_URL = "https://app.cgft.io"


def get_api_key(override: str | None = None) -> str:
    """Get API key from override or environment variable.

    Priority:
    1. Explicit override parameter
    2. EXPT_LOGGER_API_KEY environment variable
    3. Raise ConfigurationError if not found

    Args:
        override: Optional API key to use instead of environment variable

    Returns:
        API key string

    Raises:
        ConfigurationError: If no API key is found
    """
    if override is not None:
        return override

    api_key = os.environ.get("EXPT_LOGGER_API_KEY")
    if api_key is None:
        raise ConfigurationError(
            "API key not found. Set EXPT_LOGGER_API_KEY environment variable "
            "or pass api_key parameter."
        )

    return api_key


def get_base_url(override: str | None = None) -> str:
    """Get base URL from override or environment variable.

    Priority:
    1. Explicit override parameter
    2. EXPT_LOGGER_BASE_URL environment variable
    3. Default production server URL

    Args:
        override: Optional base URL to use instead of environment variable

    Returns:
        Base URL string with trailing slashes removed
    """
    if override is not None:
        return override.rstrip("/")

    base_url = os.environ.get("EXPT_LOGGER_BASE_URL", DEFAULT_BASE_URL)
    return base_url.rstrip("/")


def get_experiment_id_file_path() -> str:
    """Get the file path for the experiment ID file in the temp directory.

    Returns:
        Full file path as a string
    """
    temp_dir = tempfile.gettempdir()
    experiment_id_file = os.path.join(temp_dir, "expt-logger-experiment-id.txt")
    return experiment_id_file


def get_experiment_id(override: str | None = None, is_main_process: bool = True) -> str | None:
    """Get experiment ID from override, environment variable, or temp file.

    Priority:
    1. Explicit override parameter
    2. EXPT_LOGGER_EXPERIMENT_ID environment variable (supports attaching to existing experiments)
    3. expt-logger-experiment-id.txt file in temp directory (for subprocess discovery, only if is_main_process=False)

    Args:
        override: Optional explicit experiment ID override
        is_main_process: If True, do not check temp file (only override and env var).
                        If False, check temp file as fallback.

    Returns:
        Experiment ID string or None if not found
    """
    if override is not None:
        return override.strip()

    # Check environment variable first (supports attaching to existing experiments)
    experiment_id = os.environ.get("EXPT_LOGGER_EXPERIMENT_ID")
    if experiment_id is not None:
        return experiment_id.strip()

    # For main process, don't check temp file (allows creating new experiments)
    if is_main_process:
        return None

    # Fall back to temp file (used by subprocesses when main process hasn't set the env var yet)
    experiment_id_file = get_experiment_id_file_path()

    if os.path.isfile(experiment_id_file):
        with open(experiment_id_file) as f:
            experiment_id = f.read().strip()
            return experiment_id

    return None

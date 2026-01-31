"""Configuration management with auto-sync to server."""

import json
import logging
from queue import Queue
from threading import RLock
from typing import Any

logger = logging.getLogger(__name__)


class Config:
    """Thread-safe configuration with dict-like and attribute access.

    Provides auto-sync to server via command queue. All writes are
    validated for JSON serializability.
    """

    def __init__(
        self,
        initial_data: dict[str, Any] | None = None,
        queue: Queue[tuple[str, Any]] | None = None,
    ):
        """Initialize configuration.

        Args:
            initial_data: Initial configuration data
            queue: Optional command queue for auto-sync
        """
        self._data: dict[str, Any] = {}
        self._queue = queue
        self._lock = RLock()

        if initial_data:
            # Validate initial data
            self._validate_json_serializable(initial_data)
            self._data.update(initial_data)

    def _validate_json_serializable(self, value: Any) -> None:
        """Validate that value is JSON serializable.

        Args:
            value: Value to validate

        Raises:
            ValueError: If value is not JSON serializable
        """
        try:
            json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Configuration value must be JSON serializable: {e}")

    def _enqueue_sync(self) -> None:
        """Enqueue config update command to worker thread."""
        if self._queue is not None:
            # Send entire config as update
            with self._lock:
                config_copy = self._data.copy()
            self._queue.put(("config_update", {"updates": config_copy}))

    def __getattr__(self, key: str) -> Any:
        """Get config value via attribute access.

        Args:
            key: Configuration key

        Returns:
            Configuration value

        Raises:
            AttributeError: If key not found
        """
        # Avoid recursion for internal attributes
        if key.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

        with self._lock:
            if key in self._data:
                return self._data[key]
        raise AttributeError(f"Configuration has no key '{key}'")

    def __setattr__(self, key: str, value: Any) -> None:
        """Set config value via attribute access.

        Args:
            key: Configuration key
            value: Configuration value
        """
        # Internal attributes bypass config storage
        if key.startswith("_"):
            object.__setattr__(self, key, value)
            return

        # Validate before storing
        self._validate_json_serializable(value)

        with self._lock:
            self._data[key] = value

        # Enqueue sync after lock released
        self._enqueue_sync()

    def __getitem__(self, key: str) -> Any:
        """Get config value via dict access.

        Args:
            key: Configuration key

        Returns:
            Configuration value

        Raises:
            KeyError: If key not found
        """
        with self._lock:
            return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set config value via dict access.

        Args:
            key: Configuration key
            value: Configuration value
        """
        # Validate before storing
        self._validate_json_serializable(value)

        with self._lock:
            self._data[key] = value

        # Enqueue sync after lock released
        self._enqueue_sync()

    def __contains__(self, key: str) -> bool:
        """Check if key exists in config.

        Args:
            key: Configuration key

        Returns:
            True if key exists
        """
        with self._lock:
            return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with default.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        with self._lock:
            return self._data.get(key, default)

    def update(self, updates: dict[str, Any]) -> None:
        """Bulk update configuration.

        Args:
            updates: Dictionary of updates to apply
        """
        # Validate all updates first
        self._validate_json_serializable(updates)

        with self._lock:
            self._data.update(updates)

        # Enqueue sync after lock released
        self._enqueue_sync()

    def to_dict(self) -> dict[str, Any]:
        """Get copy of configuration data.

        Returns:
            Copy of configuration dictionary
        """
        with self._lock:
            return self._data.copy()

    def __repr__(self) -> str:
        """String representation of config.

        Returns:
            String representation
        """
        with self._lock:
            return f"Config({self._data!r})"

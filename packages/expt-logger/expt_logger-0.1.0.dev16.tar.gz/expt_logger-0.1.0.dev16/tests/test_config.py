"""Tests for Config class."""

import threading
from queue import Queue

import pytest

from expt_logger.config import Config


@pytest.fixture
def config():
    """Create a Config without queue."""
    return Config()


@pytest.fixture
def config_with_queue():
    """Create a Config with command queue."""
    queue = Queue()
    return Config(queue=queue), queue


def test_config_initialization_empty(config):
    """Test config starts empty."""
    assert config.to_dict() == {}


def test_config_initialization_with_data():
    """Test config initialization with data."""
    config = Config(initial_data={"lr": 0.001, "batch_size": 32})
    assert config.to_dict() == {"lr": 0.001, "batch_size": 32}


def test_attribute_access_get(config):
    """Test getting value via attribute access."""
    config._data["lr"] = 0.001

    assert config.lr == 0.001


def test_attribute_access_set(config):
    """Test setting value via attribute access."""
    config.lr = 0.001

    assert config._data["lr"] == 0.001
    assert config.lr == 0.001


def test_attribute_access_missing_key(config):
    """Test attribute access with missing key raises AttributeError."""
    with pytest.raises(AttributeError) as exc_info:
        _ = config.missing_key

    assert "Configuration has no key 'missing_key'" in str(exc_info.value)


def test_dict_access_get(config):
    """Test getting value via dict access."""
    config._data["lr"] = 0.001

    assert config["lr"] == 0.001


def test_dict_access_set(config):
    """Test setting value via dict access."""
    config["lr"] = 0.001

    assert config._data["lr"] == 0.001
    assert config["lr"] == 0.001


def test_dict_access_missing_key(config):
    """Test dict access with missing key raises KeyError."""
    with pytest.raises(KeyError):
        _ = config["missing_key"]


def test_contains(config):
    """Test __contains__ method."""
    assert "lr" not in config

    config["lr"] = 0.001
    assert "lr" in config


def test_get_with_default(config):
    """Test get method with default value."""
    assert config.get("missing", 999) == 999
    assert config.get("missing") is None

    config["lr"] = 0.001
    assert config.get("lr", 999) == 0.001


def test_update_method(config):
    """Test bulk update method."""
    config.update({"lr": 0.001, "batch_size": 32})

    assert config["lr"] == 0.001
    assert config["batch_size"] == 32


def test_to_dict_returns_copy(config):
    """Test that to_dict returns a copy."""
    config["lr"] = 0.001

    data = config.to_dict()
    data["modified"] = 999

    # Original should not be modified
    assert "modified" not in config


def test_queue_command_on_setattr(config_with_queue):
    """Test that attribute write enqueues sync command."""
    config, queue = config_with_queue

    config.lr = 0.001

    # Should have enqueued a command
    assert not queue.empty()
    cmd, payload = queue.get()
    assert cmd == "config_update"
    assert payload == {"updates": {"lr": 0.001}}


def test_queue_command_on_setitem(config_with_queue):
    """Test that dict write enqueues sync command."""
    config, queue = config_with_queue

    config["lr"] = 0.001

    # Should have enqueued a command
    assert not queue.empty()
    cmd, payload = queue.get()
    assert cmd == "config_update"
    assert payload == {"updates": {"lr": 0.001}}


def test_queue_command_on_update(config_with_queue):
    """Test that bulk update enqueues sync command."""
    config, queue = config_with_queue

    config.update({"lr": 0.001, "batch_size": 32})

    # Should have enqueued a command
    assert not queue.empty()
    cmd, payload = queue.get()
    assert cmd == "config_update"
    assert payload == {"updates": {"lr": 0.001, "batch_size": 32}}


def test_no_queue_command_without_queue(config):
    """Test that no command is enqueued when queue is None."""
    # Should not raise any errors
    config.lr = 0.001
    config["batch_size"] = 32
    config.update({"epochs": 10})

    # Just verify it worked
    assert config["lr"] == 0.001
    assert config["batch_size"] == 32
    assert config["epochs"] == 10


def test_json_serializable_validation_success(config):
    """Test that JSON-serializable values are accepted."""
    # These should all succeed
    config["int_value"] = 42
    config["float_value"] = 3.14
    config["string_value"] = "test"
    config["bool_value"] = True
    config["none_value"] = None
    config["list_value"] = [1, 2, 3]
    config["dict_value"] = {"nested": "data"}

    assert config["int_value"] == 42


def test_json_serializable_validation_failure_setattr(config):
    """Test that non-JSON-serializable values are rejected via setattr."""

    class NonSerializable:
        pass

    with pytest.raises(ValueError) as exc_info:
        config.obj = NonSerializable()

    assert "JSON serializable" in str(exc_info.value)


def test_json_serializable_validation_failure_setitem(config):
    """Test that non-JSON-serializable values are rejected via setitem."""

    class NonSerializable:
        pass

    with pytest.raises(ValueError) as exc_info:
        config["obj"] = NonSerializable()

    assert "JSON serializable" in str(exc_info.value)


def test_json_serializable_validation_failure_update(config):
    """Test that non-JSON-serializable values are rejected via update."""

    class NonSerializable:
        pass

    with pytest.raises(ValueError) as exc_info:
        config.update({"obj": NonSerializable()})

    assert "JSON serializable" in str(exc_info.value)


def test_json_serializable_validation_failure_init():
    """Test that non-JSON-serializable initial data is rejected."""

    class NonSerializable:
        pass

    with pytest.raises(ValueError) as exc_info:
        Config(initial_data={"obj": NonSerializable()})

    assert "JSON serializable" in str(exc_info.value)


def test_thread_safety_concurrent_reads(config):
    """Test concurrent reads are thread-safe."""
    config.update({"lr": 0.001, "batch_size": 32, "epochs": 10})

    results = []
    errors = []

    def read_config():
        try:
            for _ in range(100):
                _ = config["lr"]
                _ = config["batch_size"]
                _ = config.to_dict()
            results.append("success")
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=read_config) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 10
    assert len(errors) == 0


def test_thread_safety_concurrent_writes(config_with_queue):
    """Test concurrent writes are thread-safe."""
    config, queue = config_with_queue

    errors = []

    def write_config(thread_id):
        try:
            for i in range(50):
                config[f"key_{thread_id}"] = i
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=write_config, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should have no errors
    assert len(errors) == 0

    # Should have 10 keys with final values
    data = config.to_dict()
    assert len(data) == 10
    for i in range(10):
        assert f"key_{i}" in data
        assert data[f"key_{i}"] == 49  # Last write


def test_thread_safety_mixed_operations(config_with_queue):
    """Test mixed read/write operations are thread-safe."""
    config, queue = config_with_queue
    config.update({"counter": 0})

    errors = []

    def reader():
        try:
            for _ in range(100):
                _ = config.get("counter", 0)
                _ = config.to_dict()
        except Exception as e:
            errors.append(e)

    def writer(value):
        try:
            for _ in range(50):
                config["counter"] = value
        except Exception as e:
            errors.append(e)

    threads = []
    threads.extend([threading.Thread(target=reader) for _ in range(5)])
    threads.extend([threading.Thread(target=writer, args=(i,)) for i in range(5)])

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


def test_repr(config):
    """Test string representation."""
    config.update({"lr": 0.001, "batch_size": 32})
    repr_str = repr(config)

    assert "Config(" in repr_str
    assert "lr" in repr_str
    assert "0.001" in repr_str


def test_internal_attributes_bypass_config():
    """Test that internal attributes don't go through config storage."""
    config = Config()

    # Should not be stored in config data
    assert "_data" not in config._data
    assert "_queue" not in config._data
    assert "_lock" not in config._data

    # Should raise AttributeError for missing internal attributes
    with pytest.raises(AttributeError):
        _ = config._missing_internal

"""Tests for MetricsBuffer."""

import logging

import pytest

from expt_logger.buffer import Buffer


@pytest.fixture
def buffer():
    """Create a fresh MetricsBuffer."""
    return Buffer()


def test_buffer_initialization(buffer):
    """Test buffer starts empty."""
    assert buffer.is_empty()
    scalars, rollouts = buffer.get_and_clear()
    assert scalars == []
    assert rollouts == []


def test_add_scalar_simple(buffer):
    """Test adding a simple scalar metric."""
    buffer.add_scalar("loss", 0.5)

    scalars, rollouts = buffer.get_and_clear()
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "train", "name": "loss", "value": 0.5}
    assert rollouts == []


def test_add_scalar_with_mode_in_key(buffer):
    """Test adding scalar with mode already in key."""
    buffer.add_scalar("train/loss", 0.5)

    scalars, rollouts = buffer.get_and_clear()
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "train", "name": "loss", "value": 0.5}


def test_add_scalar_with_mode_parameter(buffer):
    """Test adding scalar with explicit mode parameter."""
    buffer.add_scalar("loss", 0.5, mode="eval")

    scalars, rollouts = buffer.get_and_clear()
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "eval", "name": "loss", "value": 0.5}


def test_add_scalar_mode_conflict_key_wins(buffer, caplog):
    """Test that provided mode takes precedence, but keeps full key as name when modes differ."""
    with caplog.at_level(logging.WARNING):
        buffer.add_scalar("train/loss", 0.5, mode="eval")

    # Should use "eval" mode from parameter, with full "train/loss" as the name
    scalars, _ = buffer.get_and_clear()
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "eval", "name": "train/loss", "value": 0.5}

    # Should NOT log warning about conflict anymore
    assert "Mode conflict" not in caplog.text


def test_add_scalar_mode_no_conflict(buffer, caplog):
    """Test that matching modes don't cause warning."""
    with caplog.at_level(logging.WARNING):
        buffer.add_scalar("train/loss", 0.5, mode="train")

    scalars, _ = buffer.get_and_clear()
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "train", "name": "loss", "value": 0.5}

    # Should NOT log warning
    assert "Mode conflict" not in caplog.text


def test_add_multiple_scalars(buffer):
    """Test adding multiple different scalars."""
    buffer.add_scalar("loss", 0.5)
    buffer.add_scalar("accuracy", 0.9)
    buffer.add_scalar("eval/loss", 0.6)

    scalars, _ = buffer.get_and_clear()
    assert len(scalars) == 3
    # Convert to dict for easier comparison
    scalars_dict = {f"{s['mode']}/{s['name']}": s["value"] for s in scalars}
    assert scalars_dict == {
        "train/loss": 0.5,
        "train/accuracy": 0.9,
        "eval/loss": 0.6,
    }


def test_add_scalar_last_write_wins(buffer, caplog):
    """Test that last write wins for duplicate keys."""
    with caplog.at_level(logging.WARNING):
        buffer.add_scalar("loss", 0.5)
        buffer.add_scalar("loss", 0.3)  # Overwrites

    scalars, _ = buffer.get_and_clear()
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "train", "name": "loss", "value": 0.3}

    # Should log warning about overwrite
    assert "Overwriting" in caplog.text
    assert "train/loss" in caplog.text
    assert "0.5" in caplog.text  # old value
    assert "0.3" in caplog.text  # new value


def test_add_scalar_last_write_wins_different_modes(buffer):
    """Test that different modes are treated as different keys."""
    buffer.add_scalar("loss", 0.5, mode="train")
    buffer.add_scalar("loss", 0.6, mode="eval")

    scalars, _ = buffer.get_and_clear()
    assert len(scalars) == 2
    # Convert to dict for easier comparison
    scalars_dict = {f"{s['mode']}/{s['name']}": s["value"] for s in scalars}
    assert scalars_dict == {
        "train/loss": 0.5,
        "eval/loss": 0.6,
    }


def test_add_rollout(buffer):
    """Test adding a rollout."""
    rollout = {
        "step": 1,
        "mode": "train",
        "promptText": "What is 2+2?",
        "messages": [{"role": "assistant", "content": "4"}],
        "rewards": [{"name": "correctness", "value": 1.0}],
    }

    buffer.add_rollout(rollout)

    scalars, rollouts = buffer.get_and_clear()
    assert scalars == []
    assert len(rollouts) == 1
    assert rollouts[0] == rollout


def test_add_multiple_rollouts(buffer):
    """Test adding multiple rollouts."""
    rollout1 = {
        "step": 1,
        "mode": "train",
        "promptText": "Test 1",
        "messages": [{"role": "assistant", "content": "Response 1"}],
        "rewards": [{"name": "quality", "value": 0.8}],
    }
    rollout2 = {
        "step": 1,
        "mode": "train",
        "promptText": "Test 2",
        "messages": [{"role": "assistant", "content": "Response 2"}],
        "rewards": [{"name": "quality", "value": 0.9}],
    }

    buffer.add_rollout(rollout1)
    buffer.add_rollout(rollout2)

    _, rollouts = buffer.get_and_clear()
    assert len(rollouts) == 2
    assert rollouts[0] == rollout1
    assert rollouts[1] == rollout2


def test_mixed_scalars_and_rollouts(buffer):
    """Test adding both scalars and rollouts."""
    buffer.add_scalar("loss", 0.5)
    buffer.add_rollout(
        {
            "step": 1,
            "mode": "train",
            "promptText": "Test",
            "messages": [{"role": "assistant", "content": "Response"}],
            "rewards": [{"name": "quality", "value": 0.8}],
        }
    )
    buffer.add_scalar("accuracy", 0.9)

    scalars, rollouts = buffer.get_and_clear()
    assert len(scalars) == 2
    scalars_dict = {f"{s['mode']}/{s['name']}": s["value"] for s in scalars}
    assert scalars_dict == {"train/loss": 0.5, "train/accuracy": 0.9}
    assert len(rollouts) == 1


def test_get_and_clear_empties_buffer(buffer):
    """Test that get_and_clear empties the buffer."""
    buffer.add_scalar("loss", 0.5)
    buffer.add_rollout(
        {
            "step": 1,
            "mode": "train",
            "promptText": "Test",
            "messages": [{"role": "assistant", "content": "Response"}],
            "rewards": [{"name": "quality", "value": 0.8}],
        }
    )

    assert not buffer.is_empty()

    # First call returns data
    scalars1, rollouts1 = buffer.get_and_clear()
    assert len(scalars1) > 0
    assert len(rollouts1) > 0

    # Buffer should now be empty
    assert buffer.is_empty()

    # Second call returns empty
    scalars2, rollouts2 = buffer.get_and_clear()
    assert scalars2 == []
    assert rollouts2 == []


def test_get_and_clear_returns_copy(buffer):
    """Test that get_and_clear returns a copy, not reference."""
    buffer.add_scalar("loss", 0.5)

    scalars1, _ = buffer.get_and_clear()
    # Modify returned list
    scalars1.append({"step": 999, "mode": "test", "name": "modified", "value": 999})

    # Add new data
    buffer.add_scalar("accuracy", 0.9)
    scalars2, _ = buffer.get_and_clear()

    # Should not contain the modification
    assert len(scalars2) == 1
    assert scalars2[0] == {"step": 0, "mode": "train", "name": "accuracy", "value": 0.9}


def test_is_empty_with_only_scalars(buffer):
    """Test is_empty with only scalars."""
    assert buffer.is_empty()

    buffer.add_scalar("loss", 0.5)
    assert not buffer.is_empty()

    buffer.get_and_clear()
    assert buffer.is_empty()


def test_is_empty_with_only_rollouts(buffer):
    """Test is_empty with only rollouts."""
    assert buffer.is_empty()

    buffer.add_rollout(
        {
            "step": 1,
            "mode": "train",
            "promptText": "Test",
            "messages": [{"role": "assistant", "content": "Response"}],
            "rewards": [{"name": "quality", "value": 0.8}],
        }
    )
    assert not buffer.is_empty()

    buffer.get_and_clear()
    assert buffer.is_empty()


def test_metric_key_with_multiple_slashes(buffer):
    """Test metric key with multiple slashes (use first as separator)."""
    # Edge case: what if key has multiple slashes?
    buffer.add_scalar("train/sub/metric", 0.5)

    scalars, _ = buffer.get_and_clear()
    # Should split on first slash only
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "train", "name": "sub/metric", "value": 0.5}


def test_default_mode_is_train(buffer):
    """Test that default mode is 'train' when not specified."""
    buffer.add_scalar("loss", 0.5)
    buffer.add_scalar("accuracy", 0.9)

    scalars, _ = buffer.get_and_clear()
    assert all(s["mode"] == "train" for s in scalars)


def test_mode_provided_strips_matching_prefix(buffer):
    """Test that when mode is provided and matches key prefix, the prefix is stripped."""
    buffer.add_scalar("train/loss", 0.5, mode="train")

    scalars, _ = buffer.get_and_clear()
    # Should be train/loss (prefix stripped)
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "train", "name": "loss", "value": 0.5}


def test_mode_provided_keeps_mismatched_prefix(buffer):
    """Test that when mode is provided and doesn't match key prefix, full key is kept."""
    buffer.add_scalar("train/loss", 0.5, mode="eval")

    scalars, _ = buffer.get_and_clear()
    # Should be eval/train/loss (full key kept as name)
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "eval", "name": "train/loss", "value": 0.5}


def test_mode_not_provided_extracts_from_key(buffer):
    """Test that when mode is not provided, it's extracted from key prefix."""
    buffer.add_scalar("eval/accuracy", 0.95)

    scalars, _ = buffer.get_and_clear()
    # Should be eval/accuracy (mode extracted, name is accuracy)
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "eval", "name": "accuracy", "value": 0.95}


def test_mode_not_provided_simple_key_defaults_train(buffer):
    """Test that simple keys without mode default to train mode."""
    buffer.add_scalar("loss", 0.5)

    scalars, _ = buffer.get_and_clear()
    # Should be train/loss (default mode)
    assert len(scalars) == 1
    assert scalars[0] == {"step": 0, "mode": "train", "name": "loss", "value": 0.5}

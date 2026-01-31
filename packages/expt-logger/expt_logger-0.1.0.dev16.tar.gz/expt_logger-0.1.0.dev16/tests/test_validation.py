"""Tests for input validation functions."""

import math

import pytest

from expt_logger.exceptions import ValidationError
from expt_logger.validation import (
    validate_messages,
    validate_metrics,
    validate_mode,
    validate_prompt,
    validate_rewards,
    validate_step,
)


class TestValidatePrompt:
    """Tests for validate_prompt function."""

    def test_validate_prompt_with_string(self):
        """Test validate_prompt with valid string."""
        result = validate_prompt("What is 2+2?")
        assert result == "What is 2+2?"

    def test_validate_prompt_with_dict(self):
        """Test validate_prompt with valid dict containing 'content' key."""
        result = validate_prompt({"role": "user", "content": "What is 2+2?"})
        assert result == "What is 2+2?"

    def test_validate_prompt_with_dict_content_only(self):
        """Test validate_prompt with dict containing only 'content' key."""
        result = validate_prompt({"content": "Test prompt"})
        assert result == "Test prompt"

    def test_validate_prompt_dict_missing_content(self):
        """Test validate_prompt raises error when dict missing 'content' key."""
        with pytest.raises(ValidationError) as exc_info:
            validate_prompt({"role": "user", "text": "Wrong key"})
        assert "'content'" in str(exc_info.value)
        assert "['role', 'text']" in str(exc_info.value)

    def test_validate_prompt_dict_content_not_string(self):
        """Test validate_prompt raises error when 'content' is not string."""
        with pytest.raises(ValidationError) as exc_info:
            validate_prompt({"content": 123})
        assert "must be a string" in str(exc_info.value)
        assert "int" in str(exc_info.value)

    def test_validate_prompt_invalid_type_int(self):
        """Test validate_prompt raises error for int type."""
        with pytest.raises(ValidationError) as exc_info:
            validate_prompt(123)
        assert "must be str or dict" in str(exc_info.value)
        assert "int" in str(exc_info.value)

    def test_validate_prompt_invalid_type_list(self):
        """Test validate_prompt raises error for list type."""
        with pytest.raises(ValidationError) as exc_info:
            validate_prompt(["test"])
        assert "must be str or dict" in str(exc_info.value)

    def test_validate_prompt_none(self):
        """Test validate_prompt raises error for None."""
        with pytest.raises(ValidationError) as exc_info:
            validate_prompt(None)
        assert "must be str or dict" in str(exc_info.value)


class TestValidateMessages:
    """Tests for validate_messages function."""

    def test_validate_messages_valid(self):
        """Test validate_messages with valid list of messages."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        validate_messages(messages)  # Should not raise

    def test_validate_messages_empty_list(self):
        """Test validate_messages with empty list."""
        validate_messages([])  # Should not raise

    def test_validate_messages_not_list(self):
        """Test validate_messages raises error when not a list."""
        with pytest.raises(ValidationError) as exc_info:
            validate_messages({"role": "user", "content": "test"})
        assert "must be a list" in str(exc_info.value)

    def test_validate_messages_item_not_dict(self):
        """Test validate_messages raises error when item is not dict."""
        with pytest.raises(ValidationError) as exc_info:
            validate_messages(["not a dict"])
        assert "index 0" in str(exc_info.value)
        assert "must be a dict" in str(exc_info.value)

    def test_validate_messages_missing_role(self):
        """Test validate_messages raises error when message missing 'role'."""
        with pytest.raises(ValidationError) as exc_info:
            validate_messages([{"content": "test"}])
        assert "index 0" in str(exc_info.value)
        assert "missing required key 'role'" in str(exc_info.value)

    def test_validate_messages_missing_content(self):
        """Test validate_messages raises error when message missing 'content'."""
        with pytest.raises(ValidationError) as exc_info:
            validate_messages([{"role": "user"}])
        assert "index 0" in str(exc_info.value)
        assert "missing required key 'content'" in str(exc_info.value)

    def test_validate_messages_role_not_string(self):
        """Test validate_messages raises error when 'role' is not string."""
        with pytest.raises(ValidationError) as exc_info:
            validate_messages([{"role": 123, "content": "test"}])
        assert "index 0" in str(exc_info.value)
        assert "'role'" in str(exc_info.value)
        assert "must be a string" in str(exc_info.value)

    def test_validate_messages_content_not_string(self):
        """Test validate_messages raises error when 'content' is not string."""
        with pytest.raises(ValidationError) as exc_info:
            validate_messages([{"role": "user", "content": ["list"]}])
        assert "index 0" in str(exc_info.value)
        assert "'content'" in str(exc_info.value)
        assert "must be a string" in str(exc_info.value)

    def test_validate_messages_second_message_invalid(self):
        """Test validate_messages reports correct index for second invalid message."""
        messages = [
            {"role": "user", "content": "Valid"},
            {"role": "assistant"},  # Missing content
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate_messages(messages)
        assert "index 1" in str(exc_info.value)

    def test_validate_messages_none(self):
        """Test validate_messages raises error for None."""
        with pytest.raises(ValidationError) as exc_info:
            validate_messages(None)
        assert "must be a list" in str(exc_info.value)


class TestValidateRewards:
    """Tests for validate_rewards function."""

    def test_validate_rewards_valid_floats(self):
        """Test validate_rewards with valid float values."""
        validate_rewards({"accuracy": 0.95, "loss": 0.05})

    def test_validate_rewards_valid_ints(self):
        """Test validate_rewards with valid int values."""
        validate_rewards({"correct": 1, "incorrect": 0})

    def test_validate_rewards_mixed_numeric(self):
        """Test validate_rewards with mix of int and float."""
        validate_rewards({"score": 100, "accuracy": 0.95})

    def test_validate_rewards_not_dict(self):
        """Test validate_rewards raises error when not dict."""
        with pytest.raises(ValidationError) as exc_info:
            validate_rewards([("score", 1.0)])
        assert "must be a dict" in str(exc_info.value)

    def test_validate_rewards_empty_key(self):
        """Test validate_rewards raises error for empty string key."""
        with pytest.raises(ValidationError) as exc_info:
            validate_rewards({"": 1.0})
        assert "must be a non-empty string" in str(exc_info.value)

    def test_validate_rewards_non_numeric_value(self):
        """Test validate_rewards raises error for string value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_rewards({"score": "high"})
        assert "score" in str(exc_info.value)
        assert "expected int or float" in str(exc_info.value)

    def test_validate_rewards_nan_value(self):
        """Test validate_rewards raises error for NaN value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_rewards({"score": math.nan})
        assert "score" in str(exc_info.value)
        assert "nan" in str(exc_info.value).lower()

    def test_validate_rewards_inf_value(self):
        """Test validate_rewards raises error for Inf value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_rewards({"score": math.inf})
        assert "score" in str(exc_info.value)
        assert "inf" in str(exc_info.value).lower()

    def test_validate_rewards_negative_inf_value(self):
        """Test validate_rewards raises error for -Inf value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_rewards({"score": -math.inf})
        assert "score" in str(exc_info.value)
        assert "inf" in str(exc_info.value).lower()

    def test_validate_rewards_bool_value(self):
        """Test validate_rewards raises error for boolean value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_rewards({"success": True})
        assert "success" in str(exc_info.value)
        assert "bool is not allowed" in str(exc_info.value)

    def test_validate_rewards_none(self):
        """Test validate_rewards raises error for None."""
        with pytest.raises(ValidationError) as exc_info:
            validate_rewards(None)
        assert "must be a dict" in str(exc_info.value)

    def test_validate_rewards_negative_value(self):
        """Test validate_rewards accepts negative numbers."""
        validate_rewards({"penalty": -0.5})  # Should not raise


class TestValidateMetrics:
    """Tests for validate_metrics function."""

    def test_validate_metrics_valid_floats(self):
        """Test validate_metrics with valid float values."""
        validate_metrics({"loss": 0.5, "accuracy": 0.95})

    def test_validate_metrics_valid_ints(self):
        """Test validate_metrics with valid int values."""
        validate_metrics({"epoch": 10, "batch": 5})

    def test_validate_metrics_mixed_numeric(self):
        """Test validate_metrics with mix of int and float."""
        validate_metrics({"loss": 0.5, "epoch": 10})

    def test_validate_metrics_not_dict(self):
        """Test validate_metrics raises error when not dict."""
        with pytest.raises(ValidationError) as exc_info:
            validate_metrics([("loss", 0.5)])
        assert "must be a dict" in str(exc_info.value)

    def test_validate_metrics_empty_key(self):
        """Test validate_metrics raises error for empty string key."""
        with pytest.raises(ValidationError) as exc_info:
            validate_metrics({"": 1.0})
        assert "must be a non-empty string" in str(exc_info.value)

    def test_validate_metrics_non_numeric_value(self):
        """Test validate_metrics raises error for string value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_metrics({"status": "good"})
        assert "status" in str(exc_info.value)
        assert "expected int or float" in str(exc_info.value)

    def test_validate_metrics_nan_value(self):
        """Test validate_metrics raises error for NaN value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_metrics({"loss": math.nan})
        assert "loss" in str(exc_info.value)
        assert "nan" in str(exc_info.value).lower()

    def test_validate_metrics_inf_value(self):
        """Test validate_metrics raises error for Inf value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_metrics({"loss": math.inf})
        assert "loss" in str(exc_info.value)
        assert "inf" in str(exc_info.value).lower()

    def test_validate_metrics_bool_value(self):
        """Test validate_metrics raises error for boolean value."""
        with pytest.raises(ValidationError) as exc_info:
            validate_metrics({"converged": False})
        assert "converged" in str(exc_info.value)
        assert "bool is not allowed" in str(exc_info.value)

    def test_validate_metrics_none(self):
        """Test validate_metrics raises error for None."""
        with pytest.raises(ValidationError) as exc_info:
            validate_metrics(None)
        assert "must be a dict" in str(exc_info.value)


class TestValidateStep:
    """Tests for validate_step function."""

    def test_validate_step_valid_positive(self):
        """Test validate_step with positive integer."""
        validate_step(10)  # Should not raise

    def test_validate_step_valid_zero(self):
        """Test validate_step with zero."""
        validate_step(0)  # Should not raise

    def test_validate_step_none(self):
        """Test validate_step with None."""
        validate_step(None)  # Should not raise

    def test_validate_step_negative(self):
        """Test validate_step raises error for negative integer."""
        with pytest.raises(ValidationError) as exc_info:
            validate_step(-5)
        assert "non-negative" in str(exc_info.value)
        assert "-5" in str(exc_info.value)

    def test_validate_step_float(self):
        """Test validate_step raises error for float."""
        with pytest.raises(ValidationError) as exc_info:
            validate_step(5.5)
        assert "must be an integer" in str(exc_info.value)

    def test_validate_step_string(self):
        """Test validate_step raises error for string."""
        with pytest.raises(ValidationError) as exc_info:
            validate_step("10")
        assert "must be an integer" in str(exc_info.value)

    def test_validate_step_bool(self):
        """Test validate_step raises error for boolean."""
        with pytest.raises(ValidationError) as exc_info:
            validate_step(True)
        assert "must be an integer" in str(exc_info.value)


class TestValidateMode:
    """Tests for validate_mode function."""

    def test_validate_mode_valid(self):
        """Test validate_mode with valid string."""
        validate_mode("train")  # Should not raise
        validate_mode("eval")  # Should not raise

    def test_validate_mode_none(self):
        """Test validate_mode with None."""
        validate_mode(None)  # Should not raise

    def test_validate_mode_empty_string(self):
        """Test validate_mode raises error for empty string."""
        with pytest.raises(ValidationError) as exc_info:
            validate_mode("")
        assert "non-empty string" in str(exc_info.value)

    def test_validate_mode_not_string(self):
        """Test validate_mode raises error for non-string."""
        with pytest.raises(ValidationError) as exc_info:
            validate_mode(123)
        assert "must be a string" in str(exc_info.value)

"""Input validation functions for expt-logger."""

import math
from typing import Any

from expt_logger.exceptions import ValidationError


def _is_numeric(value: Any) -> bool:
    """Check if value is numeric (int/float) and not NaN/Inf.

    Args:
        value: Value to check

    Returns:
        True if value is a valid numeric type (int or float, not NaN/Inf), False otherwise
    """
    # Exclude booleans (bool is subclass of int in Python)
    if isinstance(value, bool):
        return False

    # Check if it's int or float
    if not isinstance(value, (int | float)):
        return False

    # For floats, check for NaN and Inf
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return False

    return True


def validate_prompt(prompt: str | dict[str, str]) -> str:
    """Validate and normalize prompt parameter.

    Args:
        prompt: Prompt text (str) or dict with 'content' key

    Returns:
        Normalized prompt text as string

    Raises:
        ValidationError: If prompt is invalid
    """
    if isinstance(prompt, str):
        return prompt

    if isinstance(prompt, dict):
        if "content" not in prompt:
            raise ValidationError(
                f"Prompt dict must have 'content' key. Got dict with keys: {list(prompt.keys())}"
            )

        content = prompt["content"]
        if not isinstance(content, str):
            raise ValidationError(
                f"Prompt dict 'content' value must be a string, got {type(content).__name__}"
            )

        return content

    raise ValidationError(
        f"Prompt must be str or dict with 'content' key, got {type(prompt).__name__}"
    )


def validate_messages(messages: list[dict[str, str]]) -> None:
    """Validate messages list structure.

    Args:
        messages: List of message dicts with 'role' and 'content' keys

    Raises:
        ValidationError: If messages structure is invalid
    """
    if not isinstance(messages, list):
        raise ValidationError(f"Messages must be a list, got {type(messages).__name__}")

    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            raise ValidationError(f"Message at index {i} must be a dict, got {type(msg).__name__}")

        # Check for required keys
        if "role" not in msg:
            raise ValidationError(f"Message at index {i} is missing required key 'role'")

        if "content" not in msg:
            raise ValidationError(f"Message at index {i} is missing required key 'content'")

        # Check that values are strings
        if not isinstance(msg["role"], str):
            raise ValidationError(
                f"Message at index {i} has invalid 'role': must be a string, "
                f"got {type(msg['role']).__name__}"
            )

        if not isinstance(msg["content"], str):
            raise ValidationError(
                f"Message at index {i} has invalid 'content': must be a string, "
                f"got {type(msg['content']).__name__}"
            )


def validate_rewards(rewards: dict[str, float]) -> None:
    """Validate rewards dict.

    Args:
        rewards: Dict of reward names to numeric values

    Raises:
        ValidationError: If rewards structure or values are invalid
    """
    if not isinstance(rewards, dict):
        raise ValidationError(f"Rewards must be a dict, got {type(rewards).__name__}")

    for name, value in rewards.items():
        # Validate key is non-empty string
        if not isinstance(name, str) or not name:
            raise ValidationError(f"Reward name must be a non-empty string, got {repr(name)}")

        # Validate value is numeric
        if not _is_numeric(value):
            if isinstance(value, bool):
                raise ValidationError(
                    f"Reward '{name}' has invalid value: {value} (bool is not allowed, use 1 or 0)"
                )
            elif isinstance(value, float) and math.isnan(value):
                raise ValidationError(
                    f"Reward '{name}' has invalid value: nan (NaN is not allowed)"
                )
            elif isinstance(value, float) and math.isinf(value):
                raise ValidationError(
                    f"Reward '{name}' has invalid value: {'inf' if value > 0 else '-inf'} "
                    "(Infinity is not allowed)"
                )
            else:
                raise ValidationError(
                    f"Reward '{name}' has invalid value: {repr(value)} "
                    f"(expected int or float, got {type(value).__name__})"
                )


def validate_metrics(metrics: dict[str, float]) -> None:
    """Validate metrics dict.

    Args:
        metrics: Dict of metric names to numeric values

    Raises:
        ValidationError: If metrics structure or values are invalid
    """
    if not isinstance(metrics, dict):
        raise ValidationError(f"Metrics must be a dict, got {type(metrics).__name__}")

    for name, value in metrics.items():
        # Validate key is non-empty string
        if not isinstance(name, str) or not name:
            raise ValidationError(f"Metric name must be a non-empty string, got {repr(name)}")

        # Validate value is numeric
        if not _is_numeric(value):
            if isinstance(value, bool):
                raise ValidationError(
                    f"Metric '{name}' has invalid value: {value} (bool is not allowed, use 1 or 0)"
                )
            elif isinstance(value, float) and math.isnan(value):
                raise ValidationError(
                    f"Metric '{name}' has invalid value: nan (NaN is not allowed)"
                )
            elif isinstance(value, float) and math.isinf(value):
                raise ValidationError(
                    f"Metric '{name}' has invalid value: {'inf' if value > 0 else '-inf'} "
                    "(Infinity is not allowed)"
                )
            else:
                raise ValidationError(
                    f"Metric '{name}' has invalid value: {repr(value)} "
                    f"(expected int or float, got {type(value).__name__})"
                )


def validate_step(step: int | None) -> None:
    """Validate step parameter.

    Args:
        step: Optional step number

    Raises:
        ValidationError: If step is invalid
    """
    if step is None:
        return

    if not isinstance(step, int) or isinstance(step, bool):
        raise ValidationError(f"Step must be an integer, got {type(step).__name__}")

    if step < 0:
        raise ValidationError(f"Step must be non-negative, got {step}")


def validate_mode(mode: str | None) -> None:
    """Validate mode parameter.

    Args:
        mode: Optional mode string

    Raises:
        ValidationError: If mode is invalid
    """
    if mode is None:
        return

    if not isinstance(mode, str):
        raise ValidationError(f"Mode must be a string, got {type(mode).__name__}")

    if not mode:
        raise ValidationError("Mode must be a non-empty string")

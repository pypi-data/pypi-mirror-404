"""Type definitions for expt-logger."""

from typing import Any, TypedDict


class ScalarItem(TypedDict):
    """A single scalar metric value."""

    name: str
    value: float
    step: int
    mode: str


class RewardItem(TypedDict):
    """A reward item with name and value."""

    name: str
    value: float


class MessageItem(TypedDict):
    """A message in a conversation."""

    role: str
    content: str


class RolloutItem(TypedDict):
    """A rollout item for API submission."""

    step: int
    mode: str
    promptText: str
    messages: list[MessageItem]
    rewards: list[RewardItem]


class ScalarValue(TypedDict):
    """A single scalar value at a specific step (used in GET responses)."""

    step: int
    value: float


# Queue command types for type-safe command passing


class LogCommand(TypedDict):
    """Command to log a scalar metric."""

    name: str
    value: float
    mode: str | None
    step: int | None


class LogRolloutCommand(TypedDict):
    """Command to log a rollout."""

    prompt: str
    messages: list[MessageItem]
    rewards: list[RewardItem]
    mode: str
    step: int | None


class CommitCommand(TypedDict):
    """Command to commit (flush) the buffer."""

    pass


class ConfigUpdateCommand(TypedDict):
    """Command to update configuration."""

    updates: dict[str, Any]


class ShutdownCommand(TypedDict):
    """Command to shut down the worker."""

    pass


# Union type for all queue commands
QueueCommand = (
    tuple[str, LogCommand]
    | tuple[str, LogRolloutCommand]
    | tuple[str, CommitCommand]
    | tuple[str, ConfigUpdateCommand]
    | tuple[str, ShutdownCommand]
)

"""Message types."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class Message:
    """Base message class."""

    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class UserMessage(Message):
    """User input message."""

    text: str = ""
    images: list[str] | None = None


@dataclass
class SystemMessage(Message):
    """System message."""

    text: str = ""


@dataclass
class TextMessage(Message):
    """Text output message."""

    text: str = ""


@dataclass
class DeltaMessage(Message):
    """Streaming delta message."""

    text: str = ""
    parent_id: str = ""


@dataclass
class ThinkingMessage(Message):
    """Agent thinking message."""

    text: str = ""


@dataclass
class ToolUseMessage(Message):
    """Tool invocation message."""

    tool: str = ""
    input: dict = field(default_factory=dict)


@dataclass
class ToolResultMessage(Message):
    """Tool result message."""

    tool: str = ""
    output: Any = None
    is_error: bool = False


@dataclass
class ErrorMessage(Message):
    """Error message."""

    code: str = ""
    message: str = ""


@dataclass
class DoneMessage(Message):
    """Completion message."""

    usage: dict | None = None

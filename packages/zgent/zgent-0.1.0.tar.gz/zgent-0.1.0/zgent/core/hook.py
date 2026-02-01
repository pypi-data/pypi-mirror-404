"""Hook system."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .agent import Agent
    from .message import Message
    from .tool import Tool


@dataclass
class HookContext:
    """Context passed to hooks."""

    tool: "Tool"
    agent: "Agent"
    message: "Message"


@dataclass
class HookResult:
    """Result returned from hooks."""

    action: Literal["continue", "deny", "modify"] = "continue"
    reason: str | None = None
    modified_input: dict | None = None
    modified_output: Any | None = None


class Hook:
    """Base hook class."""

    async def on_before(self, input: dict, ctx: HookContext) -> HookResult:
        """Called before tool execution."""
        return HookResult(action="continue")

    async def on_after(
        self, input: dict, output: Any, ctx: HookContext
    ) -> HookResult:
        """Called after tool execution."""
        return HookResult(action="continue")

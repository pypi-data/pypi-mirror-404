"""Context classes."""

from typing import TYPE_CHECKING, Any

from .message import Message

if TYPE_CHECKING:
    from .agent import Agent
    from .tool import Tool


class Context:
    """Context for message handlers."""

    def __init__(self, message: Message, agent: "Agent"):
        self.message = message
        self.agent = agent

    async def publish(self, message: Message) -> None:
        """Publish a message to the agent's output channel."""
        await self.agent._publish(message)


class ToolContext:
    """Context for tool execution."""

    def __init__(self, tool: "Tool", agent: "Agent", message: Message):
        self.tool = tool
        self.agent = agent
        self.message = message

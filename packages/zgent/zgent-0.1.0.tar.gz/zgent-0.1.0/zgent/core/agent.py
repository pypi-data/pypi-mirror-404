"""Agent class."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Awaitable, Callable, Self

from .context import Context
from .message import Message
from .tool import Tool

if TYPE_CHECKING:
    from .client import Client

MessageHandler = Callable[[Message, Context], Awaitable[None]]
OutputHandler = Callable[[Message], Awaitable[None]]
ErrorHandler = Callable[[Exception, Context], Awaitable[None]]


@dataclass
class AgentOptions:
    """Agent configuration options."""

    name: str
    model: str
    system_prompt: str | None = None


class Agent:
    """Agent class."""

    def __init__(self, client: "Client", options: AgentOptions):
        self._client = client
        self._options = options
        self._tools: list[Tool] = []
        self._subscriptions: list[str] = []
        self._message_handler: MessageHandler | None = None
        self._output_handler: OutputHandler | None = None
        self._error_handler: ErrorHandler | None = None
        self._running = False

    @property
    def name(self) -> str:
        return self._options.name

    @property
    def model(self) -> str:
        return self._options.model

    def add_tool(self, tool: Tool) -> Self:
        """Add a tool to this agent."""
        self._tools.append(tool)
        return self

    def subscribe(self, channel_name: str) -> Self:
        """Subscribe to a channel."""
        self._subscriptions.append(channel_name)
        return self

    def on_message(self, handler: MessageHandler) -> Self:
        """Register message handler."""
        self._message_handler = handler
        return self

    def on_output(self, handler: OutputHandler) -> Self:
        """Register output handler."""
        self._output_handler = handler
        return self

    def on_error(self, handler: ErrorHandler) -> Self:
        """Register error handler."""
        self._error_handler = handler
        return self

    def start(self) -> None:
        """Start the agent."""
        self._running = True

    def stop(self) -> None:
        """Stop the agent."""
        self._running = False

    async def _publish(self, message: Message) -> None:
        """Internal: publish message to output channel."""
        if self._output_handler:
            await self._output_handler(message)

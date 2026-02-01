"""Channel protocol."""

from typing import Protocol

from .message import Message


class Channel(Protocol):
    """Channel protocol for message transport."""

    async def receive(self) -> Message:
        """Receive a message from the channel."""
        ...

    async def send(self, message: Message) -> None:
        """Send a message to the channel."""
        ...

"""Tool system."""

from typing import TYPE_CHECKING, Any, Self

from .hook import Hook

if TYPE_CHECKING:
    from .context import ToolContext


class Tool:
    """Base tool class."""

    name: str = ""
    description: str = ""

    def __init__(self, name: str = "", description: str = ""):
        self.name = name or self.__class__.__name__
        self.description = description
        self._hooks: list[Hook] = []

    def add_hook(self, hook: Hook) -> Self:
        """Add a hook to this tool."""
        self._hooks.append(hook)
        return self

    async def execute(self, input: dict, ctx: "ToolContext") -> Any:
        """Execute the tool. Override in subclasses."""
        raise NotImplementedError

"""Client class."""

from .agent import Agent, AgentOptions
from .channel import Channel


class Client:
    """SDK Client."""

    def __init__(self, api_key: str, base_url: str | None = None):
        self._api_key = api_key
        self._base_url = base_url
        self._channels: dict[str, Channel] = {}
        self._agents: list[Agent] = []

    def register_channel(self, name: str, channel: Channel) -> None:
        """Register a channel."""
        self._channels[name] = channel

    def new_agent(self, options: AgentOptions) -> Agent:
        """Create a new agent."""
        agent = Agent(self, options)
        self._agents.append(agent)
        return agent

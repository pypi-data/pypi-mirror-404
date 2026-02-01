# Zen Agent SDK

A Python SDK for building AI agents.

## Installation

```bash
pip install zgent
```

## Quick Start

```python
from zgent import Client, AgentOptions, TextMessage

client = Client(api_key="xxx")

agent = client.new_agent(AgentOptions(
    name="worker",
    model="claude-sonnet",
))

@agent.on_message
async def handle(message, ctx):
    await ctx.publish(TextMessage(text="Hello!"))

agent.start()
```

## License

Apache-2.0

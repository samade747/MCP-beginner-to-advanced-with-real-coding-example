# 🌤️ Weather Agent — MCP Project 1

A complete, production-ready weather MCP server.

## What It Does

| Tool | Description |
|------|-------------|
| `get_weather` | Current conditions for any city |
| `get_detailed_weather` | Full stats: humidity, UV, wind |
| `compare_cities` | Side-by-side weather for multiple cities |
| `get_clothing_suggestion` | What to wear based on conditions |
| `check_travel_weather` | Compare origin vs destination |

## Setup

```bash
# No API key needed — uses free wttr.in service!
pip install mcp httpx
python weather_agent.py
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/path/to/weather_agent.py"]
    }
  }
}
```

## Try These Prompts

- *"What's the weather in Karachi?"*
- *"Compare weather in London, Paris, Tokyo, and Dubai"*
- *"What should I wear in New York today?"*
- *"I'm traveling from Karachi to London — what should I pack?"*
- *"Is it a good weekend for outdoor activities in Sydney?"*

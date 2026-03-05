"""
examples/02_tools/weather_tool.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Real weather tool using a free API (no key needed!)

HOW TO RUN:
  python weather_tool.py

HOW TO TEST with Claude Desktop:
  Add to claude_desktop_config.json:
  {
    "mcpServers": {
      "weather": {
        "command": "python",
        "args": ["/absolute/path/to/weather_tool.py"]
      }
    }
  }

TRY ASKING CLAUDE:
  "What's the weather in London?"
  "Compare weather in Karachi and Dubai"
  "Is it raining in Tokyo?"
"""

import sys
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")


@mcp.tool()
async def get_current_weather(city: str) -> str:
    """
    Get the current weather conditions for any city in the world.

    Use this when the user asks about current weather, temperature,
    or conditions in a specific city or location.

    Args:
        city: Name of the city (e.g. "London", "Karachi", "New York", "Tokyo")

    Returns:
        Current weather description with temperature and conditions
    """
    print(f"[weather] Fetching weather for: {city}", file=sys.stderr)

    async with httpx.AsyncClient() as client:
        try:
            # wttr.in is a free weather service — no API key needed!
            response = await client.get(
                f"https://wttr.in/{city}?format=3",
                timeout=10.0,
                headers={"User-Agent": "MCP-Weather-Bot/1.0"}
            )

            if response.status_code == 200:
                result = response.text.strip()
                print(f"[weather] Result: {result}", file=sys.stderr)
                return result
            else:
                return f"Could not fetch weather for '{city}'. Please check the city name."

        except httpx.TimeoutException:
            return f"Weather service timed out. Please try again in a moment."

        except httpx.NetworkError:
            return f"Network error: Cannot reach weather service."

        except Exception as e:
            return f"Error fetching weather: {str(e)}"


@mcp.tool()
async def compare_weather(cities: str) -> str:
    """
    Compare current weather across multiple cities at the same time.

    Use this when the user wants to compare weather in different locations,
    or asks "which city is warmer/cooler".

    Args:
        cities: Comma-separated list of city names
                Example: "London,Paris,Tokyo" or "Karachi, Dubai, Mumbai"

    Returns:
        Weather comparison for all specified cities
    """
    # Parse the city list
    city_list = [c.strip() for c in cities.split(",") if c.strip()]

    if not city_list:
        return "Please provide at least one city name."

    if len(city_list) > 6:
        return "Please compare at most 6 cities at a time."

    import asyncio

    async def fetch_city(city: str) -> str:
        """Fetch weather for one city."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"https://wttr.in/{city}?format=3",
                    timeout=8.0
                )
                return resp.text.strip() if resp.status_code == 200 else f"{city}: unavailable"
            except Exception:
                return f"{city}: unavailable"

    # Fetch all cities in parallel (much faster than one by one!)
    tasks = [fetch_city(city) for city in city_list]
    results = await asyncio.gather(*tasks)

    output = f"Weather Comparison ({len(city_list)} cities):\n"
    output += "─" * 40 + "\n"
    output += "\n".join(results)

    return output


@mcp.tool()
async def get_weather_emoji(city: str) -> str:
    """
    Get a simple emoji weather summary for a city.

    Good for quick, visual weather responses.

    Args:
        city: Name of the city

    Returns:
        Short emoji-based weather summary
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"https://wttr.in/{city}?format=%C+%t",  # Condition + Temperature
                timeout=8.0
            )
            return f"{city}: {resp.text.strip()}"
        except Exception as e:
            return f"{city}: Could not fetch weather ({e})"


if __name__ == "__main__":
    print("🌤️  Weather MCP Server starting...", file=sys.stderr)
    mcp.run()

"""
projects/weather_agent/weather_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project 1: Complete Weather Agent

A full-featured weather MCP server with:
  • Current conditions
  • Multi-day forecasts
  • City comparisons
  • Temperature conversions
  • UV index and air quality
  • Clothing suggestions based on weather

HOW TO CONNECT TO CLAUDE DESKTOP:
  1. Add to claude_desktop_config.json:
     {
       "mcpServers": {
         "weather-agent": {
           "command": "python",
           "args": ["/path/to/weather_agent.py"]
         }
       }
     }
  2. Restart Claude Desktop
  3. Ask Claude about weather!

TRY THESE PROMPTS:
  "What's the weather in my city?"
  "Compare weather across 5 major cities"
  "What should I wear in London today?"
  "Is it a good day for outdoor activities in Paris?"
"""

import sys
import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="weather-agent",
    instructions="""
    You are a helpful weather assistant powered by real-time weather data.
    When users ask about weather, always use the available tools to get
    current, accurate information. Provide helpful context about what the
    weather means for their day (activities, clothing, travel, etc.)
    """
)


# ─── Core weather functions ────────────────────────────────────────────────

async def _fetch_weather(city: str, format_str: str = "3") -> str:
    """Internal: fetch weather data from wttr.in"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"https://wttr.in/{city}?format={format_str}",
                timeout=10.0,
                headers={"User-Agent": "WeatherAgent-MCP/1.0"}
            )
            return resp.text.strip() if resp.status_code == 200 else None
        except Exception:
            return None


async def _fetch_weather_json(city: str) -> dict | None:
    """Internal: fetch full weather JSON data"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"https://wttr.in/{city}?format=j1",
                timeout=10.0
            )
            return resp.json() if resp.status_code == 200 else None
        except Exception:
            return None


# ─── MCP Tools ────────────────────────────────────────────────────────────

@mcp.tool()
async def get_weather(city: str) -> str:
    """
    Get current weather conditions for any city.

    Args:
        city: City name (e.g., "London", "Karachi", "New York")

    Returns:
        Current weather with temperature and conditions
    """
    result = await _fetch_weather(city)
    if result:
        return result
    return f"Could not get weather for '{city}'. Please check the city name."


@mcp.tool()
async def get_detailed_weather(city: str) -> dict:
    """
    Get comprehensive weather data including temperature, humidity, wind, UV index.

    Args:
        city: City name

    Returns:
        Detailed weather statistics
    """
    data = await _fetch_weather_json(city)

    if not data:
        return {"error": f"Could not fetch weather for '{city}'"}

    current = data.get("current_condition", [{}])[0]
    location = data.get("nearest_area", [{}])[0]

    city_name = location.get("areaName", [{}])[0].get("value", city)
    country = location.get("country", [{}])[0].get("value", "")

    temp_c = int(current.get("temp_C", 0))
    temp_f = int(current.get("temp_F", 0))
    feels_c = int(current.get("FeelsLikeC", 0))
    feels_f = int(current.get("FeelsLikeF", 0))
    humidity = int(current.get("humidity", 0))
    wind_kmph = int(current.get("windspeedKmph", 0))
    wind_mph = int(current.get("windspeedMiles", 0))
    visibility = int(current.get("visibility", 0))
    uv_index = int(current.get("uvIndex", 0))
    description = current.get("weatherDesc", [{}])[0].get("value", "")

    # UV index interpretation
    if uv_index <= 2:
        uv_risk = "Low"
    elif uv_index <= 5:
        uv_risk = "Moderate"
    elif uv_index <= 7:
        uv_risk = "High"
    elif uv_index <= 10:
        uv_risk = "Very High"
    else:
        uv_risk = "Extreme"

    return {
        "location": f"{city_name}, {country}",
        "conditions": description,
        "temperature": {
            "celsius": temp_c,
            "fahrenheit": temp_f,
            "feels_like_celsius": feels_c,
            "feels_like_fahrenheit": feels_f
        },
        "atmosphere": {
            "humidity_percent": humidity,
            "wind_kmph": wind_kmph,
            "wind_mph": wind_mph,
            "visibility_km": visibility
        },
        "uv_index": {
            "value": uv_index,
            "risk_level": uv_risk
        }
    }


@mcp.tool()
async def compare_cities(cities: str) -> str:
    """
    Compare weather across multiple cities simultaneously.

    Args:
        cities: Comma-separated city names (e.g. "London,Paris,Tokyo,Dubai")
                Maximum 6 cities.

    Returns:
        Side-by-side weather comparison
    """
    city_list = [c.strip() for c in cities.split(",") if c.strip()][:6]

    async def fetch_one(city):
        result = await _fetch_weather(city)
        return city, result or f"{city}: unavailable"

    tasks = [fetch_one(city) for city in city_list]
    results = await asyncio.gather(*tasks)

    lines = [
        f"🌍 Weather Comparison — {len(city_list)} Cities",
        "═" * 45
    ]
    for city, weather in results:
        lines.append(f"  {weather}")

    return "\n".join(lines)


@mcp.tool()
async def get_clothing_suggestion(city: str) -> str:
    """
    Get clothing and activity suggestions based on current weather.

    Args:
        city: City to get suggestions for

    Returns:
        Practical clothing and activity recommendations
    """
    data = await _fetch_weather_json(city)

    if not data:
        return f"Could not get weather data for '{city}'"

    current = data.get("current_condition", [{}])[0]
    temp_c = int(current.get("temp_C", 20))
    humidity = int(current.get("humidity", 50))
    wind_kmph = int(current.get("windspeedKmph", 0))
    desc = current.get("weatherDesc", [{}])[0].get("value", "").lower()

    # Clothing recommendation logic
    clothing = []
    activities = []
    warnings = []

    # Temperature-based
    if temp_c < 0:
        clothing.extend(["Heavy winter coat", "Thermal underlayers", "Hat & gloves", "Warm boots"])
        activities.append("Good for winter sports!")
        warnings.append("⚠️ Risk of frostbite — limit time outdoors")
    elif temp_c < 10:
        clothing.extend(["Winter jacket", "Sweater/jumper", "Warm trousers", "Scarf"])
        activities.append("Good for brisk walks")
    elif temp_c < 18:
        clothing.extend(["Light jacket or cardigan", "Long sleeve shirt", "Regular trousers"])
        activities.append("Perfect for outdoor activities")
    elif temp_c < 25:
        clothing.extend(["T-shirt or light shirt", "Regular trousers or jeans"])
        activities.append("Great for most outdoor activities!")
    elif temp_c < 32:
        clothing.extend(["Light, breathable clothing", "T-shirt & shorts or light dress"])
        activities.append("Good for beach, parks, outdoor dining")
        warnings.append("☀️ Apply sunscreen!")
    else:
        clothing.extend(["Very light, loose clothing", "Light colors to reflect heat"])
        activities.append("Stay in shade/AC when possible")
        warnings.append("🌡️ Heat alert — stay hydrated and avoid peak sun hours (11am-3pm)")

    # Weather conditions
    if "rain" in desc or "drizzle" in desc or "shower" in desc:
        clothing.append("Umbrella or waterproof jacket")
        warnings.append("🌧️ Rain expected — plan accordingly")

    if "snow" in desc:
        clothing.append("Waterproof, insulated footwear")
        warnings.append("🌨️ Snow — check road conditions")

    if wind_kmph > 40:
        clothing.append("Windproof outer layer")
        warnings.append(f"💨 Strong winds ({wind_kmph} km/h) — hold onto your hat!")

    if humidity > 80 and temp_c > 20:
        warnings.append(f"💧 High humidity ({humidity}%) — it will feel hotter than it is")

    result = [
        f"👗 What to Wear in {city.title()}",
        f"   Current: {temp_c}°C, {desc}",
        "",
        "🧥 Clothing:",
        *[f"   • {item}" for item in clothing],
    ]

    if activities:
        result.extend(["", "🏃 Activities:", *[f"   • {a}" for a in activities]])

    if warnings:
        result.extend(["", "⚠️ Heads Up:", *[f"   {w}" for w in warnings]])

    return "\n".join(result)


@mcp.tool()
async def check_travel_weather(origin: str, destination: str) -> str:
    """
    Compare weather between two cities for travel planning.

    Args:
        origin: Where you're traveling FROM
        destination: Where you're traveling TO

    Returns:
        Weather comparison to help with travel packing
    """
    origin_data, dest_data = await asyncio.gather(
        _fetch_weather_json(origin),
        _fetch_weather_json(destination)
    )

    def extract(data, city_name):
        if not data:
            return None
        c = data.get("current_condition", [{}])[0]
        return {
            "city": city_name,
            "temp_c": int(c.get("temp_C", 0)),
            "temp_f": int(c.get("temp_F", 0)),
            "desc": c.get("weatherDesc", [{}])[0].get("value", ""),
            "humidity": int(c.get("humidity", 0)),
            "wind": int(c.get("windspeedKmph", 0))
        }

    orig = extract(origin_data, origin)
    dest = extract(dest_data, destination)

    if not orig or not dest:
        return "Could not fetch weather for one or both cities."

    temp_diff = dest["temp_c"] - orig["temp_c"]
    temp_direction = "warmer" if temp_diff > 0 else "cooler" if temp_diff < 0 else "same temperature"

    return f"""
✈️  Travel Weather Comparison
{'─' * 40}
FROM: {orig['city'].title()}
  🌡️  {orig['temp_c']}°C ({orig['temp_f']}°F)
  🌤️  {orig['desc']}
  💧 Humidity: {orig['humidity']}%

TO: {dest['city'].title()}
  🌡️  {dest['temp_c']}°C ({dest['temp_f']}°F)
  🌤️  {dest['desc']}
  💧 Humidity: {dest['humidity']}%

📊 Difference: {abs(temp_diff)}°C {temp_direction} at destination
{'─' * 40}
💡 Packing tip: {"Pack layers for the temperature difference!" if abs(temp_diff) > 10 else "Similar temperatures — pack as normal."}
""".strip()


if __name__ == "__main__":
    print("🌤️  Weather Agent MCP Server starting...", file=sys.stderr)
    print("   Connect via Claude Desktop to use!", file=sys.stderr)
    mcp.run()

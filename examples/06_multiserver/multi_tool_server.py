"""
examples/06_multiserver/multi_tool_server.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADVANCED: A single server that combines multiple tool categories.

This is a "batteries included" server that gives Claude:
  • Weather data
  • Calculator
  • File operations
  • Web fetching
  • Text processing
  • Time & date utilities

Good for: local AI assistant / Claude Desktop power user setup

ADD TO CLAUDE DESKTOP CONFIG:
{
  "mcpServers": {
    "all-in-one": {
      "command": "python",
      "args": ["/path/to/multi_tool_server.py"]
    }
  }
}
"""

import sys
import math
import httpx
from pathlib import Path
from datetime import datetime, timezone
import pytz  # pip install pytz
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="all-in-one-assistant",
    instructions="""
    You are a powerful AI assistant with access to real-time tools.
    You can:
    - Check weather for any city
    - Perform complex calculations
    - Fetch web content
    - Work with files in the workspace
    - Process and analyze text
    - Handle time zone conversions
    
    Always use tools to provide accurate, real-time information.
    """
)

WORKSPACE = Path.home() / "mcp-workspace"
WORKSPACE.mkdir(exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: WEATHER TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def weather(city: str) -> str:
    """Get current weather for any city. Use for weather/temperature questions."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"https://wttr.in/{city}?format=3", timeout=8)
            return resp.text.strip()
        except Exception as e:
            return f"Weather unavailable for {city}: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: MATH TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def calc(expression: str) -> str:
    """
    Calculate any mathematical expression.
    Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, pi, e

    Examples: "2 + 2", "sqrt(16)", "pi * 5**2", "log(100, 10)"
    """
    safe_env = {
        fn: getattr(math, fn)
        for fn in dir(math)
        if not fn.startswith("_")
    }
    safe_env.update({"abs": abs, "round": round, "__builtins__": {}})

    try:
        result = eval(expression, safe_env)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: DATE & TIME TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_current_time(timezone_name: str = "UTC") -> dict:
    """
    Get the current date and time, optionally in a specific timezone.

    Args:
        timezone_name: IANA timezone name (e.g. "UTC", "America/New_York",
                       "Asia/Karachi", "Europe/London", "Asia/Tokyo")

    Returns:
        Current date, time, and timezone information
    """
    try:
        tz = pytz.timezone(timezone_name)
        now = datetime.now(tz)
        utc_now = datetime.now(timezone.utc)

        return {
            "timezone": timezone_name,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime_formatted": now.strftime("%A, %B %d, %Y at %I:%M %p %Z"),
            "day_of_week": now.strftime("%A"),
            "utc_offset": now.strftime("%z"),
            "utc_time": utc_now.strftime("%H:%M:%S UTC")
        }
    except Exception as e:
        return {"error": str(e), "note": "Use IANA timezone names like 'America/New_York'"}


@mcp.tool()
def convert_timezone(
    time_str: str,
    from_timezone: str,
    to_timezone: str
) -> dict:
    """
    Convert a time from one timezone to another.

    Args:
        time_str: Time in HH:MM format (e.g. "14:30")
        from_timezone: Source timezone (e.g. "America/New_York")
        to_timezone: Target timezone (e.g. "Asia/Karachi")

    Returns:
        Converted time information
    """
    try:
        hour, minute = map(int, time_str.split(":"))
        from_tz = pytz.timezone(from_timezone)
        to_tz = pytz.timezone(to_timezone)

        today = datetime.now(from_tz).date()
        source_dt = from_tz.localize(
            datetime(today.year, today.month, today.day, hour, minute)
        )
        target_dt = source_dt.astimezone(to_tz)

        return {
            "original": f"{time_str} {from_timezone}",
            "converted": target_dt.strftime("%H:%M"),
            "converted_full": target_dt.strftime("%I:%M %p %Z"),
            "timezone": to_timezone,
            "date": target_dt.strftime("%Y-%m-%d")
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: WEB TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def fetch_webpage(url: str, max_chars: int = 3000) -> str:
    """
    Fetch and return content from a public webpage.

    Args:
        url: URL to fetch (must start with https://)
        max_chars: Maximum characters to return (default 3000)

    Returns:
        Page content as plain text
    """
    if not url.startswith("https://"):
        return "Error: Only HTTPS URLs are supported for security."

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                url,
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": "MCP-Assistant/1.0"}
            )
            resp.raise_for_status()

            import re
            text = re.sub('<[^<]+?>', ' ', resp.text)
            text = re.sub(r'\s+', ' ', text).strip()

            return text[:max_chars] + ("..." if len(text) > max_chars else "")

        except httpx.HTTPStatusError as e:
            return f"HTTP Error {e.response.status_code}: {url}"
        except Exception as e:
            return f"Error fetching {url}: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: TEXT PROCESSING TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def analyze_text(text: str) -> dict:
    """
    Analyze text and return statistics and insights.

    Args:
        text: Text to analyze

    Returns:
        Detailed text statistics
    """
    words = text.split()
    sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Word frequency (top 10)
    word_freq = {}
    for word in words:
        w = word.lower().strip('.,!?;:"\'()[]{}')
        if len(w) > 3:  # Skip short words
            word_freq[w] = word_freq.get(w, 0) + 1
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "characters": len(text),
        "characters_no_spaces": len(text.replace(" ", "")),
        "words": len(words),
        "sentences": len(sentences),
        "paragraphs": len(paragraphs),
        "avg_word_length": round(sum(len(w) for w in words) / len(words), 2) if words else 0,
        "avg_sentence_length": round(len(words) / len(sentences), 1) if sentences else 0,
        "estimated_reading_time_minutes": round(len(words) / 200, 1),
        "top_words": [{"word": w, "count": c} for w, c in top_words]
    }


@mcp.tool()
def format_json(json_text: str) -> str:
    """
    Pretty-format a JSON string.

    Args:
        json_text: Raw JSON string to format

    Returns:
        Nicely formatted JSON
    """
    import json
    try:
        data = json.loads(json_text)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Invalid JSON: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: FILE TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@mcp.tool()
def save_note(title: str, content: str) -> str:
    """
    Save a note to a file in the workspace.

    Args:
        title: Note title (used as filename)
        content: Note content

    Returns:
        Confirmation with file location
    """
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
    filename = safe_title.replace(' ', '_').lower() + ".md"
    filepath = WORKSPACE / "notes" / filename
    filepath.parent.mkdir(exist_ok=True)

    note_content = f"# {title}\n\n*Saved: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n{content}"

    filepath.write_text(note_content, encoding="utf-8")
    return f"✅ Note saved: {filepath}"


@mcp.tool()
def list_notes() -> list:
    """List all saved notes."""
    notes_dir = WORKSPACE / "notes"
    if not notes_dir.exists():
        return ["No notes yet. Use save_note() to create one."]

    return [f.stem.replace('_', ' ').title() for f in sorted(notes_dir.glob("*.md"))]


if __name__ == "__main__":
    print("🚀 All-In-One MCP Server starting...", file=sys.stderr)
    mcp.run()

# 📖 Chapter 9: Advanced MCP Patterns

This chapter covers advanced patterns used in real production MCP systems — streaming, multi-server architecture, tool composition, and memory.

---

## 🌊 Pattern 1: Streaming Responses

Streaming sends results to the user as they're generated — no waiting!

```python
# examples/05_streaming/streaming_server.py

import asyncio
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("streaming-server")


@mcp.tool()
async def generate_report(topic: str, sections: int = 5, context: Context = None) -> str:
    """
    Generate a multi-section report with real-time progress updates.
    
    Args:
        topic: Topic to write the report about
        sections: Number of sections to generate (default: 5)
        context: MCP context for progress updates
    
    Returns:
        The complete generated report
    """
    report_parts = []
    
    section_titles = [
        "Executive Summary",
        "Background & Context",
        "Key Findings",
        "Analysis",
        "Recommendations",
        "Conclusion",
        "Next Steps",
        "Risk Assessment"
    ]
    
    for i in range(min(sections, len(section_titles))):
        title = section_titles[i]
        
        # Send progress update to user
        if context:
            await context.report_progress(
                progress=i,
                total=sections,
                message=f"Writing section {i+1}/{sections}: {title}..."
            )
            await context.info(f"Generating: {title}")
        
        # Simulate generating this section (replace with real LLM call)
        await asyncio.sleep(0.5)  # Simulate work
        
        section_content = f"""
## {i+1}. {title}

This section covers {title.lower()} for the topic: {topic}.
[Content would be generated here by the AI...]
"""
        report_parts.append(section_content)
    
    # Final progress update
    if context:
        await context.info("Report generation complete!")
    
    full_report = f"# Report: {topic}\n" + "\n".join(report_parts)
    return full_report


@mcp.tool()
async def process_items(items: str, context: Context = None) -> dict:
    """
    Process a list of items with progress tracking.
    
    Args:
        items: Comma-separated list of items to process
        context: MCP context
    
    Returns:
        Processing results
    """
    item_list = [item.strip() for item in items.split(",")]
    total = len(item_list)
    results = []
    
    for i, item in enumerate(item_list):
        # Progress update
        if context:
            await context.report_progress(
                progress=i,
                total=total,
                message=f"Processing: {item}"
            )
        
        # Simulate processing
        await asyncio.sleep(0.3)
        results.append({
            "item": item,
            "status": "processed",
            "result": f"Processed '{item}' successfully"
        })
    
    return {
        "total_processed": total,
        "results": results
    }


if __name__ == "__main__":
    mcp.run()
```

---

## 🏗️ Pattern 2: Multi-Server Architecture

Real AI systems connect to multiple specialized MCP servers simultaneously.

```
Claude AI
    │
    ├──────────────────────────────┐
    │                              │
    ▼                              ▼
Weather Server              GitHub Server
• get_weather()             • read_file()
• get_forecast()            • list_repos()
• get_alerts()              • create_issue()
    │                              │
    ▼                              ▼
Weather API                  GitHub API
```

### Claude Desktop Multi-Server Config:

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/projects/weather_server.py"]
    },
    "files": {
      "command": "python",
      "args": ["/projects/file_server.py"]
    },
    "github": {
      "command": "python",
      "args": ["/projects/github_server.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    },
    "database": {
      "command": "python",
      "args": ["/projects/db_server.py"],
      "env": {
        "DB_PATH": "/data/mydb.sqlite"
      }
    }
  }
}
```

Now Claude can use ALL these tools in a single conversation:
```
User: "Get the weather in London and save a report to GitHub"
Claude: → calls weather server → get_weather("London")
Claude: → calls github server → create_file("weather-report.md", ...)
Claude: "Done! Weather report saved to your GitHub repo."
```

---

## 🔗 Pattern 3: Tool Composition

Tools can call other tools — building complex workflows from simple pieces.

```python
# examples/06_multiserver/tool_composition.py

from mcp.server.fastmcp import FastMCP, Context
import httpx

mcp = FastMCP("composition-server")


# ─── Level 1: Basic tools ──────────────────────────────────────────────────
@mcp.tool()
async def fetch_url_content(url: str) -> str:
    """
    Fetch raw content from a URL.
    
    Args:
        url: URL to fetch
    
    Returns:
        Page content (first 3000 chars)
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15.0, follow_redirects=True)
        return resp.text[:3000]


@mcp.tool()
def extract_key_facts(text: str, max_facts: int = 5) -> list:
    """
    Extract key facts from text using simple heuristics.
    
    Args:
        text: Text to extract facts from
        max_facts: Maximum facts to return
    
    Returns:
        List of key sentences
    """
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 30]
    return sentences[:max_facts]


# ─── Level 2: Composed tool (uses the above tools internally) ─────────────
@mcp.tool()
async def research_topic(topic: str, context: Context = None) -> dict:
    """
    Research a topic: fetches multiple sources and extracts key information.
    This tool composes multiple simpler tools internally.
    
    Args:
        topic: Topic to research
        context: MCP context
    
    Returns:
        Research summary with sources and key facts
    """
    if context:
        await context.info(f"Starting research on: {topic}")
    
    # Step 1: Search for the topic (using Wikipedia)
    search_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={topic}&prop=extracts&exintro=1&format=json"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(search_url, timeout=10.0)
            data = resp.json()
            
            pages = data.get("query", {}).get("pages", {})
            page = list(pages.values())[0]
            
            if "extract" in page:
                raw_text = page["extract"]
                # Clean HTML tags
                import re
                clean_text = re.sub('<[^<]+?>', '', raw_text)
            else:
                clean_text = f"No Wikipedia article found for: {topic}"
                
        except Exception as e:
            clean_text = f"Research error: {e}"
    
    if context:
        await context.info("Extracting key facts...")
    
    # Step 2: Extract facts from the content
    facts = extract_key_facts(clean_text, max_facts=5)
    
    return {
        "topic": topic,
        "summary": clean_text[:500] + "..." if len(clean_text) > 500 else clean_text,
        "key_facts": facts,
        "source": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
    }


if __name__ == "__main__":
    mcp.run()
```

---

## 🧠 Pattern 4: Memory and Context

Give your MCP server a memory so it can remember things across tool calls:

```python
# examples/08_advanced_agents/memory_server.py

from mcp.server.fastmcp import FastMCP
from datetime import datetime
from typing import Optional
import json

mcp = FastMCP("memory-server")

# ─── In-memory storage (simple, for single session) ───────────────────────
# In production, use a real database (SQLite, Redis, etc.)
_memory_store = {}
_conversation_log = []


@mcp.tool()
def remember(key: str, value: str, category: str = "general") -> str:
    """
    Store information in memory for later retrieval.
    
    Args:
        key: A unique identifier for this information
        value: The information to store
        category: Category to organize memories (default: general)
    
    Returns:
        Confirmation message
    """
    _memory_store[key] = {
        "value": value,
        "category": category,
        "stored_at": datetime.now().isoformat()
    }
    return f"✅ Remembered '{key}' in category '{category}'"


@mcp.tool()
def recall(key: str) -> str:
    """
    Retrieve previously stored information by key.
    
    Args:
        key: The key to look up
    
    Returns:
        The stored value, or a message if not found
    """
    if key in _memory_store:
        item = _memory_store[key]
        return f"📝 {key}: {item['value']} (stored: {item['stored_at']})"
    else:
        return f"Nothing remembered with key '{key}'"


@mcp.tool()
def recall_by_category(category: str) -> list:
    """
    Get all memories in a specific category.
    
    Args:
        category: Category to retrieve
    
    Returns:
        List of all memories in that category
    """
    matches = []
    for key, item in _memory_store.items():
        if item["category"] == category:
            matches.append(f"{key}: {item['value']}")
    
    return matches if matches else [f"No memories in category '{category}'"]


@mcp.tool()
def forget(key: str) -> str:
    """
    Delete a stored memory.
    
    Args:
        key: Key to delete
    
    Returns:
        Confirmation or error message
    """
    if key in _memory_store:
        del _memory_store[key]
        return f"🗑️ Forgot '{key}'"
    else:
        return f"No memory found with key '{key}'"


@mcp.tool()
def list_memories(category: Optional[str] = None) -> dict:
    """
    List all stored memories, optionally filtered by category.
    
    Args:
        category: Optional category filter
    
    Returns:
        Dictionary of all memories
    """
    if category:
        filtered = {k: v for k, v in _memory_store.items() 
                   if v["category"] == category}
        return {"category": category, "count": len(filtered), "memories": filtered}
    else:
        categories = {}
        for key, item in _memory_store.items():
            cat = item["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(key)
        
        return {
            "total_memories": len(_memory_store),
            "categories": categories
        }


if __name__ == "__main__":
    mcp.run()
```

---

## 🔐 Pattern 5: Secure Server with API Keys

```python
# examples/08_advanced_agents/secure_server.py

import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("secure-server")

# ─── Load secrets from environment (NEVER hardcode keys!) ─────────────────
REQUIRED_ENV_VARS = ["WEATHER_API_KEY", "DATABASE_URL"]

def check_environment():
    """Verify all required environment variables are set."""
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        import sys
        print(f"ERROR: Missing environment variables: {missing}", file=sys.stderr)
        print("Set them in your .env file or shell environment.", file=sys.stderr)
        sys.exit(1)

check_environment()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")


@mcp.tool()
async def get_premium_weather(city: str) -> dict:
    """
    Get detailed weather data using the premium API.
    
    Args:
        city: City name
    
    Returns:
        Detailed weather data including hourly forecasts
    """
    import httpx
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.weatherapi.com/v1/current.json",
            params={"key": WEATHER_API_KEY, "q": city},
            timeout=10.0
        )
        return resp.json()


if __name__ == "__main__":
    mcp.run()
```

**Setup:**
```bash
# Create .env file
WEATHER_API_KEY=your_key_here
DATABASE_URL=sqlite:///data.db

# Run server
python secure_server.py
```

---

## 📊 Pattern 6: Async Parallel Execution

Execute multiple API calls in parallel for faster responses:

```python
import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("parallel-server")


@mcp.tool()
async def compare_cities_weather(cities: str) -> dict:
    """
    Get weather for multiple cities simultaneously (parallel execution).
    
    Args:
        cities: Comma-separated city names (e.g. "London,Paris,Tokyo,Sydney")
    
    Returns:
        Weather data for all cities
    """
    city_list = [c.strip() for c in cities.split(",")][:6]  # Max 6 cities
    
    async def fetch_one(city: str) -> tuple:
        """Fetch weather for one city."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"https://wttr.in/{city}?format=3",
                    timeout=8.0
                )
                return city, resp.text.strip()
            except Exception as e:
                return city, f"Error: {e}"
    
    # Run ALL city requests at the same time (parallel!)
    # This is much faster than doing them one by one
    tasks = [fetch_one(city) for city in city_list]
    results = await asyncio.gather(*tasks)
    
    return {
        "cities_compared": len(city_list),
        "weather": {city: weather for city, weather in results}
    }


if __name__ == "__main__":
    mcp.run()
```

---

## 🧪 Testing Your Servers

```python
# tests/test_tools.py

import asyncio
import pytest
from mcp.server.fastmcp import FastMCP

# Import your server
import sys
sys.path.append("..")
from examples.weather_server import mcp


def test_server_has_tools():
    """Verify server exposes tools."""
    tools = mcp.list_tools()
    assert len(tools) > 0, "Server should have at least one tool"


def test_tool_names():
    """Check tool names are correct."""
    tool_names = [tool.name for tool in mcp.list_tools()]
    assert "get_weather" in tool_names


@pytest.mark.asyncio
async def test_weather_tool():
    """Test the weather tool returns data."""
    # Call the tool directly (not through MCP protocol)
    from examples.weather_server import get_weather
    result = await get_weather("London")
    assert "London" in result or "london" in result.lower()


if __name__ == "__main__":
    asyncio.run(test_weather_tool())
    print("All tests passed!")
```

---

👉 **[Chapter 10: Production Systems →](10_production.md)**

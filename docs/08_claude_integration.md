# 📖 Chapter 8: Connecting to Claude AI

This chapter shows you exactly how to connect your MCP server to Claude AI — both via Claude Desktop and programmatically via the API.

---

## 🖥️ Method 1: Claude Desktop (Easiest)

Claude Desktop is Anthropic's free desktop app that has built-in MCP support.

### Step 1: Install Claude Desktop

Download from: https://claude.ai/download

Available for: macOS and Windows

### Step 2: Find the Config File

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Step 3: Configure Your MCP Server

Edit the config file:

```json
{
  "mcpServers": {
    "my-weather-server": {
      "command": "python",
      "args": ["/absolute/path/to/your/server.py"]
    }
  }
}
```

**With virtual environment (recommended):**
```json
{
  "mcpServers": {
    "weather": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/your/weather_server.py"]
    }
  }
}
```

**Multiple servers:**
```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/projects/mcp/weather_server.py"]
    },
    "github": {
      "command": "python",
      "args": ["/projects/mcp/github_server.py"]
    },
    "database": {
      "command": "python",
      "args": ["/projects/mcp/db_server.py"],
      "env": {
        "DATABASE_URL": "sqlite:///data.db"
      }
    }
  }
}
```

### Step 4: Restart Claude Desktop

After saving the config, restart Claude Desktop completely.

### Step 5: Verify Connection

Look for the 🔧 tools icon in Claude Desktop. Click it to see your connected tools.

---

## 🧪 Complete Example: Weather Server for Claude Desktop

Here's a complete, working server you can connect to Claude Desktop right now:

```python
# weather_server.py
# Place this file somewhere on your computer
# Then add it to claude_desktop_config.json

import sys
import httpx
from mcp.server.fastmcp import FastMCP

# IMPORTANT: For stdio servers, only write to stderr for debugging
# Never write to stdout (it breaks the protocol)

mcp = FastMCP("weather")


@mcp.tool()
async def get_weather(city: str) -> str:
    """
    Get current weather for any city.
    Use this when the user asks about weather anywhere in the world.
    
    Args:
        city: City name (e.g. "London", "Karachi", "New York")
    
    Returns:
        Current weather conditions
    """
    print(f"Getting weather for: {city}", file=sys.stderr)
    
    async with httpx.AsyncClient() as client:
        try:
            # Free weather API — no key needed!
            response = await client.get(
                f"https://wttr.in/{city}?format=3",
                timeout=10.0
            )
            return response.text.strip()
        except Exception as e:
            return f"Could not get weather: {e}"


@mcp.tool()
async def compare_weather(cities: str) -> str:
    """
    Compare weather across multiple cities.
    
    Args:
        cities: Comma-separated list of cities (e.g. "London,Paris,Tokyo")
    
    Returns:
        Weather comparison table
    """
    city_list = [c.strip() for c in cities.split(",")]
    
    results = []
    async with httpx.AsyncClient() as client:
        for city in city_list[:5]:  # Limit to 5 cities
            try:
                resp = await client.get(
                    f"https://wttr.in/{city}?format=3",
                    timeout=8.0
                )
                results.append(resp.text.strip())
            except Exception:
                results.append(f"{city}: unavailable")
    
    return "Weather Comparison:\n" + "\n".join(results)


if __name__ == "__main__":
    mcp.run()
```

**Add to config:**
```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/full/path/to/weather_server.py"]
    }
  }
}
```

**Test in Claude Desktop:**
```
You: What's the weather in Karachi?
Claude: [calls get_weather("Karachi")]
Claude: The weather in Karachi is currently ☀️ 35°C (sunny).
```

---

## 💻 Method 2: Programmatic (Claude API + MCP)

You can also use MCP tools programmatically via the Anthropic Python SDK:

```python
# claude_with_mcp.py
# This shows how Claude API handles tool calling (the MCP pattern)

import anthropic
import json

client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

# ─── Define tools (equivalent to MCP tool schemas) ─────────────────────────
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for any city in the world.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city to get weather for"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculate",
        "description": "Perform a mathematical calculation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate, e.g. '2 + 2'"
                }
            },
            "required": ["expression"]
        }
    }
]


# ─── Tool execution functions ───────────────────────────────────────────────
def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return the result."""
    
    if tool_name == "get_weather":
        import httpx
        city = tool_input["city"]
        resp = httpx.get(f"https://wttr.in/{city}?format=3", timeout=10)
        return resp.text.strip()
    
    elif tool_name == "calculate":
        import math
        expr = tool_input["expression"]
        safe_env = {"sqrt": math.sqrt, "pi": math.pi, "__builtins__": {}}
        result = eval(expr, safe_env)
        return f"{expr} = {result}"
    
    else:
        return f"Unknown tool: {tool_name}"


# ─── Agentic loop ──────────────────────────────────────────────────────────
def chat_with_tools(user_message: str) -> str:
    """
    Run Claude with tool support.
    This implements the full agentic loop.
    """
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        # Call Claude
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        # Check if Claude wants to use a tool
        if response.stop_reason == "tool_use":
            # Process all tool calls
            tool_results = []
            
            for block in response.content:
                if block.type == "tool_use":
                    print(f"🔧 Claude is using: {block.name}({block.input})")
                    
                    # Execute the tool
                    result = execute_tool(block.name, block.input)
                    print(f"📤 Tool result: {result}")
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            
            # Add Claude's response and tool results to message history
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
            # Continue the loop — Claude will process the results
            continue
        
        else:
            # Claude is done — extract the text response
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "No response"


# ─── Example usage ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    questions = [
        "What's the weather in London?",
        "What is 1234 * 5678?",
        "What's the weather in Tokyo and what is sqrt(144)?"
    ]
    
    for question in questions:
        print(f"\n{'='*50}")
        print(f"👤 User: {question}")
        answer = chat_with_tools(question)
        print(f"🤖 Claude: {answer}")
```

**Run it:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
python claude_with_mcp.py
```

---

## 🔑 Setting Up Your API Key

```bash
# Linux/macOS
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# In a .env file (recommended for projects)
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

Load from .env in Python:
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file
api_key = os.getenv("ANTHROPIC_API_KEY")
```

---

## 🔄 The Agentic Loop Explained

When Claude uses tools, this loop runs:

```
1. Claude receives user message
2. Claude thinks: "I need the weather tool"
3. Claude returns: stop_reason = "tool_use"
4. YOUR CODE executes the tool
5. YOUR CODE sends tool result back to Claude
6. Claude reads the result and thinks again
7. If Claude needs another tool → go to step 2
8. When done: stop_reason = "end_turn"
9. Return final response to user
```

```
User Question
     │
     ▼
Claude thinks
     │
     ├── Needs tool? ──YES──► Execute Tool ──► Send result ──► Claude thinks again
     │                                                              │
     └── No tools needed? ──────────────────────────────────────────┘
                                                                    │
                                                                    ▼
                                                              Final Answer
```

---

## ✅ Checklist: Claude Integration

- [ ] Claude Desktop installed
- [ ] Config file edited with correct path
- [ ] Claude Desktop restarted
- [ ] 🔧 icon visible in Claude Desktop
- [ ] Test tool call works
- [ ] Error messages are clear (not crashes)

---

👉 **[Chapter 9: Advanced Patterns →](09_advanced_patterns.md)**

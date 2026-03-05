# 📖 Chapter 4: Building Real MCP Tools

Tools are the heart of MCP. In this chapter you'll learn how to build tools that connect to real APIs, handle errors gracefully, and return rich responses.

---

## 🔧 What Makes a Great Tool?

| Quality | Description |
|---------|-------------|
| **Clear name** | `get_current_weather` not `tool1` |
| **Good docstring** | Claude reads this to decide when to use it |
| **Strong typing** | Type hints generate the schema |
| **Error handling** | Never crash — return useful error messages |
| **Single purpose** | Each tool does ONE thing well |

---

## 🌤️ Example 1: Weather Tool (Real API)

```python
# tools/weather_tool.py

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-server")

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """
    Get the current weather for any city in the world.
    
    Args:
        city: Name of the city (e.g. "London", "Karachi", "New York")
    
    Returns:
        Current weather description including temperature and conditions
    """
    # We use wttr.in — a free weather API, no key needed!
    url = f"https://wttr.in/{city}?format=3"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                return response.text.strip()
            else:
                return f"Could not get weather for '{city}'. Please check the city name."
                
        except httpx.TimeoutException:
            return f"Weather service timed out. Please try again."
        
        except Exception as e:
            return f"Error fetching weather: {str(e)}"


@mcp.tool()
async def get_weather_forecast(city: str, days: int = 3) -> str:
    """
    Get a multi-day weather forecast for a city.
    
    Args:
        city: Name of the city
        days: Number of days to forecast (1-3, default is 3)
    
    Returns:
        Weather forecast as formatted text
    """
    # Clamp days between 1 and 3
    days = max(1, min(3, days))
    
    url = f"https://wttr.in/{city}?format=v2"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                return f"Weather forecast for {city} ({days} days):\n\n{response.text[:500]}"
            else:
                return f"Could not get forecast for '{city}'."
                
        except Exception as e:
            return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run()
```

**Test it:**
```
User: What's the weather in Tokyo?
Claude: → calls get_current_weather("Tokyo")
Result: "Tokyo: ⛅ +22°C"
Claude: "The current weather in Tokyo is partly cloudy with a temperature of 22°C."
```

---

## 🔢 Example 2: Calculator Tool (Complex Returns)

```python
# tools/calculator_tool.py

from mcp.server.fastmcp import FastMCP
import math

mcp = FastMCP("calculator-server")

@mcp.tool()
def calculate(expression: str) -> dict:
    """
    Safely evaluate a mathematical expression.
    
    Args:
        expression: A math expression like "2 + 2", "sqrt(16)", "10 * 5 / 2"
    
    Returns:
        Dictionary with result and any error message
    
    Supported operations: +, -, *, /, **, sqrt, sin, cos, tan, log, pi, e
    """
    # Safe math environment — only allow math functions
    safe_env = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "abs": abs,
        "round": round,
        "pi": math.pi,
        "e": math.e,
        "__builtins__": {}  # Disable all built-ins for safety!
    }
    
    try:
        result = eval(expression, safe_env)
        return {
            "success": True,
            "expression": expression,
            "result": result,
            "result_formatted": f"{expression} = {result}"
        }
    except ZeroDivisionError:
        return {
            "success": False,
            "expression": expression,
            "error": "Cannot divide by zero"
        }
    except Exception as e:
        return {
            "success": False,
            "expression": expression,
            "error": f"Invalid expression: {str(e)}"
        }


@mcp.tool()
def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    """
    Convert between common units of measurement.
    
    Args:
        value: The numeric value to convert
        from_unit: Source unit (e.g. "km", "miles", "kg", "lbs", "celsius", "fahrenheit")
        to_unit: Target unit (same options as from_unit)
    
    Returns:
        Dictionary with converted value or error message
    """
    conversions = {
        # Length
        ("km", "miles"):      lambda x: x * 0.621371,
        ("miles", "km"):      lambda x: x * 1.60934,
        ("meters", "feet"):   lambda x: x * 3.28084,
        ("feet", "meters"):   lambda x: x * 0.3048,
        
        # Weight
        ("kg", "lbs"):        lambda x: x * 2.20462,
        ("lbs", "kg"):        lambda x: x * 0.453592,
        ("grams", "ounces"):  lambda x: x * 0.035274,
        
        # Temperature
        ("celsius", "fahrenheit"):    lambda x: (x * 9/5) + 32,
        ("fahrenheit", "celsius"):    lambda x: (x - 32) * 5/9,
        ("celsius", "kelvin"):        lambda x: x + 273.15,
    }
    
    key = (from_unit.lower(), to_unit.lower())
    
    if key in conversions:
        result = conversions[key](value)
        return {
            "success": True,
            "original": f"{value} {from_unit}",
            "converted": f"{result:.4f} {to_unit}",
            "result": result
        }
    else:
        available = [f"{f} → {t}" for f, t in conversions.keys()]
        return {
            "success": False,
            "error": f"Conversion from '{from_unit}' to '{to_unit}' not supported.",
            "available_conversions": available
        }


if __name__ == "__main__":
    mcp.run()
```

---

## 📁 Example 3: File System Tool (with Safety)

```python
# tools/file_tool.py

import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("filesystem-server")

# ─── IMPORTANT: Set a safe root directory ──────────────────────────────────
# Only files within this directory can be accessed
SAFE_ROOT = Path.home() / "mcp-workspace"
SAFE_ROOT.mkdir(exist_ok=True)  # Create if it doesn't exist


def is_safe_path(path: Path) -> bool:
    """Check if a path is within our safe root directory."""
    try:
        path.resolve().relative_to(SAFE_ROOT.resolve())
        return True
    except ValueError:
        return False


@mcp.tool()
def read_file(filename: str) -> str:
    """
    Read the contents of a file from the workspace.
    
    Args:
        filename: Name of the file to read (relative to workspace)
    
    Returns:
        File contents as text
    """
    file_path = SAFE_ROOT / filename
    
    # Security check!
    if not is_safe_path(file_path):
        return f"Access denied: Cannot read files outside the workspace."
    
    if not file_path.exists():
        return f"File not found: '{filename}'"
    
    if not file_path.is_file():
        return f"'{filename}' is not a file."
    
    try:
        content = file_path.read_text(encoding="utf-8")
        return f"Contents of '{filename}':\n\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """
    Write content to a file in the workspace.
    
    Args:
        filename: Name of the file to create/overwrite
        content: Text content to write
    
    Returns:
        Success or error message
    """
    file_path = SAFE_ROOT / filename
    
    if not is_safe_path(file_path):
        return "Access denied: Cannot write outside the workspace."
    
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to '{filename}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
def list_files(subfolder: str = "") -> list:
    """
    List all files in the workspace or a subfolder.
    
    Args:
        subfolder: Optional subfolder to list (default: root workspace)
    
    Returns:
        List of filenames in the directory
    """
    target = SAFE_ROOT / subfolder if subfolder else SAFE_ROOT
    
    if not is_safe_path(target):
        return ["Access denied"]
    
    if not target.exists():
        return [f"Folder '{subfolder}' does not exist"]
    
    files = []
    for item in target.iterdir():
        if item.is_file():
            files.append(f"📄 {item.name}")
        elif item.is_dir():
            files.append(f"📁 {item.name}/")
    
    return sorted(files) if files else ["(empty folder)"]


if __name__ == "__main__":
    mcp.run()
```

---

## 🎛️ Tool with Optional Parameters

```python
@mcp.tool()
def search_text(
    text: str,
    query: str,
    case_sensitive: bool = False,   # ← Optional with default
    max_results: int = 10           # ← Optional with default
) -> dict:
    """
    Search for a query string within a text.
    
    Args:
        text: The text to search in
        query: The string to search for
        case_sensitive: Whether the search should be case-sensitive (default: False)
        max_results: Maximum number of results to return (default: 10)
    
    Returns:
        Dictionary with matches and their line numbers
    """
    lines = text.split('\n')
    matches = []
    
    for i, line in enumerate(lines, start=1):
        haystack = line if case_sensitive else line.lower()
        needle = query if case_sensitive else query.lower()
        
        if needle in haystack:
            matches.append({
                "line_number": i,
                "content": line.strip()
            })
            
            if len(matches) >= max_results:
                break
    
    return {
        "query": query,
        "total_matches": len(matches),
        "matches": matches
    }
```

---

## 🛡️ Error Handling Patterns

Always handle errors gracefully — never let a tool crash:

```python
@mcp.tool()
async def fetch_url(url: str) -> str:
    """
    Fetch content from a URL.
    
    Args:
        url: The URL to fetch
    
    Returns:
        Page content or error message
    """
    import httpx
    
    # ─── Validate input ────────────────────────────────────────────────
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"
    
    # ─── Fetch with timeout ────────────────────────────────────────────
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=15.0, follow_redirects=True)
            response.raise_for_status()  # Raises error for 4xx/5xx
            
            # Return first 2000 chars to avoid huge responses
            content = response.text[:2000]
            return f"Content from {url}:\n\n{content}"
            
        except httpx.TimeoutException:
            return f"Error: Request to {url} timed out after 15 seconds."
        
        except httpx.HTTPStatusError as e:
            return f"Error: Server returned {e.response.status_code} for {url}"
        
        except httpx.RequestError as e:
            return f"Error: Could not connect to {url}: {str(e)}"
```

---

## 📊 Return Types Summary

| Return Type | When to Use | Example |
|-------------|-------------|---------|
| `str` | Simple text responses | `"Weather: 22°C"` |
| `dict` | Structured data | `{"temp": 22, "unit": "C"}` |
| `list` | Multiple items | `["file1.py", "file2.py"]` |
| `int` / `float` | Numbers | `42` |
| `bool` | Yes/No results | `True` |

---

## 📁 Code For This Chapter

- [examples/02_tools/weather_tool.py](../examples/02_tools/weather_tool.py)
- [examples/02_tools/calculator_tool.py](../examples/02_tools/calculator_tool.py)
- [examples/02_tools/file_tool.py](../examples/02_tools/file_tool.py)

---

👉 **[Chapter 5: MCP Resources →](05_resources.md)**

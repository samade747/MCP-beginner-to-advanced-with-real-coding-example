# 📖 Chapter 3: Your First MCP Server

Time to write real code! In this chapter you will build and run your first MCP server from scratch.

---

## 📦 Step 1: Install the MCP SDK

Open your terminal and run:

```bash
pip install mcp
```

Verify the installation:
```bash
python -c "import mcp; print('MCP installed! Version:', mcp.__version__)"
```

---

## 📁 Step 2: Set Up Your Project

Create a new folder for your project:

```bash
mkdir my-first-mcp
cd my-first-mcp
```

---

## 🖊️ Step 3: Write Your First Server

Create a file called `server.py`:

```python
# server.py
# Your very first MCP server!

from mcp.server.fastmcp import FastMCP

# ─── Step 1: Create the server ─────────────────────────────────────────────
# Give your server a name. This is what clients see.
mcp = FastMCP("my-first-server")

# ─── Step 2: Add a simple tool ─────────────────────────────────────────────
@mcp.tool()
def say_hello(name: str) -> str:
    """
    Say hello to someone.
    
    Args:
        name: The person's name to greet
    
    Returns:
        A greeting message
    """
    return f"Hello, {name}! Welcome to MCP! 🎉"

# ─── Step 3: Run the server ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting MCP server...", flush=True)
    mcp.run()
```

---

## ▶️ Step 4: Run the Server

```bash
python server.py
```

You should see:
```
Starting MCP server...
```

The server is now running and waiting for connections!

> 💡 **Note:** The server will appear to "hang" — that's normal! It's waiting for a client to connect via stdio.

Press `Ctrl+C` to stop it.

---

## 🔍 What Just Happened?

Let's break down each part of the code:

```python
from mcp.server.fastmcp import FastMCP
```
We import `FastMCP` — a high-level helper that makes building servers easy. It handles all the JSON-RPC complexity for you.

---

```python
mcp = FastMCP("my-first-server")
```
We create a server instance with a name. The name identifies your server to clients.

---

```python
@mcp.tool()
def say_hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"
```

The `@mcp.tool()` decorator turns a normal Python function into an MCP tool. FastMCP automatically:
- Reads the **function name** → tool name
- Reads the **docstring** → tool description
- Reads the **type hints** → input/output schema
- Handles all the protocol details

---

```python
mcp.run()
```
Starts the server using stdio transport (default). The server now waits for JSON-RPC messages.

---

## 🧠 Understanding Tool Schemas

When you write a tool, MCP automatically creates a schema from your type hints. Here's what the `say_hello` tool looks like to a client:

```json
{
  "name": "say_hello",
  "description": "Say hello to someone.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "The person's name to greet"
      }
    },
    "required": ["name"]
  }
}
```

Claude reads this schema to understand:
- What the tool does (description)
- What inputs it needs (inputSchema)
- Which inputs are required

---

## 🔢 Step 5: Add More Tools

Let's make the server more interesting. Update `server.py`:

```python
# server.py - Enhanced version

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-first-server")

# ─── Tool 1: Greet ─────────────────────────────────────────────────────────
@mcp.tool()
def say_hello(name: str) -> str:
    """Say hello to someone by name."""
    return f"Hello, {name}! 👋"

# ─── Tool 2: Calculator ────────────────────────────────────────────────────
@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """
    Add two numbers together.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        The sum of a and b
    """
    return a + b

@mcp.tool()
def multiply_numbers(a: float, b: float) -> float:
    """
    Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        The product of a and b
    """
    return a * b

# ─── Tool 3: Text helper ───────────────────────────────────────────────────
@mcp.tool()
def count_words(text: str) -> dict:
    """
    Count words and characters in a text.
    
    Args:
        text: The text to analyze
    
    Returns:
        Dictionary with word count and character count
    """
    words = text.split()
    return {
        "word_count": len(words),
        "character_count": len(text),
        "character_count_no_spaces": len(text.replace(" ", ""))
    }

if __name__ == "__main__":
    mcp.run()
```

---

## 🧪 Step 6: Test with the MCP Inspector

The MCP SDK comes with a built-in inspector tool. Run:

```bash
mcp dev server.py
```

This opens an interactive web interface where you can:
- See all your tools
- Call tools manually
- See request/response JSON
- Debug your server

> 💡 This is the fastest way to test your server without Claude Desktop!

---

## 📊 Type Hints You Can Use

MCP supports all common Python types:

```python
# Basic types
def my_tool(
    name: str,          # text
    count: int,         # whole number
    price: float,       # decimal number
    active: bool,       # true/false
) -> str:
    ...

# Optional inputs (not required)
from typing import Optional

def optional_tool(
    required_input: str,
    optional_input: Optional[str] = None
) -> str:
    ...

# Return types
def returns_dict() -> dict:      # JSON object
    return {"key": "value"}

def returns_list() -> list:      # JSON array
    return [1, 2, 3]
```

---

## ⚠️ Common Mistakes (and Fixes)

### ❌ Mistake 1: Writing to stdout
```python
# WRONG - this breaks the JSON-RPC protocol!
@mcp.tool()
def my_tool():
    print("Hello")  # ← breaks stdio transport!
    return "result"
```

```python
# CORRECT - use stderr for debugging
import sys

@mcp.tool()
def my_tool():
    print("Hello", file=sys.stderr)  # ← safe!
    return "result"
```

### ❌ Mistake 2: No type hints
```python
# WRONG - MCP can't create schema without types
@mcp.tool()
def bad_tool(name):  # ← no type hints!
    return f"Hello {name}"
```

```python
# CORRECT - always add type hints
@mcp.tool()
def good_tool(name: str) -> str:
    return f"Hello {name}"
```

### ❌ Mistake 3: No docstring
```python
# WRONG - Claude won't know what this tool does
@mcp.tool()
def mystery_tool(x: int) -> int:
    return x * 2
```

```python
# CORRECT - always write a clear docstring
@mcp.tool()
def double_number(x: int) -> int:
    """Double a number (multiply by 2)."""
    return x * 2
```

---

## ✅ What We Built

You now have a working MCP server with:
- ✅ 4 tools
- ✅ Proper type hints
- ✅ Clear docstrings
- ✅ Multiple return types

---

## 📁 Code For This Chapter

See the complete example: [examples/01_basic/hello_server.py](../examples/01_basic/hello_server.py)

---

👉 **[Chapter 4: Building Real Tools →](04_tools.md)**

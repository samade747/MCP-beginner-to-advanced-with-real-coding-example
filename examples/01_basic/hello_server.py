"""
examples/01_basic/hello_server.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your very first MCP server!

HOW TO RUN:
  python hello_server.py

HOW TO TEST:
  mcp dev hello_server.py

WHAT IT DOES:
  • Creates an MCP server named "hello-world"
  • Exposes 4 simple tools
  • Claude can use these tools in conversations
"""

import sys
from mcp.server.fastmcp import FastMCP

# ─── Create the MCP server ─────────────────────────────────────────────────
mcp = FastMCP("hello-world")


# ─── Tool 1: Simple greeting ───────────────────────────────────────────────
@mcp.tool()
def say_hello(name: str) -> str:
    """
    Say hello to someone by name.

    Use this when the user wants to greet someone.

    Args:
        name: The person's name to greet

    Returns:
        A personalized greeting message
    """
    return f"Hello, {name}! Welcome to MCP! 🎉"


# ─── Tool 2: Addition ──────────────────────────────────────────────────────
@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """
    Add two numbers together.

    Args:
        a: The first number
        b: The second number

    Returns:
        The sum of a and b
    """
    return a + b


# ─── Tool 3: String reversal ───────────────────────────────────────────────
@mcp.tool()
def reverse_text(text: str) -> str:
    """
    Reverse any text string.

    Args:
        text: The text to reverse

    Returns:
        The text in reverse order
    """
    return text[::-1]


# ─── Tool 4: Word counter ──────────────────────────────────────────────────
@mcp.tool()
def count_words(text: str) -> dict:
    """
    Count words, characters, and sentences in a text.

    Args:
        text: The text to analyze

    Returns:
        A dictionary with word count, character count, and sentence count
    """
    words = text.split()
    sentences = [s for s in text.split('.') if s.strip()]

    return {
        "word_count": len(words),
        "character_count": len(text),
        "character_count_no_spaces": len(text.replace(" ", "")),
        "sentence_count": len(sentences),
        "average_word_length": round(
            sum(len(w) for w in words) / len(words), 2
        ) if words else 0
    }


# ─── Run the server ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting Hello World MCP Server...", file=sys.stderr)
    print("   Connect via Claude Desktop or 'mcp dev hello_server.py'", file=sys.stderr)
    mcp.run()

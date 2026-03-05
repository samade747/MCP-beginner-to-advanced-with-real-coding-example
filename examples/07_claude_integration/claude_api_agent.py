"""
examples/07_claude_integration/claude_api_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Claude API + MCP Tools — Complete Agentic Loop

This shows how to use Claude API programmatically with your own tools.
This is equivalent to what Claude Desktop does internally.

SETUP:
  export ANTHROPIC_API_KEY="sk-ant-..."
  pip install anthropic httpx

RUN:
  python claude_api_agent.py

HOW IT WORKS:
  1. You define tools (same schema as MCP)
  2. Claude decides which tools to use
  3. You execute the tools
  4. Send results back to Claude
  5. Claude gives the final answer
  (Repeat steps 2-4 as needed — this is the "agentic loop")
"""

import os
import sys
import math
import httpx
import anthropic

# ─── Initialize client ─────────────────────────────────────────────────────
# Reads ANTHROPIC_API_KEY from environment
client = anthropic.Anthropic()

MODEL = "claude-opus-4-6"


# ─── Tool Definitions ──────────────────────────────────────────────────────
# These are the same schema as MCP tools — Claude reads these to understand
# what tools are available and when to use them.

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for any city in the world. Use this when the user asks about weather, temperature, or conditions in a specific location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name (e.g. 'London', 'Karachi', 'New York')"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculate",
        "description": "Safely evaluate a mathematical expression. Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, pi, e",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate, e.g. '2 + 2', 'sqrt(144)', '10 ** 3'"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "search_wikipedia",
        "description": "Search Wikipedia for information about any topic. Use for factual questions about history, science, people, places, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to search for"
                },
                "sentences": {
                    "type": "integer",
                    "description": "Number of sentences to return (1-10, default 3)",
                    "default": 3
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "convert_units",
        "description": "Convert between units of measurement: km/miles, kg/lbs, celsius/fahrenheit, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "number",
                    "description": "The value to convert"
                },
                "from_unit": {
                    "type": "string",
                    "description": "Source unit (e.g. km, miles, kg, lbs, celsius, fahrenheit)"
                },
                "to_unit": {
                    "type": "string",
                    "description": "Target unit"
                }
            },
            "required": ["value", "from_unit", "to_unit"]
        }
    }
]


# ─── Tool Implementation ───────────────────────────────────────────────────
# These are the actual Python functions that execute when Claude calls a tool.

def execute_get_weather(city: str) -> str:
    """Execute the weather tool."""
    import httpx
    try:
        resp = httpx.get(f"https://wttr.in/{city}?format=3", timeout=10)
        return resp.text.strip() if resp.status_code == 200 else f"Could not get weather for {city}"
    except Exception as e:
        return f"Weather error: {e}"


def execute_calculate(expression: str) -> str:
    """Execute the calculator tool."""
    safe_env = {
        "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "log10": math.log10, "abs": abs, "round": round,
        "pi": math.pi, "e": math.e, "pow": pow,
        "__builtins__": {}
    }
    try:
        result = eval(expression, safe_env)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculation error: {e}"


def execute_search_wikipedia(topic: str, sentences: int = 3) -> str:
    """Execute the Wikipedia search tool."""
    try:
        resp = httpx.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "titles": topic,
                "prop": "extracts",
                "exintro": 1,
                "exsentences": min(sentences, 10),
                "explaintext": 1,
                "format": "json"
            },
            timeout=10
        )
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        page = list(pages.values())[0]
        extract = page.get("extract", "No article found.")
        title = page.get("title", topic)
        return f"{title}:\n{extract}"
    except Exception as e:
        return f"Wikipedia search error: {e}"


def execute_convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Execute the unit conversion tool."""
    conversions = {
        ("km", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x * 1.60934,
        ("kg", "lbs"): lambda x: x * 2.20462,
        ("lbs", "kg"): lambda x: x * 0.453592,
        ("celsius", "fahrenheit"): lambda x: (x * 9/5) + 32,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
        ("meters", "feet"): lambda x: x * 3.28084,
        ("feet", "meters"): lambda x: x * 0.3048,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} = {result:.4g} {to_unit}"
    else:
        return f"Cannot convert {from_unit} to {to_unit}"


# ─── Tool Router ──────────────────────────────────────────────────────────
def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Route tool calls to the correct function."""
    print(f"  🔧 Executing: {tool_name}({tool_input})", file=sys.stderr)

    if tool_name == "get_weather":
        return execute_get_weather(tool_input["city"])

    elif tool_name == "calculate":
        return execute_calculate(tool_input["expression"])

    elif tool_name == "search_wikipedia":
        return execute_search_wikipedia(
            tool_input["topic"],
            tool_input.get("sentences", 3)
        )

    elif tool_name == "convert_units":
        return execute_convert_units(
            tool_input["value"],
            tool_input["from_unit"],
            tool_input["to_unit"]
        )

    else:
        return f"Unknown tool: {tool_name}"


# ─── Agentic Loop ─────────────────────────────────────────────────────────
def ask_claude(user_message: str, verbose: bool = True) -> str:
    """
    The complete agentic loop:
    1. Send message to Claude
    2. If Claude wants to use tools, execute them
    3. Send tool results back
    4. Repeat until Claude is done
    5. Return final answer
    """
    messages = [{"role": "user", "content": user_message}]

    if verbose:
        print(f"\n{'='*55}", file=sys.stderr)
        print(f"👤 User: {user_message}", file=sys.stderr)

    iteration = 0
    max_iterations = 10  # Safety limit

    while iteration < max_iterations:
        iteration += 1

        # ─── Call Claude ───────────────────────────────────────────
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
            system=(
                "You are a helpful AI assistant with access to real-time tools. "
                "Use the available tools whenever they would give you accurate, "
                "current information. Be concise and helpful."
            )
        )

        if verbose:
            print(f"  📊 Stop reason: {response.stop_reason}", file=sys.stderr)

        # ─── Check if Claude wants to use tools ────────────────────
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    # Execute the tool
                    result = execute_tool(block.name, block.input)

                    if verbose:
                        print(f"  📤 Result: {result[:100]}...", file=sys.stderr)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Add Claude's response and tool results to conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            # Continue the loop — Claude will process the results
            continue

        else:
            # ─── Claude is done — extract the text response ────────
            for block in response.content:
                if hasattr(block, "text"):
                    if verbose:
                        print(f"\n🤖 Claude: {block.text}", file=sys.stderr)
                    return block.text

            return "No response generated."

    return "Error: Too many tool iterations."


# ─── Interactive Chat ──────────────────────────────────────────────────────
def chat():
    """Run an interactive chat session."""
    print("\n🤖 Claude AI Agent with MCP Tools")
    print("   Available tools: weather, calculator, wikipedia, unit converter")
    print("   Type 'quit' to exit")
    print("─" * 50)

    print("\nExample questions to try:")
    print("  • What's the weather in Tokyo?")
    print("  • What is sqrt(1764) + 100?")
    print("  • Tell me about Python programming language")
    print("  • Convert 100 miles to kilometers")
    print()

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            answer = ask_claude(user_input, verbose=False)
            print(f"\nClaude: {answer}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


# ─── Demo (non-interactive) ───────────────────────────────────────────────
def demo():
    """Run a demonstration with preset questions."""
    demo_questions = [
        "What's the weather like in London?",
        "What is 15 percent of 240?",
        "Who invented Python programming language?",
        "Convert 5 miles to kilometers",
        "What is the weather in Tokyo and what is 100 divided by 7?"
    ]

    print("\n🤖 Claude AI Agent — Demo Mode")
    print("Running preset questions...\n")

    for question in demo_questions:
        answer = ask_claude(question, verbose=True)
        print()


# ─── Entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set.")
        print("   Get your key from: https://console.anthropic.com")
        print("   Then run: export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)

    # Use --demo flag for non-interactive demo, otherwise interactive chat
    if "--demo" in sys.argv:
        demo()
    else:
        chat()

# 📖 Chapter 7: MCP Client Features

Client features are **special capabilities that servers can request from the client**. Instead of just serving data and tools, the server can ask the client to do things — like call an LLM or ask the user for input.

---

## 🎯 The Three Client Features

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT FEATURES                    │
│                                                      │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │  SAMPLING    │  │ ELICITATION │  │   ROOTS    │ │
│  │              │  │             │  │            │ │
│  │ Server asks  │  │ Server asks │  │ Server     │ │
│  │ client to    │  │ user for    │  │ learns     │ │
│  │ call LLM     │  │ more input  │  │ safe dirs  │ │
│  └──────────────┘  └─────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 🤖 Feature 1: Sampling (Server calls LLM)

**What is it?**
Sampling lets your MCP server request the client to make an LLM call. The server can use Claude's intelligence without needing its own API key!

**Why is this useful?**
- Server can ask Claude to summarize data it retrieved
- Server can ask Claude to generate text as part of a workflow
- No API keys stored in the server — the client handles it

```
Normal flow:     User → Claude → Server → Data

Sampling flow:   User → Claude → Server → gets data
                                Server → asks Claude to summarize it
                                Server → returns AI-enhanced result
```

### Sampling Code Example

```python
# examples/05_streaming/sampling_example.py

from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("sampling-server")

@mcp.tool()
async def analyze_and_explain(data: str, context: Context) -> str:
    """
    Fetches data and uses Claude to explain it in simple terms.
    
    Args:
        data: Raw data or text to analyze
        context: MCP context (injected automatically)
    
    Returns:
        AI-generated explanation of the data
    """
    # ─── Step 1: Process the raw data ──────────────────────────────────
    word_count = len(data.split())
    
    # ─── Step 2: Use sampling to ask Claude to explain it ──────────────
    # This calls Claude through the client — no API key needed in server!
    await context.info(f"Analyzing {word_count} words of data...")
    
    result = await context.sample(
        messages=[
            {
                "role": "user",
                "content": f"""Please explain this data in simple, clear language 
                that a non-technical person can understand:
                
                {data}
                
                Focus on: what it means, key patterns, and practical implications."""
            }
        ],
        max_tokens=500
    )
    
    return f"Analysis of your data:\n\n{result.content.text}"


@mcp.tool()
async def summarize_long_text(text: str, context: Context) -> str:
    """
    Summarize a long text using Claude AI.
    
    Args:
        text: The text to summarize (can be very long)
        context: MCP context
    
    Returns:
        A concise summary
    """
    # Notify the user that we're working
    await context.info("Preparing to summarize...")
    
    result = await context.sample(
        messages=[
            {
                "role": "user", 
                "content": f"Summarize this in 3 bullet points:\n\n{text}"
            }
        ],
        max_tokens=200
    )
    
    return result.content.text


if __name__ == "__main__":
    mcp.run()
```

---

## 📝 Feature 2: Elicitation (Ask User for Input)

**What is it?**
Elicitation lets your server ask the user for additional information mid-conversation through a form.

```
Conversation flow with Elicitation:

User: "Set up my project"
         ↓
Claude calls your tool
         ↓
Server: "I need more info!" → sends elicitation request
         ↓
Client shows user a FORM:
   Project Name: [__________]
   Language: [Python ▼]
   Testing framework: [pytest ▼]
         ↓
User fills form → submits
         ↓
Server receives the answers
         ↓
Server sets up project with correct settings
```

### Elicitation Code Example

```python
# This is a conceptual example — elicitation API varies by SDK version

from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("elicitation-server")

@mcp.tool()
async def setup_new_project(context: Context) -> str:
    """
    Set up a new project by asking the user for details.
    """
    # Request information from the user via a form
    # The client will display this as a UI form
    user_input = await context.elicit(
        message="Please provide your project details:",
        schema={
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "title": "Project Name",
                    "description": "What should your project be called?"
                },
                "language": {
                    "type": "string",
                    "title": "Programming Language",
                    "enum": ["Python", "JavaScript", "TypeScript", "Go"],
                    "default": "Python"
                },
                "include_tests": {
                    "type": "boolean",
                    "title": "Include Test Setup?",
                    "default": True
                }
            },
            "required": ["project_name", "language"]
        }
    )
    
    # Use the information the user provided
    name = user_input.get("project_name", "my-project")
    lang = user_input.get("language", "Python")
    tests = user_input.get("include_tests", True)
    
    return f"""✅ Project setup complete!

Project: {name}
Language: {lang}
Tests: {'Yes' if tests else 'No'}

Files created:
• {name}/README.md
• {name}/src/main.{'py' if lang == 'Python' else 'js'}
{'• ' + name + '/tests/test_main.py' if tests and lang == 'Python' else ''}
"""


if __name__ == "__main__":
    mcp.run()
```

---

## 📁 Feature 3: Roots (Safe Directory Access)

**What is it?**
Roots let the client tell the server which directories it's allowed to access. This is how Claude Desktop safely exposes your project files to MCP servers.

```
Without Roots:                  With Roots:
Server can try to read         Server only sees:
ANYTHING on the filesystem     /Users/you/my-project/
                               (and nothing else)
```

### Roots Code Example

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("roots-aware-server")

@mcp.tool()
async def list_project_files(context: Context) -> list:
    """
    List files in the user's approved project directories.
    Uses roots to find safe directories to access.
    """
    # Get the roots (approved directories) from the client
    roots = await context.get_roots()
    
    if not roots:
        return ["No project directories have been approved."]
    
    all_files = []
    
    for root in roots:
        root_path = root.uri.replace("file://", "")
        
        import os
        try:
            files = os.listdir(root_path)
            all_files.append(f"📁 {root.name or root_path}:")
            for f in files[:20]:  # Limit to 20 files per root
                all_files.append(f"  • {f}")
        except Exception as e:
            all_files.append(f"Error reading {root_path}: {e}")
    
    return all_files


if __name__ == "__main__":
    mcp.run()
```

---

## 📊 Progress Tracking

For long operations, send progress updates to the user:

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("progress-server")

@mcp.tool()
async def process_large_file(filename: str, context: Context) -> str:
    """
    Process a large file with progress updates.
    
    Args:
        filename: File to process
        context: MCP context for sending progress
    """
    # Simulate processing with progress updates
    total_steps = 5
    steps = [
        "Reading file...",
        "Parsing content...",
        "Validating data...",
        "Transforming records...",
        "Writing output..."
    ]
    
    for i, step in enumerate(steps):
        # Send progress update to client
        await context.report_progress(
            progress=i,
            total=total_steps,
            message=step
        )
        
        # Simulate work
        import asyncio
        await asyncio.sleep(1)
    
    return f"✅ Processing complete! {total_steps} steps finished."


if __name__ == "__main__":
    mcp.run()
```

---

## 📋 Logging Inside Tools

```python
@mcp.tool()
async def complex_operation(data: str, context: Context) -> str:
    """Demonstrate logging from within a tool."""
    
    await context.debug("Starting operation")           # Debug level
    await context.info("Processing data...")            # Info level
    
    if len(data) > 1000:
        await context.warning("Large data set detected")  # Warning level
    
    # Do work...
    result = data.upper()
    
    await context.info(f"Completed. Processed {len(data)} characters.")
    
    return result
```

---

👉 **[Chapter 8: Connecting to Claude AI →](08_claude_integration.md)**

# 💻 Coding Agent — MCP Project 4

Gives Claude the ability to read, write, and execute code.

## ⚠️ Security Warning

This server can execute Python code. Only use it:
- On your own machine
- In a trusted environment
- Never expose it publicly

## What It Does

| Tool | Description |
|------|-------------|
| `list_code_files` | List all code in workspace |
| `read_code` | Read a file with line numbers |
| `analyze_python_code` | Extract functions, classes, imports |
| `write_code` | Create new code files |
| `append_to_code` | Add code to existing files |
| `execute_python` | Run Python code (sandboxed) |
| `run_python_file` | Execute a file with subprocess |

## Workspace

All files are stored in: `~/mcp-workspace/code/`

## Setup

```bash
pip install mcp
python coding_agent.py
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "coding": {
      "command": "python",
      "args": ["/path/to/coding_agent.py"]
    }
  }
}
```

## Try These Prompts

- *"What Python files do I have in my workspace?"*
- *"Write a Python function to find prime numbers"*
- *"Analyze my main.py and explain its structure"*
- *"Execute this: print([x**2 for x in range(10)])"*
- *"Create a calculator.py with add, subtract, multiply, divide"*

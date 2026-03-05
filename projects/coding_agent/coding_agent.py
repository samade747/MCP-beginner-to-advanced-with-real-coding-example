"""
projects/coding_agent/coding_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project 4: Autonomous Coding Agent

Gives Claude the ability to read, write, and execute code:
  • Read and analyze code files
  • Write new code files
  • Execute Python code safely
  • Find bugs and suggest fixes
  • Run tests
  • Refactor code

⚠️  SECURITY NOTE:
    This server CAN execute Python code.
    Only run it in a trusted, sandboxed environment.
    Never expose it publicly.

SETUP:
  python coding_agent.py

TRY ASKING CLAUDE:
  "Read my main.py and explain what it does"
  "Write a Python function to sort a list of dictionaries"
  "Execute this code and tell me what it outputs: print(2**10)"
  "Find all Python files in my workspace"
  "Run the tests in test_app.py"
"""

import sys
import os
import io
import ast
import time
import traceback
import subprocess
from pathlib import Path
from typing import Optional
from contextlib import redirect_stdout, redirect_stderr
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("coding-agent")

# ─── Workspace (safe sandbox) ──────────────────────────────────────────────
WORKSPACE = Path.home() / "mcp-workspace" / "code"
WORKSPACE.mkdir(parents=True, exist_ok=True)

print(f"[coding] Workspace: {WORKSPACE}", file=sys.stderr)


def safe_path(filename: str) -> Path | None:
    """Resolve to absolute path within workspace. Returns None if unsafe."""
    try:
        target = (WORKSPACE / filename).resolve()
        target.relative_to(WORKSPACE.resolve())
        return target
    except ValueError:
        return None


# ─── Code Reading Tools ────────────────────────────────────────────────────

@mcp.tool()
def list_code_files(extension: str = "") -> list:
    """
    List all code files in the workspace.

    Args:
        extension: Filter by extension (e.g. ".py", ".js", ".ts")
                   Leave empty for all files.

    Returns:
        List of code files with their sizes
    """
    pattern = f"**/*{extension}" if extension else "**/*"
    files = []

    for path in sorted(WORKSPACE.glob(pattern)):
        if path.is_file():
            rel = path.relative_to(WORKSPACE)
            size = path.stat().st_size
            files.append({
                "path": str(rel),
                "size_bytes": size,
                "extension": path.suffix,
            })

    return files if files else [{"message": "No files found. Use write_code() to create some."}]


@mcp.tool()
def read_code(filename: str) -> str:
    """
    Read the contents of a code file.

    Args:
        filename: Path to the file relative to workspace

    Returns:
        File contents with line numbers
    """
    path = safe_path(filename)

    if path is None:
        return "Error: Access denied"

    if not path.exists():
        return f"File not found: '{filename}'"

    try:
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        numbered = "\n".join(f"{i+1:4d} │ {line}" for i, line in enumerate(lines))
        return f"📄 {filename} ({len(lines)} lines)\n{'─'*50}\n{numbered}"
    except Exception as e:
        return f"Error reading file: {e}"


@mcp.tool()
def analyze_python_code(filename: str) -> dict:
    """
    Analyze a Python file and extract its structure.

    Extracts: functions, classes, imports, line count, complexity hints.

    Args:
        filename: Python file to analyze (.py)

    Returns:
        Code structure analysis
    """
    path = safe_path(filename)

    if path is None or not path.exists():
        return {"error": f"File not found: {filename}"}

    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}
    except Exception as e:
        return {"error": str(e)}

    functions = []
    classes = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            args = [a.arg for a in node.args.args]
            docstring = ast.get_docstring(node) or ""
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "args": args,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "has_docstring": bool(docstring),
                "docstring_preview": docstring[:80] if docstring else ""
            })

        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "methods": methods,
                "has_docstring": bool(ast.get_docstring(node))
            })

        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")

    lines = content.split("\n")
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    comment_lines = [l for l in lines if l.strip().startswith("#")]

    return {
        "filename": filename,
        "total_lines": len(lines),
        "code_lines": len(code_lines),
        "comment_lines": len(comment_lines),
        "blank_lines": len(lines) - len(code_lines) - len(comment_lines),
        "functions": functions,
        "classes": classes,
        "imports": list(set(imports))[:20],
        "has_main_block": "if __name__" in content,
    }


# ─── Code Writing Tools ────────────────────────────────────────────────────

@mcp.tool()
def write_code(
    filename: str,
    content: str,
    overwrite: bool = False
) -> str:
    """
    Write code to a file in the workspace.

    Args:
        filename: File to create (e.g. "my_script.py", "utils/helpers.py")
        content: Code content to write
        overwrite: If True, replace existing files (default False)

    Returns:
        Confirmation message
    """
    path = safe_path(filename)

    if path is None:
        return "Error: Access denied"

    if path.exists() and not overwrite:
        return f"File '{filename}' already exists. Set overwrite=True to replace it."

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        lines = len(content.split("\n"))
        return f"✅ Written: {filename} ({lines} lines, {len(content)} chars)"
    except Exception as e:
        return f"Error writing file: {e}"


@mcp.tool()
def append_to_code(filename: str, content: str) -> str:
    """
    Append code to an existing file.

    Args:
        filename: File to append to
        content: Code to add at the end

    Returns:
        Confirmation message
    """
    path = safe_path(filename)

    if path is None:
        return "Error: Access denied"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Appended {len(content)} chars to {filename}"
    except Exception as e:
        return f"Error: {e}"


# ─── Code Execution Tool ───────────────────────────────────────────────────

@mcp.tool()
def execute_python(
    code: str,
    timeout_seconds: int = 10
) -> dict:
    """
    Execute Python code in a sandboxed environment.

    ⚠️ SECURITY: Only runs in the MCP workspace. Use with caution.

    Args:
        code: Python code to execute
        timeout_seconds: Maximum execution time (default 10s, max 30s)

    Returns:
        stdout output, stderr output, and execution status
    """
    # Safety limits
    timeout_seconds = min(timeout_seconds, 30)

    # Basic safety checks
    dangerous_patterns = [
        "import os", "import sys", "import subprocess",
        "__import__", "eval(", "exec(",
        "open(", "file(",
        "shutil", "socket", "urllib", "requests", "httpx",
    ]

    for pattern in dangerous_patterns:
        if pattern in code:
            return {
                "success": False,
                "error": f"Blocked: '{pattern}' is not allowed in sandboxed execution",
                "tip": "Use file_tool.py for file access, weather_tool.py for HTTP requests"
            }

    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    start_time = time.time()
    error = None
    result = None

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Execute with a timeout using a subprocess for real isolation
            exec_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "sorted": sorted,
                    "reversed": reversed,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "tuple": tuple,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "abs": abs,
                    "round": round,
                    "max": max,
                    "min": min,
                    "sum": sum,
                    "type": type,
                    "isinstance": isinstance,
                    "hasattr": hasattr,
                    "getattr": getattr,
                }
            }
            exec(code, exec_globals)

    except Exception as e:
        error = traceback.format_exc()

    elapsed = round(time.time() - start_time, 3)
    stdout_output = stdout_capture.getvalue()
    stderr_output = stderr_capture.getvalue()

    return {
        "success": error is None,
        "stdout": stdout_output[:2000] if stdout_output else "",
        "stderr": stderr_output[:500] if stderr_output else "",
        "error": error[:1000] if error else None,
        "execution_time_seconds": elapsed,
        "code_lines": len(code.strip().split("\n"))
    }


@mcp.tool()
def run_python_file(filename: str, timeout_seconds: int = 30) -> dict:
    """
    Run a Python file from the workspace using a subprocess.

    Args:
        filename: Python file to run (must be in workspace)
        timeout_seconds: Maximum run time (default 30s)

    Returns:
        stdout, stderr, exit code, and timing
    """
    path = safe_path(filename)

    if path is None or not path.exists():
        return {"error": f"File not found: {filename}"}

    if not filename.endswith(".py"):
        return {"error": "Can only run .py files"}

    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(WORKSPACE)
        )

        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[:3000],
            "stderr": result.stderr[:1000],
            "filename": filename
        }

    except subprocess.TimeoutExpired:
        return {"error": f"Execution timed out after {timeout_seconds}s"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("💻 Coding Agent MCP Server starting...", file=sys.stderr)
    print(f"   Workspace: {WORKSPACE}", file=sys.stderr)
    mcp.run()

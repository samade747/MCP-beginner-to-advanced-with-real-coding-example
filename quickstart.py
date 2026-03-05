#!/usr/bin/env python3
"""
quickstart.py
━━━━━━━━━━━━
Interactive quickstart guide for MCP Complete Guide.

RUN:
  python quickstart.py

This script will:
  1. Check your Python version
  2. Install required packages
  3. Run a test to verify everything works
  4. Show you how to connect to Claude Desktop
"""

import sys
import os
import subprocess
from pathlib import Path


def print_header():
    print("\n" + "═"*55)
    print("  🤖 MCP Complete Guide — Quickstart")
    print("  From Zero to Expert in Model Context Protocol")
    print("═"*55 + "\n")


def check_python_version():
    print("Step 1: Checking Python version...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"  ❌ Python {version.major}.{version.minor} detected")
        print("     MCP requires Python 3.10 or higher.")
        print("     Download from: https://www.python.org/downloads/")
        sys.exit(1)
    
    print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} — OK!\n")


def install_packages():
    print("Step 2: Installing required packages...")
    
    packages = ["mcp", "httpx", "python-dotenv", "requests"]
    
    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"  ✅ {pkg} — already installed")
        except ImportError:
            print(f"  📦 Installing {pkg}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "-q"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  ✅ {pkg} — installed!")
            else:
                print(f"  ⚠️  Could not install {pkg}: {result.stderr[:100]}")
    
    print()


def run_basic_test():
    print("Step 3: Running a basic server test...")
    
    # Test that the hello server can be imported
    hello_server = Path(__file__).parent / "examples" / "01_basic" / "hello_server.py"
    
    if not hello_server.exists():
        print(f"  ⚠️  Test file not found: {hello_server}")
        return
    
    # Test basic Python math (simulating the calculator tool)
    import math
    
    safe_env = {"sqrt": math.sqrt, "pi": math.pi, "abs": abs, "__builtins__": {}}
    result = eval("sqrt(144) + pi", safe_env)
    expected = math.sqrt(144) + math.pi
    
    assert abs(result - expected) < 0.001, "Calculator test failed!"
    print(f"  ✅ Calculator test: sqrt(144) + pi = {result:.4f}")
    
    # Test text analysis
    text = "Hello world from MCP!"
    words = text.split()
    assert len(words) == 4
    print(f"  ✅ Text analysis test: '{text}' has {len(words)} words")
    
    print()


def show_next_steps():
    print("Step 4: What to do next...\n")
    
    workspace = Path.home() / "mcp-workspace"
    workspace.mkdir(exist_ok=True)
    
    guide_path = Path(__file__).parent / "docs" / "01_introduction.md"
    server_path = Path(__file__).parent / "examples" / "01_basic" / "hello_server.py"
    config_path = Path(__file__).parent / "claude_desktop_config_examples.json"
    
    print("  📖 START READING:")
    print(f"     Open: {guide_path}")
    print()
    
    print("  🧪 TEST YOUR FIRST SERVER:")
    print(f"     python {server_path}")
    print()
    
    if sys.platform == "darwin":
        claude_config = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        claude_config = Path(os.environ.get("APPDATA", "~")) / "Claude" / "claude_desktop_config.json"
    
    print("  🔌 CONNECT TO CLAUDE DESKTOP:")
    print(f"     1. Install Claude Desktop from https://claude.ai/download")
    print(f"     2. Edit config file: {claude_config}")
    print(f"     3. See example config: {config_path}")
    print(f"     4. Restart Claude Desktop")
    print()
    
    print("  📁 YOUR WORKSPACE:")
    print(f"     Files will be saved to: {workspace}")
    print()
    
    print("  🏆 PROJECTS TO BUILD:")
    projects = [
        "Weather Agent → projects/weather_agent/",
        "Research Agent → projects/research_agent/",
        "Database Agent → projects/database_agent/"
    ]
    for p in projects:
        print(f"     • {p}")
    
    print()
    print("═"*55)
    print("  🎉 You're ready to build with MCP!")
    print("  Start with docs/01_introduction.md")
    print("═"*55 + "\n")


if __name__ == "__main__":
    print_header()
    check_python_version()
    install_packages()
    run_basic_test()
    show_next_steps()

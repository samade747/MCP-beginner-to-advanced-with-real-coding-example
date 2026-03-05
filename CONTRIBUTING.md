# Contributing to MCP Complete Guide

Thank you for helping make this the best MCP learning resource for students! 🎉

---

## 🐛 Found a Bug?

1. Check [existing issues](../../issues) first
2. Open a new issue with:
   - What you expected to happen
   - What actually happened
   - Your Python version (`python --version`)
   - Your MCP SDK version (`pip show mcp`)
   - Steps to reproduce

---

## 💡 Want to Add Something?

Great ideas for contributions:

- **New examples** — more tool types (database, email, calendar)
- **New projects** — Slack bot, email assistant, PDF reader
- **Better explanations** — clearer docs for beginners
- **Translations** — docs in other languages
- **Bug fixes** — fix broken examples
- **Diagrams** — better architecture visuals

---

## 🔧 How to Contribute

### Step 1: Fork & Clone
```bash
git clone https://github.com/yourname/mcpforge
cd mcpforge
```

### Step 2: Create a Branch
```bash
git checkout -b feature/my-new-example
# or
git checkout -b fix/broken-weather-tool
```

### Step 3: Make Your Changes

**For new examples:**
- Add your file to the correct `examples/` subfolder
- Follow the existing code style (docstrings, type hints, comments)
- Test it works with `mcp dev your_file.py`

**For documentation:**
- Edit files in `docs/`
- Keep language simple — remember this is for beginners
- Include working code examples

**For new projects:**
- Create a new folder in `projects/`
- Include a README.md in the project folder
- Include setup instructions

### Step 4: Test Your Code
```bash
# Run all tests
python tests/test_all_servers.py

# Test your specific server
mcp dev examples/your_file.py
```

### Step 5: Submit a Pull Request
```bash
git add .
git commit -m "Add: weather forecast comparison tool"
git push origin feature/my-new-example
```

Then open a Pull Request on GitHub.

---

## 📋 Code Standards

### Python Style
```python
# ✅ Good: clear name, type hints, docstring
@mcp.tool()
async def get_weather(city: str) -> str:
    """
    Get current weather for a city.
    
    Args:
        city: City name (e.g. "London", "Karachi")
    
    Returns:
        Weather description
    """
    ...

# ❌ Bad: unclear name, no types, no docstring
@mcp.tool()
def tool1(x):
    ...
```

### Always Include:
- Type hints on all parameters and return values
- Docstrings explaining what the tool does
- Error handling (never let tools crash)
- Comments for complex logic
- `file=sys.stderr` on all print statements

### Never Include:
- API keys or secrets (use environment variables)
- `print()` to stdout (breaks MCP protocol)
- Imports of unnecessary packages
- Code that accesses files outside the safe workspace

---

## 🏷️ Commit Message Format

```
Add: new gmail integration tool
Fix: weather tool timeout handling
Update: Chapter 3 examples for SDK v1.2
Remove: deprecated sampling example
Docs: improve architecture explanation
```

---

## 📝 Documentation Standards

- Write for someone with **zero MCP knowledge**
- Short paragraphs (2-4 sentences)
- Code examples for every concept
- ASCII diagrams for architecture
- Real-world analogies

---

## ❓ Questions?

Open a [Discussion](../../discussions) — no question is too basic!

---

*This project is MIT licensed. By contributing, you agree your contributions will be under the same license.*

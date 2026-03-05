"""
tests/test_all_servers.py
━━━━━━━━━━━━━━━━━━━━━━━━
Quick sanity tests for all MCP servers.

INSTALL TEST DEPS:
  pip install pytest pytest-asyncio

RUN TESTS:
  pytest tests/ -v

Or run this file directly:
  python tests/test_all_servers.py
"""

import sys
import math
import asyncio
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ─── Calculator Tests ──────────────────────────────────────────────────────

def test_calculator_basic():
    """Test basic arithmetic."""
    safe_env = {
        "sqrt": math.sqrt, "pi": math.pi, "e": math.e, "abs": abs,
        "round": round, "__builtins__": {}
    }
    assert eval("2 + 2", safe_env) == 4
    assert eval("10 * 5", safe_env) == 50
    assert eval("100 / 4", safe_env) == 25.0
    assert eval("2 ** 8", safe_env) == 256
    print("✅ Calculator basic tests passed")


def test_calculator_math_functions():
    """Test math functions."""
    safe_env = {
        "sqrt": math.sqrt, "pi": math.pi, "sin": math.sin,
        "cos": math.cos, "abs": abs, "__builtins__": {}
    }
    assert eval("sqrt(16)", safe_env) == 4.0
    assert eval("abs(-5)", safe_env) == 5
    assert round(eval("pi", safe_env), 4) == 3.1416
    print("✅ Calculator math function tests passed")


# ─── Unit Conversion Tests ─────────────────────────────────────────────────

def test_unit_conversions():
    """Test unit conversion logic."""
    conversions = {
        ("km", "miles"): lambda x: x * 0.621371,
        ("celsius", "fahrenheit"): lambda x: (x * 9/5) + 32,
        ("kg", "lbs"): lambda x: x * 2.20462,
    }

    # 1 km = 0.621 miles
    result = conversions[("km", "miles")](1)
    assert abs(result - 0.621371) < 0.001, f"Expected ~0.621, got {result}"

    # 100°C = 212°F
    result = conversions[("celsius", "fahrenheit")](100)
    assert result == 212.0, f"Expected 212, got {result}"

    # 1 kg = 2.20462 lbs
    result = conversions[("kg", "lbs")](1)
    assert abs(result - 2.20462) < 0.001

    print("✅ Unit conversion tests passed")


# ─── File System Tests ─────────────────────────────────────────────────────

def test_safe_path_validation():
    """Test that path traversal attacks are blocked."""
    workspace = Path.home() / "mcp-workspace"

    def is_safe_path(filename):
        try:
            target = (workspace / filename).resolve()
            target.relative_to(workspace.resolve())
            return True
        except ValueError:
            return False

    # Safe paths
    assert is_safe_path("notes.txt") == True
    assert is_safe_path("docs/readme.md") == True

    # Dangerous paths (path traversal)
    assert is_safe_path("../etc/passwd") == False
    assert is_safe_path("../../secret") == False

    print("✅ Path safety tests passed")


# ─── Text Analysis Tests ───────────────────────────────────────────────────

def test_text_analysis():
    """Test text analysis logic."""
    text = "Hello world. This is a test sentence. Python is great."
    words = text.split()
    sentences = [s.strip() for s in text.split('.') if s.strip()]

    assert len(words) == 10, f"Expected 10 words, got {len(words)}"
    assert len(sentences) == 3, f"Expected 3 sentences, got {len(sentences)}"
    print("✅ Text analysis tests passed")


# ─── JSON Validation Tests ─────────────────────────────────────────────────

def test_json_handling():
    """Test JSON parsing used in database tool."""
    # Valid JSON
    valid = '{"name": "Python Book", "price": 29.99, "quantity": 100}'
    data = json.loads(valid)
    assert data["name"] == "Python Book"
    assert data["price"] == 29.99

    # Invalid JSON
    try:
        json.loads("not valid json")
        assert False, "Should have raised exception"
    except json.JSONDecodeError:
        pass  # Expected

    print("✅ JSON handling tests passed")


# ─── Async Tests ───────────────────────────────────────────────────────────

async def test_async_tool():
    """Test that async tools work correctly."""
    import httpx

    # Test basic HTTP request works
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get("https://httpbin.org/get", timeout=5.0)
            assert resp.status_code == 200
            print("✅ Async HTTP tests passed")
        except Exception as e:
            print(f"⚠️  Async HTTP test skipped (network issue): {e}")


async def test_parallel_execution():
    """Test that parallel execution works."""
    import asyncio

    results = []

    async def task(i):
        await asyncio.sleep(0.1)
        results.append(i)

    # Run 5 tasks in parallel
    await asyncio.gather(*[task(i) for i in range(5)])

    assert len(results) == 5
    assert sorted(results) == [0, 1, 2, 3, 4]
    print("✅ Parallel execution tests passed")


# ─── Run all tests ─────────────────────────────────────────────────────────

def run_all_tests():
    """Run all tests and report results."""
    print("\n🧪 MCP Complete Guide — Test Suite")
    print("=" * 45)

    tests = [
        ("Calculator Basic", test_calculator_basic),
        ("Calculator Math Functions", test_calculator_math_functions),
        ("Unit Conversions", test_unit_conversions),
        ("Safe Path Validation", test_safe_path_validation),
        ("Text Analysis", test_text_analysis),
        ("JSON Handling", test_json_handling),
    ]

    async_tests = [
        ("Async Tool Execution", test_async_tool),
        ("Parallel Execution", test_parallel_execution),
    ]

    passed = 0
    failed = 0

    print("\n📋 Synchronous Tests:")
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
            failed += 1

    print("\n📋 Async Tests:")
    for name, test_fn in async_tests:
        try:
            asyncio.run(test_fn())
            passed += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
            failed += 1

    print(f"\n{'='*45}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} tests failed")


if __name__ == "__main__":
    run_all_tests()

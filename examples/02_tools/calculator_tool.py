"""
examples/02_tools/calculator_tool.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Safe math calculator tool.

TRY ASKING CLAUDE:
  "What is 15% of 240?"
  "Convert 100 miles to kilometers"
  "What is sqrt(144) + 5^2?"
"""

import math
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("calculator")


@mcp.tool()
def calculate(expression: str) -> dict:
    """
    Safely evaluate a mathematical expression.

    Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, log10, abs, round, pi, e

    Args:
        expression: A mathematical expression to evaluate.
                    Examples: "2 + 2", "sqrt(16)", "sin(pi/2)", "10**3"

    Returns:
        Dictionary with:
        - success: whether calculation worked
        - result: the numeric answer
        - expression: the original expression
        - error: error message if failed
    """
    # Safe math environment — ONLY allow math functions
    # This prevents code injection attacks!
    safe_env = {
        # Basic math functions
        "sqrt": math.sqrt,
        "cbrt": lambda x: x ** (1/3),
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,

        # Trig functions (radians)
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "atan2": math.atan2,

        # Log/exp functions
        "log": math.log,
        "log2": math.log2,
        "log10": math.log10,
        "exp": math.exp,
        "pow": pow,

        # Constants
        "pi": math.pi,
        "e": math.e,
        "inf": math.inf,

        # Disable all Python built-ins for safety
        "__builtins__": {}
    }

    try:
        result = eval(expression, safe_env)

        # Format nicely
        if isinstance(result, float):
            if result == int(result):
                formatted = str(int(result))
            else:
                formatted = f"{result:.6g}"  # Up to 6 significant figures
        else:
            formatted = str(result)

        return {
            "success": True,
            "expression": expression,
            "result": result,
            "result_formatted": formatted,
            "equation": f"{expression} = {formatted}"
        }

    except ZeroDivisionError:
        return {
            "success": False,
            "expression": expression,
            "error": "Cannot divide by zero"
        }
    except NameError as e:
        return {
            "success": False,
            "expression": expression,
            "error": f"Unknown function or variable: {e}. Available: sqrt, sin, cos, pi, e, ..."
        }
    except SyntaxError:
        return {
            "success": False,
            "expression": expression,
            "error": f"Invalid syntax. Example: '2 + 2' or 'sqrt(16)'"
        }
    except Exception as e:
        return {
            "success": False,
            "expression": expression,
            "error": str(e)
        }


@mcp.tool()
def calculate_percentage(value: float, percentage: float, operation: str = "of") -> dict:
    """
    Calculate percentages easily.

    Args:
        value: The base number
        percentage: The percentage (e.g. 15 for 15%)
        operation: Type of calculation:
                   "of" → what is X% of value?  (e.g. 15% of 200 = 30)
                   "what" → value is what % of total?
                   "increase" → value increased by X%
                   "decrease" → value decreased by X%

    Returns:
        Dictionary with the result and explanation
    """
    operations = {
        "of":       lambda v, p: v * (p / 100),
        "what":     lambda v, p: (v / p) * 100,  # p is the total here
        "increase": lambda v, p: v * (1 + p / 100),
        "decrease": lambda v, p: v * (1 - p / 100),
    }

    if operation not in operations:
        return {
            "success": False,
            "error": f"Unknown operation '{operation}'. Use: of, what, increase, decrease"
        }

    result = operations[operation](value, percentage)

    explanations = {
        "of":       f"{percentage}% of {value} = {result:.4g}",
        "what":     f"{value} is {result:.4g}% of {percentage}",
        "increase": f"{value} increased by {percentage}% = {result:.4g}",
        "decrease": f"{value} decreased by {percentage}% = {result:.4g}",
    }

    return {
        "success": True,
        "result": result,
        "explanation": explanations[operation]
    }


@mcp.tool()
def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    """
    Convert between common units of measurement.

    Args:
        value: The number to convert
        from_unit: Source unit. Options:
                   Length: km, miles, meters, feet, inches, cm
                   Weight: kg, lbs, grams, ounces
                   Temperature: celsius, fahrenheit, kelvin
                   Volume: liters, gallons, ml, fl_oz
        to_unit: Target unit (same options)

    Returns:
        Conversion result or error message
    """
    # All conversions stored as functions
    conversions = {
        # ─ Length ─────────────────────────────────
        ("km", "miles"):       lambda x: x * 0.621371,
        ("miles", "km"):       lambda x: x * 1.60934,
        ("km", "meters"):      lambda x: x * 1000,
        ("meters", "km"):      lambda x: x / 1000,
        ("meters", "feet"):    lambda x: x * 3.28084,
        ("feet", "meters"):    lambda x: x * 0.3048,
        ("feet", "inches"):    lambda x: x * 12,
        ("inches", "feet"):    lambda x: x / 12,
        ("inches", "cm"):      lambda x: x * 2.54,
        ("cm", "inches"):      lambda x: x / 2.54,
        ("miles", "feet"):     lambda x: x * 5280,
        ("feet", "miles"):     lambda x: x / 5280,

        # ─ Weight ─────────────────────────────────
        ("kg", "lbs"):         lambda x: x * 2.20462,
        ("lbs", "kg"):         lambda x: x * 0.453592,
        ("kg", "grams"):       lambda x: x * 1000,
        ("grams", "kg"):       lambda x: x / 1000,
        ("grams", "ounces"):   lambda x: x * 0.035274,
        ("ounces", "grams"):   lambda x: x * 28.3495,
        ("lbs", "ounces"):     lambda x: x * 16,
        ("ounces", "lbs"):     lambda x: x / 16,

        # ─ Temperature ────────────────────────────
        ("celsius", "fahrenheit"):  lambda x: (x * 9/5) + 32,
        ("fahrenheit", "celsius"):  lambda x: (x - 32) * 5/9,
        ("celsius", "kelvin"):      lambda x: x + 273.15,
        ("kelvin", "celsius"):      lambda x: x - 273.15,
        ("fahrenheit", "kelvin"):   lambda x: (x - 32) * 5/9 + 273.15,
        ("kelvin", "fahrenheit"):   lambda x: (x - 273.15) * 9/5 + 32,

        # ─ Volume ─────────────────────────────────
        ("liters", "gallons"):  lambda x: x * 0.264172,
        ("gallons", "liters"):  lambda x: x * 3.78541,
        ("liters", "ml"):       lambda x: x * 1000,
        ("ml", "liters"):       lambda x: x / 1000,
        ("liters", "fl_oz"):    lambda x: x * 33.814,
        ("fl_oz", "liters"):    lambda x: x / 33.814,
    }

    from_lower = from_unit.lower()
    to_lower = to_unit.lower()

    # Same unit — no conversion needed
    if from_lower == to_lower:
        return {
            "success": True,
            "original": f"{value} {from_unit}",
            "converted": f"{value} {to_unit}",
            "result": value,
            "note": "Same unit — no conversion needed."
        }

    key = (from_lower, to_lower)

    if key in conversions:
        result = conversions[key](value)
        return {
            "success": True,
            "original": f"{value} {from_unit}",
            "converted": f"{result:.6g} {to_unit}",
            "result": result,
            "formula": f"{value} {from_unit} = {result:.6g} {to_unit}"
        }
    else:
        # List available conversions for help
        available = list(set([f[0] for f in conversions.keys()]))
        return {
            "success": False,
            "error": f"Cannot convert '{from_unit}' to '{to_unit}'.",
            "tip": "Check unit spelling. Available units include: " + ", ".join(sorted(available))
        }


if __name__ == "__main__":
    mcp.run()

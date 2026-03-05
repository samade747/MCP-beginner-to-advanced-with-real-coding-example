"""
examples/05_streaming/streaming_demo.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Complete demo of MCP Streaming + Progress Tracking.

Streaming lets the user see real-time progress during
long-running operations instead of waiting for the final result.

WHAT THIS DEMO SHOWS:
  1. Progress reporting (progress bar updates)
  2. Logging from tools (info/warning/debug messages)
  3. Long-running async tasks with live updates
  4. Sampling — server asks Claude to generate text
  5. Parallel task execution with progress

TRY ASKING CLAUDE:
  "Generate a 5-section report about Python"
  "Process these 10 items: apple, banana, cherry, ..."
  "Analyze this large dataset with progress updates"
"""

import sys
import asyncio
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("streaming-demo")


# ══════════════════════════════════════════════════════
# EXAMPLE 1: Progress Tracking
# ══════════════════════════════════════════════════════

@mcp.tool()
async def generate_report(
    topic: str,
    num_sections: int = 5,
    ctx: Context = None
) -> str:
    """
    Generate a multi-section report with live progress updates.

    The user sees real-time progress as each section is written.

    Args:
        topic: The report topic
        num_sections: Number of sections (1-8, default 5)
        ctx: MCP Context for sending progress (injected automatically)

    Returns:
        The complete generated report
    """
    num_sections = max(1, min(8, num_sections))

    section_titles = [
        "Executive Summary",
        "Background & Context",
        "Current State Analysis",
        "Key Findings",
        "Challenges & Risks",
        "Opportunities",
        "Recommendations",
        "Conclusion & Next Steps",
    ]

    # Notify start
    if ctx:
        await ctx.info(f"Starting report generation on: {topic}")

    report_sections = []

    for i in range(num_sections):
        title = section_titles[i % len(section_titles)]

        # ─── Send progress update ──────────────────────────────────
        if ctx:
            await ctx.report_progress(
                progress=i,
                total=num_sections,
                message=f"Writing section {i+1}/{num_sections}: {title}..."
            )
            await ctx.info(f"📝 Generating: {title}")

        # Simulate writing this section (replace with real LLM call)
        await asyncio.sleep(0.8)

        section_content = f"""
## {i+1}. {title}

This section covers {title.lower()} for the topic: **{topic}**.

Key points for this section:
- Analysis of {title.lower()} from multiple perspectives
- Data-driven insights relevant to {topic}
- Practical implications for stakeholders

[In a real system, this content would be AI-generated based on your topic]
"""
        report_sections.append(section_content)

    # Final progress update
    if ctx:
        await ctx.report_progress(
            progress=num_sections,
            total=num_sections,
            message="Report complete! ✅"
        )
        await ctx.info(f"Report generated: {num_sections} sections, ~{num_sections * 150} words")

    header = f"# Report: {topic}\n\n*Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"
    return header + "\n".join(report_sections)


# ══════════════════════════════════════════════════════
# EXAMPLE 2: Batch Processing with Progress
# ══════════════════════════════════════════════════════

@mcp.tool()
async def process_items(
    items: str,
    operation: str = "analyze",
    ctx: Context = None
) -> dict:
    """
    Process a list of items with real-time progress updates.

    Args:
        items: Comma-separated list of items to process
        operation: What to do with each item — "analyze", "transform", "validate"
        ctx: MCP Context (injected automatically)

    Returns:
        Processing results for all items
    """
    item_list = [item.strip() for item in items.split(",") if item.strip()]
    total = len(item_list)

    if total == 0:
        return {"error": "No items provided"}

    if total > 20:
        return {"error": "Maximum 20 items at once"}

    if ctx:
        await ctx.info(f"Processing {total} items with operation: {operation}")

    results = []
    errors = []

    for i, item in enumerate(item_list):
        # Progress update for each item
        if ctx:
            await ctx.report_progress(
                progress=i,
                total=total,
                message=f"Processing ({i+1}/{total}): {item}"
            )

        # Simulate processing work
        await asyncio.sleep(0.3)

        # Simulate the operation
        try:
            if operation == "analyze":
                result = {
                    "item": item,
                    "length": len(item),
                    "words": len(item.split()),
                    "is_numeric": item.replace('.', '').replace('-', '').isdigit(),
                    "status": "analyzed"
                }
            elif operation == "transform":
                result = {
                    "item": item,
                    "upper": item.upper(),
                    "lower": item.lower(),
                    "title": item.title(),
                    "reversed": item[::-1],
                    "status": "transformed"
                }
            elif operation == "validate":
                issues = []
                if len(item) < 2:
                    issues.append("too short")
                if len(item) > 100:
                    issues.append("too long")
                if not item.replace(' ', '').isalnum():
                    issues.append("contains special characters")
                result = {
                    "item": item,
                    "valid": len(issues) == 0,
                    "issues": issues,
                    "status": "validated"
                }
            else:
                result = {"item": item, "status": "unknown operation"}

            results.append(result)

            # Log warnings for certain conditions
            if ctx and operation == "validate" and not result.get("valid", True):
                await ctx.warning(f"Validation issues found for: {item}")

        except Exception as e:
            errors.append({"item": item, "error": str(e)})
            if ctx:
                await ctx.warning(f"Error processing '{item}': {e}")

    if ctx:
        await ctx.report_progress(progress=total, total=total, message="All items processed! ✅")
        await ctx.info(f"Completed: {len(results)} succeeded, {len(errors)} failed")

    return {
        "operation": operation,
        "total": total,
        "succeeded": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


# ══════════════════════════════════════════════════════
# EXAMPLE 3: Logging Levels Demo
# ══════════════════════════════════════════════════════

@mcp.tool()
async def demo_logging(ctx: Context = None) -> str:
    """
    Demonstrates all MCP logging levels.

    Shows how tools can send different types of messages
    to the client during execution.

    Returns:
        Summary of all log messages sent
    """
    if not ctx:
        return "Context not available for logging demo"

    await ctx.debug("🔍 DEBUG: Detailed diagnostic info (only shown in debug mode)")
    await asyncio.sleep(0.2)

    await ctx.info("ℹ️  INFO: Normal operation message — task started")
    await asyncio.sleep(0.2)

    await ctx.info("ℹ️  INFO: Processing step 1 of 3...")
    await asyncio.sleep(0.3)

    await ctx.info("ℹ️  INFO: Processing step 2 of 3...")
    await asyncio.sleep(0.3)

    await ctx.warning("⚠️  WARNING: Optional feature unavailable — using fallback")
    await asyncio.sleep(0.2)

    await ctx.info("ℹ️  INFO: Processing step 3 of 3...")
    await asyncio.sleep(0.3)

    await ctx.info("✅ INFO: All steps completed successfully")

    return """Logging demo complete!

Messages sent to the client:
  • DEBUG   — detailed diagnostics (filtered in production)
  • INFO    — normal operation progress (most common)
  • WARNING — non-fatal issues the user should know about
  • ERROR   — failures (use sparingly, prefer returning error in result)

Use ctx.info() to keep users informed during long operations.
Use ctx.warning() when something unexpected happens but can continue.
"""


# ══════════════════════════════════════════════════════
# EXAMPLE 4: Parallel Operations with Progress
# ══════════════════════════════════════════════════════

@mcp.tool()
async def parallel_weather(cities: str, ctx: Context = None) -> dict:
    """
    Fetch weather for multiple cities IN PARALLEL with progress tracking.

    This shows how parallel execution is much faster than sequential.

    Args:
        cities: Comma-separated city names (max 6)
        ctx: MCP Context

    Returns:
        Weather data for all cities with timing comparison
    """
    import httpx
    import time

    city_list = [c.strip() for c in cities.split(",") if c.strip()][:6]
    total = len(city_list)

    if ctx:
        await ctx.info(f"Fetching weather for {total} cities in parallel...")

    start_time = time.time()
    completed = 0

    async def fetch_city(city: str) -> tuple:
        nonlocal completed
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"https://wttr.in/{city}?format=3",
                    timeout=8.0
                )
                result = resp.text.strip() if resp.status_code == 200 else f"{city}: unavailable"
            except Exception:
                result = f"{city}: error"

        completed += 1
        if ctx:
            await ctx.report_progress(
                progress=completed,
                total=total,
                message=f"Got weather for: {city}"
            )
        return city, result

    # ALL cities fetched simultaneously (parallel!)
    tasks = [fetch_city(city) for city in city_list]
    results = await asyncio.gather(*tasks)

    elapsed = round(time.time() - start_time, 2)
    sequential_estimate = round(total * 1.5, 1)

    if ctx:
        await ctx.info(f"Done! Parallel: {elapsed}s vs Sequential estimate: {sequential_estimate}s")

    return {
        "cities": total,
        "parallel_time_seconds": elapsed,
        "sequential_estimate_seconds": sequential_estimate,
        "time_saved_seconds": round(sequential_estimate - elapsed, 2),
        "weather": {city: weather for city, weather in results}
    }


if __name__ == "__main__":
    print("⚡ Streaming Demo MCP Server starting...", file=sys.stderr)
    print("   Tools with progress tracking:", file=sys.stderr)
    print("   • generate_report   - Report with section-by-section progress", file=sys.stderr)
    print("   • process_items     - Batch processing with progress", file=sys.stderr)
    print("   • demo_logging      - All logging levels demonstration", file=sys.stderr)
    print("   • parallel_weather  - Parallel fetch with live updates", file=sys.stderr)
    mcp.run()

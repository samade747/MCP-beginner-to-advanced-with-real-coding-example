"""
examples/08_advanced_agents/secure_production_server.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Production-ready MCP server with full security hardening.

Security features demonstrated:
  ✅ Environment variable secrets (never hardcoded)
  ✅ Input validation & sanitization
  ✅ Rate limiting (per tool)
  ✅ Request size limits
  ✅ URL allowlist/blocklist
  ✅ Structured logging to stderr
  ✅ Graceful error handling
  ✅ Timeout protection

SETUP:
  cp .env.example .env
  # Edit .env with your values
  python secure_production_server.py
"""

import os
import sys
import re
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional
from pathlib import Path
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context

# ─── Load environment variables ────────────────────────────────────────────
load_dotenv()

# ─── Logging — ALWAYS to stderr for MCP servers ────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("secure-server")

# ─── Configuration from environment ────────────────────────────────────────
class Config:
    WEATHER_API_KEY: str    = os.getenv("WEATHER_API_KEY", "")
    MAX_TEXT_LENGTH: int    = int(os.getenv("MAX_TEXT_LENGTH", "5000"))
    MAX_URL_LENGTH: int     = int(os.getenv("MAX_URL_LENGTH", "2000"))
    REQUEST_TIMEOUT: int    = int(os.getenv("REQUEST_TIMEOUT", "15"))
    RATE_LIMIT_CALLS: int   = int(os.getenv("RATE_LIMIT_CALLS", "10"))
    RATE_LIMIT_WINDOW: int  = int(os.getenv("RATE_LIMIT_WINDOW", "60"))


config = Config()

# ─── Rate limiter ──────────────────────────────────────────────────────────
_rate_limit_store: dict = defaultdict(list)


def check_rate_limit(tool_name: str) -> tuple[bool, str]:
    """
    Check if a tool call is within rate limits.
    Returns (allowed: bool, message: str)
    """
    now = datetime.now()
    window_start = now - timedelta(seconds=config.RATE_LIMIT_WINDOW)

    # Clean old entries
    _rate_limit_store[tool_name] = [
        t for t in _rate_limit_store[tool_name] if t > window_start
    ]

    call_count = len(_rate_limit_store[tool_name])

    if call_count >= config.RATE_LIMIT_CALLS:
        wait_seconds = config.RATE_LIMIT_WINDOW - (now - _rate_limit_store[tool_name][0]).seconds
        return False, f"Rate limit: {config.RATE_LIMIT_CALLS} calls per {config.RATE_LIMIT_WINDOW}s. Wait {wait_seconds}s."

    _rate_limit_store[tool_name].append(now)
    return True, ""


# ─── Input validators ──────────────────────────────────────────────────────

def validate_text(value: str, max_length: Optional[int] = None) -> str:
    """Validate and sanitize a text string."""
    if not isinstance(value, str):
        raise ValueError(f"Expected text, got {type(value).__name__}")

    max_len = max_length or config.MAX_TEXT_LENGTH
    if len(value) > max_len:
        raise ValueError(f"Text too long: {len(value)} chars (maximum: {max_len})")

    return value.strip()


def validate_url(url: str) -> str:
    """Validate a URL for security."""
    url = url.strip()

    # Must be HTTPS
    if not url.startswith("https://"):
        raise ValueError("Only HTTPS URLs are allowed")

    # Length check
    if len(url) > config.MAX_URL_LENGTH:
        raise ValueError(f"URL too long (maximum {config.MAX_URL_LENGTH} characters)")

    # Block internal/dangerous addresses
    blocked_patterns = [
        r'localhost', r'127\.0\.0', r'0\.0\.0\.0', r'::1',
        r'169\.254\.', r'10\.', r'192\.168\.', r'172\.(1[6-9]|2\d|3[01])\.',
        r'file://', r'ftp://', r'javascript:',
    ]
    for pattern in blocked_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            raise ValueError(f"URL not allowed: blocked address pattern detected")

    return url


def validate_city_name(city: str) -> str:
    """Validate a city name."""
    city = city.strip()

    if len(city) < 2:
        raise ValueError("City name too short")

    if len(city) > 100:
        raise ValueError("City name too long")

    # Only allow letters, spaces, hyphens, apostrophes, commas
    if not re.match(r"^[a-zA-Z\s\-',\.]+$", city):
        raise ValueError("City name contains invalid characters")

    return city


# ─── MCP Server ────────────────────────────────────────────────────────────
mcp = FastMCP("secure-production-server")


@mcp.tool()
async def secure_weather(city: str, ctx: Context = None) -> str:
    """
    Get weather with full security validation.

    Demonstrates: rate limiting, input validation, timeout, error handling.

    Args:
        city: City name (validated for safety)

    Returns:
        Current weather or error message
    """
    # ─── Rate limit check ──────────────────────────────────────────
    allowed, msg = check_rate_limit("secure_weather")
    if not allowed:
        logger.warning(f"Rate limit hit for secure_weather")
        return f"⏳ {msg}"

    # ─── Input validation ──────────────────────────────────────────
    try:
        city = validate_city_name(city)
    except ValueError as e:
        logger.warning(f"Invalid city name: {e}")
        return f"Invalid city name: {e}"

    logger.info(f"Weather request for: {city}")
    if ctx:
        await ctx.info(f"Fetching weather for {city}...")

    # ─── Fetch with timeout ────────────────────────────────────────
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"https://wttr.in/{city}?format=3",
                timeout=config.REQUEST_TIMEOUT,
                headers={"User-Agent": "SecureMCP/1.0"}
            )
            resp.raise_for_status()
            result = resp.text.strip()
            logger.info(f"Weather fetched successfully for {city}")
            return result

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching weather for {city}")
            return f"Request timed out after {config.REQUEST_TIMEOUT}s"

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {city}")
            return f"Weather service error: HTTP {e.response.status_code}"

        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
            return f"Error: {str(e)}"


@mcp.tool()
async def secure_fetch(url: str, ctx: Context = None) -> str:
    """
    Securely fetch a webpage with full security validation.

    Demonstrates: URL validation, blocklists, response size limits.

    Args:
        url: URL to fetch (must be HTTPS, no internal addresses)

    Returns:
        Page content (limited to first 3000 chars)
    """
    # ─── Rate limit ────────────────────────────────────────────────
    allowed, msg = check_rate_limit("secure_fetch")
    if not allowed:
        return f"⏳ {msg}"

    # ─── Validate URL ──────────────────────────────────────────────
    try:
        url = validate_url(url)
    except ValueError as e:
        logger.warning(f"URL validation failed: {e} | URL: {url[:50]}")
        return f"URL not allowed: {e}"

    logger.info(f"Fetching URL: {url[:80]}")

    # ─── Fetch ─────────────────────────────────────────────────────
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                url,
                timeout=config.REQUEST_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": "SecureMCP/1.0"}
            )
            resp.raise_for_status()

            # Strip HTML tags
            content = re.sub('<[^<]+?>', ' ', resp.text)
            content = re.sub(r'\s+', ' ', content).strip()

            # Limit response size
            if len(content) > 3000:
                content = content[:3000] + "\n\n[... content truncated for safety ...]"

            logger.info(f"Fetched {len(content)} chars from {url[:50]}")
            return content

        except httpx.TimeoutException:
            return f"Request timed out after {config.REQUEST_TIMEOUT}s"
        except httpx.HTTPStatusError as e:
            return f"HTTP {e.response.status_code}: {url}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def secure_text_process(
    text: str,
    operation: str = "analyze",
    ctx: Context = None
) -> dict:
    """
    Process text securely with size limits and validation.

    Args:
        text: Text to process (max 5000 chars by default)
        operation: "analyze", "word_count", "sentences"

    Returns:
        Processing results
    """
    # ─── Rate limit ────────────────────────────────────────────────
    allowed, msg = check_rate_limit("secure_text_process")
    if not allowed:
        return {"error": msg}

    # ─── Validate input ────────────────────────────────────────────
    try:
        text = validate_text(text)
    except ValueError as e:
        return {"error": str(e)}

    # ─── Process ───────────────────────────────────────────────────
    words = text.split()
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

    return {
        "operation": operation,
        "word_count": len(words),
        "character_count": len(text),
        "sentence_count": len(sentences),
        "unique_words": len(set(w.lower() for w in words)),
        "avg_word_length": round(sum(len(w) for w in words) / len(words), 2) if words else 0,
    }


if __name__ == "__main__":
    logger.info("Secure Production MCP Server starting...")
    logger.info(f"Rate limit: {config.RATE_LIMIT_CALLS} calls/{config.RATE_LIMIT_WINDOW}s")
    logger.info(f"Max text: {config.MAX_TEXT_LENGTH} chars")
    mcp.run()

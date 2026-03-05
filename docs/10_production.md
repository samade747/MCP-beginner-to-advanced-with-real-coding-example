# 📖 Chapter 10: Building Production MCP Systems

This chapter covers everything you need to deploy a real, production-grade MCP system.

---

## 🏭 Production Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     PRODUCTION MCP SYSTEM                     │
│                                                              │
│  ┌──────────┐     ┌───────────┐     ┌──────────────────┐   │
│  │  Users   │────►│  Claude   │────►│   MCP Client     │   │
│  └──────────┘     │  (Host)   │     │   (Host manages) │   │
│                   └───────────┘     └────────┬─────────┘   │
│                                              │              │
│                          ┌───────────────────┼───────────┐  │
│                          │                   │           │  │
│                    ┌─────▼─────┐     ┌───────▼───┐  ┌───▼──┐│
│                    │ Weather   │     │  GitHub   │  │  DB  ││
│                    │  Server   │     │  Server   │  │Server││
│                    └─────┬─────┘     └───────┬───┘  └───┬──┘│
│                          │                   │           │  │
│                    ┌─────▼─────┐     ┌───────▼───┐  ┌───▼──┐│
│                    │  Weather  │     │  GitHub   │  │ SQL  ││
│                    │   API     │     │   API     │  │  DB  ││
│                    └───────────┘     └───────────┘  └──────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## 🐳 Docker Deployment

### Dockerfile for an MCP Server:

```dockerfile
# Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .
COPY tools/ ./tools/
COPY resources/ ./resources/

# Security: Don't run as root
RUN useradd -m mcpuser
USER mcpuser

# Environment variables (set at runtime, not build time!)
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD python -c "import mcp; print('OK')" || exit 1

# Run the MCP server
CMD ["python", "server.py"]
```

### docker-compose.yml for multi-server setup:

```yaml
# docker-compose.yml

version: '3.8'

services:
  # Weather MCP Server
  weather-mcp:
    build:
      context: ./servers/weather
      dockerfile: Dockerfile
    environment:
      - WEATHER_API_KEY=${WEATHER_API_KEY}
    restart: unless-stopped
    
  # GitHub MCP Server
  github-mcp:
    build:
      context: ./servers/github
      dockerfile: Dockerfile
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    restart: unless-stopped
    
  # Database MCP Server
  database-mcp:
    build:
      context: ./servers/database
      dockerfile: Dockerfile
    volumes:
      - db-data:/data
    environment:
      - DB_PATH=/data/app.db
    restart: unless-stopped

volumes:
  db-data:
```

---

## 🔒 Production Security Checklist

```python
# production_server.py - Security best practices

import os
import sys
import logging
from mcp.server.fastmcp import FastMCP

# ─── Logging setup ─────────────────────────────────────────────────────────
# IMPORTANT: Log to stderr, not stdout!
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("production-server")

mcp = FastMCP("production-server")


# ─── Input validation helpers ───────────────────────────────────────────────
def validate_string(value: str, max_length: int = 1000, allow_special: bool = False) -> str:
    """Validate and sanitize string inputs."""
    if not isinstance(value, str):
        raise ValueError(f"Expected string, got {type(value)}")
    
    if len(value) > max_length:
        raise ValueError(f"Input too long: {len(value)} chars (max {max_length})")
    
    if not allow_special:
        # Remove dangerous characters
        import re
        value = re.sub(r'[<>&;`$]', '', value)
    
    return value.strip()


def validate_positive_int(value: int, max_value: int = 1000) -> int:
    """Validate positive integer inputs."""
    if not isinstance(value, int):
        raise ValueError(f"Expected integer, got {type(value)}")
    if value < 0:
        raise ValueError(f"Value must be positive, got {value}")
    if value > max_value:
        raise ValueError(f"Value too large: {value} (max {max_value})")
    return value


# ─── Rate limiting (simple in-memory) ──────────────────────────────────────
from collections import defaultdict
from datetime import datetime, timedelta

_call_counts = defaultdict(list)

def check_rate_limit(tool_name: str, max_calls: int = 10, per_seconds: int = 60) -> bool:
    """Simple rate limiter. Returns True if allowed, False if rate limited."""
    now = datetime.now()
    cutoff = now - timedelta(seconds=per_seconds)
    
    # Clean old entries
    _call_counts[tool_name] = [t for t in _call_counts[tool_name] if t > cutoff]
    
    if len(_call_counts[tool_name]) >= max_calls:
        return False
    
    _call_counts[tool_name].append(now)
    return True


# ─── Production tool example ────────────────────────────────────────────────
@mcp.tool()
async def safe_web_fetch(url: str) -> str:
    """
    Safely fetch content from a URL with all security checks.
    
    Args:
        url: URL to fetch (must be https://)
    
    Returns:
        Page content (sanitized)
    """
    import httpx
    
    # Rate limit check
    if not check_rate_limit("safe_web_fetch", max_calls=5, per_seconds=60):
        return "Rate limit exceeded. Please wait before making more requests."
    
    # Input validation
    try:
        url = validate_string(url, max_length=2000, allow_special=True)
    except ValueError as e:
        return f"Invalid URL: {e}"
    
    # Security: Only allow HTTPS
    if not url.startswith("https://"):
        return "Security error: Only HTTPS URLs are allowed."
    
    # Block dangerous domains (example)
    blocked_domains = ["localhost", "127.0.0.1", "0.0.0.0", "internal"]
    if any(blocked in url for blocked in blocked_domains):
        return "Security error: Cannot access internal/local addresses."
    
    logger.info(f"Fetching URL: {url[:100]}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                timeout=10.0,
                follow_redirects=True,
                headers={"User-Agent": "MCP-Bot/1.0"}
            )
            
            # Limit response size
            content = response.text[:5000]
            
            logger.info(f"Fetched {len(content)} chars from {url[:50]}")
            return content
            
    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching {url[:50]}")
        return "Request timed out."
    except Exception as e:
        logger.error(f"Error fetching {url[:50]}: {e}")
        return f"Error: {str(e)}"


if __name__ == "__main__":
    logger.info("Starting production MCP server...")
    mcp.run()
```

---

## 📈 Performance Optimization

### Caching with TTL

```python
from functools import lru_cache
from datetime import datetime, timedelta
import asyncio

# Cache with time-to-live
_cache = {}

def cached(ttl_seconds: int = 300):
    """Decorator: cache tool results for ttl_seconds."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            if cache_key in _cache:
                result, expires_at = _cache[cache_key]
                if datetime.now() < expires_at:
                    return result  # Return cached result
            
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Store in cache
            _cache[cache_key] = (result, datetime.now() + timedelta(seconds=ttl_seconds))
            return result
        
        return wrapper
    return decorator


@mcp.tool()
@cached(ttl_seconds=300)  # Cache for 5 minutes
async def get_weather_cached(city: str) -> str:
    """Get weather with 5-minute caching."""
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://wttr.in/{city}?format=3", timeout=10)
        return resp.text.strip()
```

---

## 📋 Environment Configuration

```python
# config.py - Centralized configuration

import os
from dataclasses import dataclass

@dataclass
class Config:
    # Server settings
    server_name: str = "production-mcp"
    log_level: str = "INFO"
    
    # API Keys (loaded from environment)
    weather_api_key: str = ""
    github_token: str = ""
    openai_api_key: str = ""
    
    # Limits
    max_request_size: int = 10_000   # characters
    request_timeout: int = 30         # seconds
    rate_limit_per_minute: int = 60
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load config from environment variables."""
        return cls(
            server_name=os.getenv("MCP_SERVER_NAME", "production-mcp"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            weather_api_key=os.getenv("WEATHER_API_KEY", ""),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            max_request_size=int(os.getenv("MAX_REQUEST_SIZE", "10000")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT", "60")),
        )
    
    def validate(self):
        """Check required config values are set."""
        errors = []
        if not self.weather_api_key:
            errors.append("WEATHER_API_KEY is not set")
        if errors:
            raise ValueError(f"Config errors:\n" + "\n".join(errors))


# Load config globally
config = Config.from_env()
```

---

## 🚀 Deployment Checklist

### Before deploying to production:

**Security:**
- [ ] All secrets loaded from environment variables
- [ ] Input validation on all tool parameters
- [ ] Rate limiting implemented
- [ ] HTTPS only for external URLs
- [ ] Internal network access blocked

**Reliability:**
- [ ] Error handling on all tools (never crash)
- [ ] Timeouts on all HTTP requests
- [ ] Logging to stderr (not stdout)
- [ ] Health check endpoint

**Performance:**
- [ ] Caching for expensive operations
- [ ] Async/await for all I/O
- [ ] Response size limits

**Testing:**
- [ ] Unit tests for all tools
- [ ] Integration tests
- [ ] Test with Claude Desktop

---

## 🎯 Final Architecture: Complete Production System

```
┌─────────────────────────────────────────────────────────────────┐
│                      YOUR PRODUCTION SYSTEM                      │
│                                                                  │
│   User ──► Claude Desktop / Claude API                          │
│                    │                                             │
│              MCP Client Layer                                    │
│                    │                                             │
│   ┌────────────────┼──────────────────────┐                    │
│   │                │                      │                     │
│   ▼                ▼                      ▼                     │
│ ┌──────┐     ┌──────────┐           ┌──────────┐               │
│ │Cache │     │  Secure  │           │  Async   │               │
│ │Layer │────►│  Server  │◄─────────►│  Pool    │               │
│ └──────┘     └────┬─────┘           └──────────┘               │
│                   │                                              │
│         ┌─────────┼──────────┐                                  │
│         │         │          │                                   │
│         ▼         ▼          ▼                                   │
│      Weather   GitHub     Database                               │
│        API      API         DB                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎓 Congratulations!

You've completed the full MCP guide. You now know how to:

✅ Understand MCP architecture  
✅ Build MCP servers with tools, resources, and prompts  
✅ Connect to Claude AI (Desktop and API)  
✅ Use advanced patterns (streaming, composition, memory)  
✅ Deploy production-grade MCP systems  

### Your Next Steps:

1. **Build the 5 projects** in the `/projects` folder
2. **Share your MCP servers** — publish them for others to use
3. **Explore the ecosystem** — hundreds of MCP servers at https://github.com/modelcontextprotocol
4. **Join the community** — Discord, GitHub discussions

---

*Happy building! 🚀*

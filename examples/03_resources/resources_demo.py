"""
examples/03_resources/resources_demo.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Complete demo of MCP Resources.

Resources expose READ-ONLY structured data to Claude.
Unlike tools (which execute actions), resources are data sources.

Resource URI formats:
  docs://topic          - documentation
  db://table/data       - database records
  api://endpoint        - API data
  users://{id}/profile  - dynamic (parameterized) resources

TRY ASKING CLAUDE (after connecting via Claude Desktop):
  "What are the company policies?"
  "Show me the API reference"
  "What products do you have?"
  "Get the profile for user 42"
"""

import sys
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("resources-demo")


# ══════════════════════════════════════════════════════
# STATIC RESOURCES — fixed data that doesn't change
# ══════════════════════════════════════════════════════

@mcp.resource("docs://company/about")
def get_company_about() -> str:
    """
    Company information and overview.
    Claude reads this to answer questions about the company.
    """
    return """
    # TechCorp AI Solutions

    ## About Us
    TechCorp AI Solutions is a leading provider of AI-powered developer tools.
    Founded in 2020, we help developers build smarter applications faster.

    ## Mission
    To make AI accessible to every developer, regardless of experience level.

    ## Products
    - **DevAssist Pro** — AI coding assistant for VS Code and JetBrains
    - **DataBridge** — Connect any data source to your AI model
    - **AgentKit** — Framework for building production AI agents

    ## Team
    - CEO: Sarah Johnson
    - CTO: Ahmed Khan
    - Head of Product: Maria Chen
    - 150+ employees across San Francisco, London, and Karachi

    ## Contact
    - Website: https://techcorp.ai
    - Email: hello@techcorp.ai
    - Support: support@techcorp.ai
    """


@mcp.resource("docs://company/faq")
def get_faq() -> str:
    """Frequently asked questions about the company and products."""
    return """
    # Frequently Asked Questions

    ## Pricing
    Q: What are your pricing plans?
    A: We offer three plans:
       - Free: Up to 100 AI requests/month
       - Pro ($29/month): Unlimited requests, priority support
       - Enterprise: Custom pricing, dedicated support, SLA guarantee

    Q: Is there a free trial?
    A: Yes! All paid plans include a 14-day free trial. No credit card required.

    ## Technical
    Q: What programming languages do you support?
    A: Python, JavaScript/TypeScript, Go, Rust, Java, C#, Ruby

    Q: Do you support on-premise deployment?
    A: Yes, Enterprise plan includes on-premise and private cloud options.

    Q: What AI models do you use?
    A: We use Claude (Anthropic), GPT-4 (OpenAI), and support custom models.

    ## Support
    Q: How do I get help?
    A: Documentation at docs.techcorp.ai, email support@techcorp.ai,
       or join our Discord community at discord.techcorp.ai
    """


@mcp.resource("docs://api/reference")
def get_api_reference() -> str:
    """Complete API reference documentation."""
    return """
    # API Reference

    ## Base URL
    https://api.techcorp.ai/v1

    ## Authentication
    All requests require an API key in the header:
    Authorization: Bearer YOUR_API_KEY

    ## Endpoints

    ### POST /completions
    Generate AI completions.

    Request body:
    {
      "model": "devassist-pro",
      "prompt": "Your prompt here",
      "max_tokens": 1000,
      "temperature": 0.7
    }

    Response:
    {
      "id": "cmpl-abc123",
      "text": "Generated response...",
      "tokens_used": 150,
      "cost_usd": 0.003
    }

    ### GET /models
    List available models.

    ### POST /embeddings
    Generate text embeddings for semantic search.

    ## Rate Limits
    - Free: 10 requests/minute
    - Pro: 100 requests/minute
    - Enterprise: Custom limits

    ## Error Codes
    - 400: Bad Request (invalid parameters)
    - 401: Unauthorized (invalid API key)
    - 429: Rate Limited (too many requests)
    - 500: Server Error
    """


# ══════════════════════════════════════════════════════
# DYNAMIC RESOURCES — change based on URI parameters
# ══════════════════════════════════════════════════════

@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> dict:
    """
    Get profile for a specific user.
    URI: users://123/profile  →  user_id = "123"
    """
    # In production, query a real database here
    users = {
        "1":  {"id": "1",  "name": "Ahmed Khan",    "role": "Senior Developer", "team": "Backend",  "joined": "2022-03-15", "location": "Karachi"},
        "2":  {"id": "2",  "name": "Sarah Johnson",  "role": "CEO",             "team": "Executive","joined": "2020-01-01", "location": "San Francisco"},
        "3":  {"id": "3",  "name": "Maria Chen",     "role": "Product Manager", "team": "Product",  "joined": "2021-06-20", "location": "London"},
        "42": {"id": "42", "name": "Test User",      "role": "QA Engineer",     "team": "Quality",  "joined": "2023-09-01", "location": "Remote"},
    }

    if user_id in users:
        return users[user_id]
    else:
        return {"error": f"User {user_id} not found", "available_ids": list(users.keys())}


@mcp.resource("products://{category}/list")
def get_products_by_category(category: str) -> dict:
    """
    Get products in a specific category.
    URI: products://tools/list  →  category = "tools"
    """
    catalog = {
        "tools": [
            {"name": "DevAssist Pro", "price": 29.00, "type": "IDE Plugin"},
            {"name": "CodeReview AI", "price": 19.00, "type": "Code Review"},
            {"name": "DocWriter", "price": 15.00, "type": "Documentation"},
        ],
        "platforms": [
            {"name": "DataBridge", "price": 49.00, "type": "Data Platform"},
            {"name": "AgentKit", "price": 79.00, "type": "Agent Framework"},
        ],
        "services": [
            {"name": "API Access", "price": 29.00, "type": "API"},
            {"name": "Enterprise Support", "price": 299.00, "type": "Support"},
        ]
    }

    if category in catalog:
        return {
            "category": category,
            "products": catalog[category],
            "count": len(catalog[category])
        }
    else:
        return {
            "error": f"Category '{category}' not found",
            "available": list(catalog.keys())
        }


# ══════════════════════════════════════════════════════
# LIVE RESOURCES — fetched in real-time
# ══════════════════════════════════════════════════════

@mcp.resource("stats://server/status")
def get_server_status() -> dict:
    """
    Real-time server status (generated fresh each time).
    Claude reads this to answer questions about system health.
    """
    import random

    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "uptime_days": 47,
        "services": {
            "api": {"status": "up", "latency_ms": random.randint(20, 80)},
            "database": {"status": "up", "connections": random.randint(10, 50)},
            "ai_models": {"status": "up", "queue_depth": random.randint(0, 5)},
            "file_storage": {"status": "up", "used_percent": random.randint(30, 60)},
        },
        "metrics": {
            "requests_today": random.randint(50000, 150000),
            "active_users": random.randint(500, 2000),
            "error_rate_percent": round(random.uniform(0.01, 0.5), 3),
        }
    }


if __name__ == "__main__":
    print("📊 Resources Demo MCP Server starting...", file=sys.stderr)
    print("   Resources exposed:", file=sys.stderr)
    print("   • docs://company/about", file=sys.stderr)
    print("   • docs://company/faq", file=sys.stderr)
    print("   • docs://api/reference", file=sys.stderr)
    print("   • users://{id}/profile", file=sys.stderr)
    print("   • products://{category}/list", file=sys.stderr)
    print("   • stats://server/status", file=sys.stderr)
    mcp.run()

# 📖 Chapter 5: MCP Resources

Resources are how MCP servers expose **data** to AI models. Unlike tools (which execute actions), resources are **read-only data sources**.

---

## 📚 Resources vs Tools

| | Tools | Resources |
|--|-------|-----------|
| **Type** | Actions / Functions | Data / Documents |
| **Effect** | Can change things | Read-only |
| **Example** | `send_email()` | `emails://inbox` |
| **When used** | When AI needs to DO something | When AI needs to READ something |

---

## 🔗 Resource URIs

Resources are identified by URIs (like web URLs):

```
docs://user-manual          ← documentation
db://customers/active       ← database data
file://config.json          ← file contents
api://products/catalog      ← API data
git://repo/README.md        ← git repository
```

---

## 📝 Creating a Static Resource

```python
# resources/static_resource.py

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("resource-server")

@mcp.resource("docs://company-info")
def get_company_info() -> str:
    """
    Returns information about the company.
    The AI can read this to answer company-related questions.
    """
    return """
    Company: TechCorp Ltd
    Founded: 2020
    CEO: Sarah Johnson
    Products: AI Tools, Developer Platform
    Headquarters: San Francisco, CA
    Team Size: 150 employees
    
    Our Mission:
    We build tools that make developers more productive using AI.
    
    Contact:
    Email: hello@techcorp.com
    Website: https://techcorp.com
    """

@mcp.resource("docs://faq")
def get_faq() -> str:
    """Returns frequently asked questions."""
    return """
    Q: What is your pricing?
    A: We offer a free tier and paid plans starting at $10/month.
    
    Q: Do you offer a free trial?
    A: Yes! 14-day free trial, no credit card required.
    
    Q: What programming languages do you support?
    A: Python, JavaScript, TypeScript, Go, and Rust.
    """

if __name__ == "__main__":
    mcp.run()
```

---

## 🔄 Dynamic Resources (Template URIs)

Resources can be dynamic — the URI contains parameters:

```python
# resources/dynamic_resource.py

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dynamic-resource-server")

# ─── Template resource ─────────────────────────────────────────────────────
# The {user_id} part is a parameter — different URIs return different data
@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> dict:
    """
    Get profile data for a specific user.
    URI format: users://<user_id>/profile
    Example: users://123/profile
    """
    # In a real app, you'd query a database here
    users = {
        "123": {
            "id": "123",
            "name": "Ahmed Khan",
            "email": "ahmed@example.com",
            "role": "developer",
            "joined": "2023-01-15"
        },
        "456": {
            "id": "456",
            "name": "Fatima Ali",
            "email": "fatima@example.com",
            "role": "designer",
            "joined": "2023-03-20"
        }
    }
    
    if user_id in users:
        return users[user_id]
    else:
        return {"error": f"User {user_id} not found"}


@mcp.resource("products://{category}/list")
async def get_products_by_category(category: str) -> list:
    """
    Get all products in a specific category.
    URI: products://<category>/list
    """
    import httpx
    
    # Example: fetch from a real API
    async with httpx.AsyncClient() as client:
        try:
            # Using a free fake store API for demonstration
            response = await client.get(
                f"https://fakestoreapi.com/products/category/{category}",
                timeout=10.0
            )
            return response.json()
        except Exception:
            return [{"error": "Could not fetch products"}]


if __name__ == "__main__":
    mcp.run()
```

---

## 📊 Resource with Structured Data

```python
@mcp.resource("stats://system")
def get_system_stats() -> dict:
    """Current system statistics and health."""
    import psutil  # pip install psutil
    
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
            "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2)
        }
    }
```

---

## 💡 When to Use Resources vs Tools

Use **Resources** when:
- The data doesn't change based on user input
- You're providing context/background information  
- The AI needs reference data to answer questions

Use **Tools** when:
- You need to execute an action
- The result depends on user-provided parameters
- You're writing/changing data

---

## 📁 Code For This Chapter

[examples/03_resources/](../examples/03_resources/)

---

👉 **[Chapter 6: MCP Prompts →](06_prompts.md)**

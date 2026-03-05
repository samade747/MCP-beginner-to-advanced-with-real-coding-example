"""
projects/github_agent/github_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project 2: GitHub AI Assistant

Gives Claude the ability to interact with GitHub:
  • Read repositories, files, and code
  • List and create issues
  • Read pull requests
  • Search code across repos
  • Get commit history

SETUP:
  1. Get a GitHub Personal Access Token:
     → https://github.com/settings/tokens
     → Select scopes: repo, read:user

  2. Set environment variable:
     export GITHUB_TOKEN="ghp_your_token_here"

  3. Add to Claude Desktop config:
     {
       "mcpServers": {
         "github": {
           "command": "python",
           "args": ["/path/to/github_agent.py"],
           "env": { "GITHUB_TOKEN": "ghp_your_token_here" }
         }
       }
     }

TRY ASKING CLAUDE:
  "What repos do I have on GitHub?"
  "Show me the README for my project"
  "Create an issue in my-repo about the login bug"
  "What are the open issues in facebook/react?"
  "Show me the latest commits in my project"
"""

import os
import sys
import httpx
from typing import Optional
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("github-agent")

# ─── GitHub API config ─────────────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_API = "https://api.github.com"

if not GITHUB_TOKEN:
    print("⚠️  WARNING: GITHUB_TOKEN not set. Most tools will fail.", file=sys.stderr)
    print("   Set it: export GITHUB_TOKEN='ghp_your_token'", file=sys.stderr)


def get_headers() -> dict:
    """Get GitHub API headers with authentication."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MCP-GitHub-Agent/1.0"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


async def github_get(endpoint: str, params: dict = None) -> dict | list | None:
    """Make an authenticated GET request to GitHub API."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{GITHUB_API}{endpoint}",
                headers=get_headers(),
                params=params or {},
                timeout=15.0
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return {"error": "Not found", "status": 404}
            elif resp.status_code == 401:
                return {"error": "Unauthorized. Check your GITHUB_TOKEN.", "status": 401}
            else:
                return {"error": f"GitHub API error: HTTP {resp.status_code}", "status": resp.status_code}
        except Exception as e:
            return {"error": str(e)}


# ─── Repository Tools ──────────────────────────────────────────────────────

@mcp.tool()
async def list_my_repos(
    repo_type: str = "all",
    sort_by: str = "updated",
    limit: int = 20
) -> list:
    """
    List your GitHub repositories.

    Args:
        repo_type: "all", "owner" (yours only), "public", "private", "forks"
        sort_by: "updated", "created", "pushed", "full_name"
        limit: Number of repos to return (max 50)

    Returns:
        List of repositories with details
    """
    if not GITHUB_TOKEN:
        return [{"error": "GITHUB_TOKEN not set"}]

    data = await github_get(
        "/user/repos",
        params={"type": repo_type, "sort": sort_by, "per_page": min(limit, 50)}
    )

    if isinstance(data, list):
        return [
            {
                "name": r["name"],
                "full_name": r["full_name"],
                "description": r.get("description", ""),
                "language": r.get("language", ""),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "open_issues": r.get("open_issues_count", 0),
                "private": r.get("private", False),
                "url": r.get("html_url", ""),
                "updated_at": r.get("updated_at", "")[:10]
            }
            for r in data[:limit]
        ]
    return [data]  # Error case


@mcp.tool()
async def get_repo_info(owner: str, repo: str) -> dict:
    """
    Get detailed information about a specific repository.

    Args:
        owner: Repository owner (username or org name)
        repo: Repository name

    Returns:
        Detailed repository information
    """
    data = await github_get(f"/repos/{owner}/{repo}")

    if "error" in data:
        return data

    return {
        "name": data.get("name"),
        "full_name": data.get("full_name"),
        "description": data.get("description", "No description"),
        "language": data.get("language", ""),
        "languages_url": data.get("languages_url", ""),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "watchers": data.get("watchers_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "default_branch": data.get("default_branch", "main"),
        "created_at": data.get("created_at", "")[:10],
        "updated_at": data.get("updated_at", "")[:10],
        "license": data.get("license", {}).get("name", "None") if data.get("license") else "None",
        "topics": data.get("topics", []),
        "private": data.get("private", False),
        "url": data.get("html_url", ""),
        "clone_url": data.get("clone_url", ""),
    }


@mcp.tool()
async def read_file_from_repo(
    owner: str,
    repo: str,
    file_path: str,
    branch: str = "main"
) -> str:
    """
    Read the contents of a file from a GitHub repository.

    Args:
        owner: Repository owner
        repo: Repository name
        file_path: Path to the file (e.g. "README.md", "src/main.py")
        branch: Branch name (default: "main")

    Returns:
        File contents as text
    """
    import base64

    data = await github_get(
        f"/repos/{owner}/{repo}/contents/{file_path}",
        params={"ref": branch}
    )

    if "error" in data:
        return f"Error reading file: {data['error']}"

    if data.get("type") == "dir":
        # It's a directory — list contents instead
        files = [f"{item['type']}: {item['name']}" for item in data if isinstance(item, dict)]
        return f"'{file_path}' is a directory. Contents:\n" + "\n".join(files[:20])

    if data.get("encoding") == "base64" and data.get("content"):
        try:
            content = base64.b64decode(data["content"]).decode("utf-8")
            # Limit size
            if len(content) > 10000:
                content = content[:10000] + "\n\n[... file truncated at 10,000 chars ...]"
            return f"File: {owner}/{repo}/{file_path}\n{'─'*40}\n{content}"
        except UnicodeDecodeError:
            return f"'{file_path}' appears to be a binary file (cannot display as text)"

    return f"Could not read file content"


@mcp.tool()
async def list_repo_files(
    owner: str,
    repo: str,
    path: str = "",
    branch: str = "main"
) -> list:
    """
    List files and directories in a repository path.

    Args:
        owner: Repository owner
        repo: Repository name
        path: Directory path (default: root)
        branch: Branch name (default: main)

    Returns:
        List of files and directories
    """
    data = await github_get(
        f"/repos/{owner}/{repo}/contents/{path}",
        params={"ref": branch}
    )

    if isinstance(data, dict) and "error" in data:
        return [f"Error: {data['error']}"]

    if isinstance(data, list):
        result = []
        for item in sorted(data, key=lambda x: (x.get("type", ""), x.get("name", ""))):
            icon = "📁" if item.get("type") == "dir" else "📄"
            size = f" ({item.get('size', 0)} bytes)" if item.get("type") == "file" else ""
            result.append(f"{icon} {item.get('name', '')}{size}")
        return result

    return ["Unexpected response from GitHub API"]


# ─── Issues Tools ──────────────────────────────────────────────────────────

@mcp.tool()
async def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 15
) -> list:
    """
    List issues in a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        state: "open", "closed", or "all"
        limit: Maximum issues to return (default 15)

    Returns:
        List of issues with details
    """
    data = await github_get(
        f"/repos/{owner}/{repo}/issues",
        params={"state": state, "per_page": min(limit, 30)}
    )

    if isinstance(data, dict) and "error" in data:
        return [f"Error: {data['error']}"]

    if isinstance(data, list):
        return [
            {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "author": issue.get("user", {}).get("login"),
                "labels": [l.get("name") for l in issue.get("labels", [])],
                "comments": issue.get("comments", 0),
                "created_at": issue.get("created_at", "")[:10],
                "url": issue.get("html_url", "")
            }
            for issue in data[:limit]
            if not issue.get("pull_request")  # Exclude PRs from issues list
        ]

    return ["No issues found or error occurred"]


@mcp.tool()
async def create_issue(
    owner: str,
    repo: str,
    title: str,
    body: str = "",
    labels: str = ""
) -> dict:
    """
    Create a new issue in a repository.

    Requires GITHUB_TOKEN with write access to the repo.

    Args:
        owner: Repository owner
        repo: Repository name
        title: Issue title
        body: Issue description (supports Markdown)
        labels: Comma-separated label names (e.g. "bug,high-priority")

    Returns:
        Created issue details
    """
    if not GITHUB_TOKEN:
        return {"error": "GITHUB_TOKEN not set. Cannot create issues."}

    label_list = [l.strip() for l in labels.split(",") if l.strip()] if labels else []

    payload = {"title": title, "body": body}
    if label_list:
        payload["labels"] = label_list

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{GITHUB_API}/repos/{owner}/{repo}/issues",
                headers=get_headers(),
                json=payload,
                timeout=15.0
            )

            if resp.status_code == 201:
                data = resp.json()
                return {
                    "success": True,
                    "issue_number": data.get("number"),
                    "title": data.get("title"),
                    "url": data.get("html_url"),
                    "message": f"Issue #{data.get('number')} created successfully!"
                }
            else:
                return {"error": f"Failed to create issue: HTTP {resp.status_code}", "details": resp.text[:200]}

        except Exception as e:
            return {"error": str(e)}


# ─── Commits Tools ─────────────────────────────────────────────────────────

@mcp.tool()
async def get_recent_commits(
    owner: str,
    repo: str,
    branch: str = "main",
    limit: int = 10
) -> list:
    """
    Get recent commit history for a repository.

    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch to get commits from (default: main)
        limit: Number of commits to return (default 10)

    Returns:
        List of recent commits with messages and authors
    """
    data = await github_get(
        f"/repos/{owner}/{repo}/commits",
        params={"sha": branch, "per_page": min(limit, 30)}
    )

    if isinstance(data, dict) and "error" in data:
        return [f"Error: {data['error']}"]

    if isinstance(data, list):
        return [
            {
                "sha": commit.get("sha", "")[:7],
                "message": commit.get("commit", {}).get("message", "").split("\n")[0][:80],
                "author": commit.get("commit", {}).get("author", {}).get("name", ""),
                "date": commit.get("commit", {}).get("author", {}).get("date", "")[:10],
                "url": commit.get("html_url", "")
            }
            for commit in data[:limit]
        ]

    return ["Could not fetch commits"]


if __name__ == "__main__":
    print("🐙 GitHub Agent MCP Server starting...", file=sys.stderr)
    if GITHUB_TOKEN:
        print("   ✅ GitHub token found", file=sys.stderr)
    else:
        print("   ❌ No GITHUB_TOKEN — set it for full functionality", file=sys.stderr)
    mcp.run()

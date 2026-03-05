# 🐙 GitHub Agent — MCP Project 2

Gives Claude the ability to read and interact with GitHub repositories.

## What It Does

| Tool | Description |
|------|-------------|
| `list_my_repos` | List all your repositories |
| `get_repo_info` | Detailed info about a repo |
| `read_file_from_repo` | Read any file from any repo |
| `list_repo_files` | Browse repository structure |
| `list_issues` | See open/closed issues |
| `create_issue` | Create a new issue |
| `get_recent_commits` | View commit history |

## Setup

### 1. Get a GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:user`
4. Copy the token

### 2. Set Environment Variable

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

### 3. Run

```bash
pip install mcp httpx
python github_agent.py
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["/path/to/github_agent.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

## Try These Prompts

- *"Show me all my GitHub repositories"*
- *"Read the README from my project"*
- *"What are the open issues in facebook/react?"*
- *"Create an issue in my-repo: 'Fix login bug'"*
- *"Show me the last 10 commits in my project"*
- *"What files are in the src/ folder of my-repo?"*

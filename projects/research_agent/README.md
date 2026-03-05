# 🔬 Research Agent — MCP Project 3

Wikipedia-powered research assistant.

## What It Does

| Tool | Description |
|------|-------------|
| `search_wikipedia` | Search and summarize Wikipedia articles |
| `get_related_topics` | Find related topics to explore |
| `extract_key_facts` | Pull key facts from an article |
| `create_research_summary` | Full research report on any topic |

## Setup

```bash
pip install mcp httpx
python research_agent.py
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "research": {
      "command": "python",
      "args": ["/path/to/research_agent.py"]
    }
  }
}
```

## Try These Prompts

- *"Research the history of Python programming language"*
- *"What are the key facts about machine learning?"*
- *"Create a research summary on quantum computing"*
- *"What topics are related to artificial intelligence?"*

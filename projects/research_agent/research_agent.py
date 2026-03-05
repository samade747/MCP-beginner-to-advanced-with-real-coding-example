"""
projects/research_agent/research_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project 3: AI Research Agent

Capabilities:
  • Wikipedia search and summary
  • Topic exploration with related articles
  • Key fact extraction
  • Citation generation

TRY ASKING CLAUDE:
  "Research the history of Python programming language"
  "What are the key facts about quantum computing?"
  "Summarize what Wikipedia says about MCP"
"""

import sys
import re
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("research-agent")


def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.sub('<[^<]+?>', '', text)
    clean = re.sub(r'\n\s*\n', '\n\n', clean)
    return clean.strip()


@mcp.tool()
async def search_wikipedia(topic: str, sentences: int = 5) -> dict:
    """
    Search Wikipedia for information about any topic.

    Args:
        topic: Topic to search (e.g. "Python programming", "Machine Learning")
        sentences: Number of sentences for the summary (1-10, default 5)

    Returns:
        Wikipedia article summary with key information
    """
    sentences = max(1, min(10, sentences))

    async with httpx.AsyncClient() as client:
        # Step 1: Search for the topic
        search_resp = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": topic,
                "srlimit": 3,
                "format": "json"
            },
            timeout=10.0
        )
        search_data = search_resp.json()
        search_results = search_data.get("query", {}).get("search", [])

        if not search_results:
            return {"error": f"No Wikipedia results found for '{topic}'"}

        # Step 2: Get the best matching article
        page_title = search_results[0]["title"]

        # Step 3: Get article extract
        extract_resp = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "titles": page_title,
                "prop": "extracts",
                "exintro": 1,
                "exsentences": sentences,
                "explaintext": 1,
                "format": "json"
            },
            timeout=10.0
        )
        extract_data = extract_resp.json()
        pages = extract_data.get("query", {}).get("pages", {})
        page = list(pages.values())[0]

        if "extract" not in page:
            return {"error": f"Could not get article content for '{topic}'"}

        return {
            "topic": topic,
            "title": page_title,
            "summary": page["extract"],
            "url": f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}",
            "other_results": [r["title"] for r in search_results[1:3]]
        }


@mcp.tool()
async def get_related_topics(topic: str, max_links: int = 10) -> dict:
    """
    Find topics related to a subject via Wikipedia links.

    Args:
        topic: Main topic to explore
        max_links: Maximum related topics to return (default 10)

    Returns:
        List of related topics and subtopics
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "titles": topic,
                "prop": "links",
                "pllimit": max_links,
                "format": "json"
            },
            timeout=10.0
        )
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        page = list(pages.values())[0]

        links = page.get("links", [])
        related = [link["title"] for link in links if not link["title"].startswith("Wikipedia:")]

        return {
            "topic": topic,
            "related_topics": related[:max_links],
            "count": len(related)
        }


@mcp.tool()
async def extract_key_facts(topic: str) -> dict:
    """
    Extract key facts and bullet points from a Wikipedia article.

    Args:
        topic: Topic to extract facts from

    Returns:
        List of key facts about the topic
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "titles": topic,
                "prop": "extracts",
                "exintro": 1,
                "explaintext": 1,
                "format": "json"
            },
            timeout=10.0
        )
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        page = list(pages.values())[0]

        if "extract" not in page:
            return {"error": f"No article found for '{topic}'"}

        text = page["extract"]
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 40]

        # Select the most informative sentences (contains numbers, dates, names)
        key_facts = []
        for s in sentences:
            if any([
                any(char.isdigit() for char in s),   # Contains numbers
                any(word[0].isupper() for word in s.split()[1:] if word),  # Named entities
                len(s) > 60                           # Long, detailed sentences
            ]):
                key_facts.append(s + ".")

        return {
            "topic": page.get("title", topic),
            "facts": key_facts[:8],  # Top 8 key facts
            "source": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
        }


@mcp.tool()
async def create_research_summary(topic: str) -> str:
    """
    Create a comprehensive research summary combining multiple Wikipedia sources.

    Args:
        topic: Topic to research thoroughly

    Returns:
        Formatted research report with overview, facts, and related topics
    """
    import asyncio

    # Gather all information in parallel
    wiki_task = search_wikipedia(topic, sentences=8)
    facts_task = extract_key_facts(topic)
    related_task = get_related_topics(topic, max_links=8)

    wiki, facts, related = await asyncio.gather(wiki_task, facts_task, related_task)

    # Build the report
    lines = [
        f"# Research Report: {topic}",
        "",
        "## Overview",
        wiki.get("summary", "No summary available."),
        "",
        "## Key Facts",
    ]

    for i, fact in enumerate(facts.get("facts", [])[:6], 1):
        lines.append(f"{i}. {fact}")

    lines.extend([
        "",
        "## Related Topics",
        ", ".join(related.get("related_topics", [])[:8]),
        "",
        f"## Sources",
        f"• Wikipedia: {wiki.get('url', '')}",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    print("🔬 Research Agent MCP Server starting...", file=sys.stderr)
    mcp.run()

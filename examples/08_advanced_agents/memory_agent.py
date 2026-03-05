"""
examples/08_advanced_agents/memory_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Advanced: MCP server with persistent memory using SQLite.

This server gives Claude a real memory that:
  ✅ Persists across conversations
  ✅ Organizes memories by category
  ✅ Supports fuzzy search
  ✅ Tracks when things were remembered
  ✅ Allows updating and forgetting

TRY ASKING CLAUDE:
  "Remember that my favorite language is Python"
  "Remember my project deadline is March 15"
  "What do you remember about my projects?"
  "Forget my favorite language"
  "What have you learned about me?"
"""

import sys
import json
import asyncio
import aiosqlite
from pathlib import Path
from datetime import datetime
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("memory-agent")

# ─── Persistent storage location ───────────────────────────────────────────
MEMORY_DB = Path.home() / "mcp-workspace" / "memory.db"
MEMORY_DB.parent.mkdir(parents=True, exist_ok=True)


# ─── Database setup ────────────────────────────────────────────────────────
async def init_db():
    """Create the memories table if it doesn't exist."""
    async with aiosqlite.connect(MEMORY_DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                key         TEXT UNIQUE NOT NULL,
                value       TEXT NOT NULL,
                category    TEXT DEFAULT 'general',
                importance  INTEGER DEFAULT 5,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        """)
        await db.commit()


# Initialize on startup
asyncio.get_event_loop().run_until_complete(init_db())


# ─── Memory Tools ──────────────────────────────────────────────────────────

@mcp.tool()
async def remember(
    key: str,
    value: str,
    category: str = "general",
    importance: int = 5
) -> str:
    """
    Store a piece of information in long-term memory.

    Use this when the user shares something they want remembered,
    or when important context should be retained for future conversations.

    Args:
        key: A unique identifier for this memory (e.g. "favorite_language", "project_deadline")
        value: The information to remember
        category: Organize memories by category:
                  "personal" — about the user
                  "projects" — project-related info
                  "preferences" — user preferences
                  "tasks" — to-dos and deadlines
                  "facts" — general facts
                  "general" — everything else
        importance: How important is this? 1 (low) to 10 (critical), default 5

    Returns:
        Confirmation that the memory was stored
    """
    now = datetime.now().isoformat()

    async with aiosqlite.connect(MEMORY_DB) as db:
        # INSERT OR REPLACE — update if key already exists
        await db.execute("""
            INSERT INTO memories (key, value, category, importance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                category = excluded.category,
                importance = excluded.importance,
                updated_at = excluded.updated_at
        """, (key, value, category, importance, now, now))
        await db.commit()

    return f"✅ Remembered: [{category}] {key} = {value}"


@mcp.tool()
async def recall(key: str) -> str:
    """
    Retrieve a specific memory by its key.

    Args:
        key: The key of the memory to retrieve

    Returns:
        The stored memory value, or a message if not found
    """
    async with aiosqlite.connect(MEMORY_DB) as db:
        # Update access count
        await db.execute(
            "UPDATE memories SET access_count = access_count + 1 WHERE key = ?",
            (key,)
        )
        await db.commit()

        async with db.execute(
            "SELECT key, value, category, importance, created_at, updated_at FROM memories WHERE key = ?",
            (key,)
        ) as cursor:
            row = await cursor.fetchone()

    if row:
        key, value, category, importance, created_at, updated_at = row
        return (
            f"📝 Memory: {key}\n"
            f"   Value: {value}\n"
            f"   Category: {category} | Importance: {importance}/10\n"
            f"   Stored: {created_at[:10]}"
        )
    else:
        return f"No memory found with key '{key}'"


@mcp.tool()
async def search_memories(
    query: str,
    category: Optional[str] = None
) -> list:
    """
    Search through all memories for relevant information.

    Args:
        query: Text to search for (searches keys and values)
        category: Optional category to filter by

    Returns:
        List of matching memories
    """
    async with aiosqlite.connect(MEMORY_DB) as db:
        if category:
            async with db.execute(
                """SELECT key, value, category, importance
                   FROM memories
                   WHERE category = ? AND (key LIKE ? OR value LIKE ?)
                   ORDER BY importance DESC, updated_at DESC
                   LIMIT 10""",
                (category, f"%{query}%", f"%{query}%")
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute(
                """SELECT key, value, category, importance
                   FROM memories
                   WHERE key LIKE ? OR value LIKE ?
                   ORDER BY importance DESC, updated_at DESC
                   LIMIT 10""",
                (f"%{query}%", f"%{query}%")
            ) as cursor:
                rows = await cursor.fetchall()

    if not rows:
        return [f"No memories found matching '{query}'"]

    return [
        f"[{cat}] {key}: {value} (importance: {imp}/10)"
        for key, value, cat, imp in rows
    ]


@mcp.tool()
async def list_memories(
    category: Optional[str] = None,
    min_importance: int = 1
) -> dict:
    """
    List all memories, optionally filtered by category or importance.

    Args:
        category: Optional category to filter by
        min_importance: Only show memories with importance >= this value (default 1 = show all)

    Returns:
        Organized list of all matching memories
    """
    async with aiosqlite.connect(MEMORY_DB) as db:
        if category:
            async with db.execute(
                """SELECT key, value, category, importance, updated_at
                   FROM memories
                   WHERE category = ? AND importance >= ?
                   ORDER BY importance DESC, key ASC""",
                (category, min_importance)
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute(
                """SELECT key, value, category, importance, updated_at
                   FROM memories
                   WHERE importance >= ?
                   ORDER BY category ASC, importance DESC, key ASC""",
                (min_importance,)
            ) as cursor:
                rows = await cursor.fetchall()

    if not rows:
        return {"message": "No memories stored yet", "total": 0}

    # Group by category
    by_category = {}
    for key, value, cat, importance, updated_at in rows:
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append({
            "key": key,
            "value": value,
            "importance": importance,
            "last_updated": updated_at[:10]
        })

    return {
        "total": len(rows),
        "categories": list(by_category.keys()),
        "memories": by_category
    }


@mcp.tool()
async def forget(key: str) -> str:
    """
    Delete a specific memory.

    Args:
        key: The key of the memory to delete

    Returns:
        Confirmation of deletion
    """
    async with aiosqlite.connect(MEMORY_DB) as db:
        cursor = await db.execute("DELETE FROM memories WHERE key = ?", (key,))
        await db.commit()
        deleted = cursor.rowcount

    if deleted > 0:
        return f"🗑️  Forgotten: '{key}'"
    else:
        return f"No memory found with key '{key}'"


@mcp.tool()
async def forget_category(category: str) -> str:
    """
    Delete ALL memories in a specific category.

    Args:
        category: The category to clear (e.g. "tasks", "projects")

    Returns:
        Number of memories deleted
    """
    async with aiosqlite.connect(MEMORY_DB) as db:
        cursor = await db.execute("DELETE FROM memories WHERE category = ?", (category,))
        await db.commit()
        deleted = cursor.rowcount

    if deleted > 0:
        return f"🗑️  Cleared {deleted} memories from category '{category}'"
    else:
        return f"No memories found in category '{category}'"


@mcp.tool()
async def memory_summary() -> str:
    """
    Get a summary of everything stored in memory.
    Use this to give Claude context about what it knows about the user.

    Returns:
        Formatted summary of all stored memories
    """
    async with aiosqlite.connect(MEMORY_DB) as db:
        async with db.execute(
            "SELECT COUNT(*), category FROM memories GROUP BY category ORDER BY COUNT(*) DESC"
        ) as cursor:
            category_counts = await cursor.fetchall()

        async with db.execute(
            "SELECT key, value, category FROM memories ORDER BY importance DESC LIMIT 20"
        ) as cursor:
            top_memories = await cursor.fetchall()

    if not top_memories:
        return "No memories stored yet. Use remember() to start building memory."

    lines = ["🧠 Memory Summary\n" + "─"*40]

    lines.append("\nCategories:")
    for count, category in category_counts:
        lines.append(f"  {category}: {count} memories")

    lines.append("\nTop Memories:")
    for key, value, category in top_memories:
        lines.append(f"  [{category}] {key}: {value}")

    return "\n".join(lines)


if __name__ == "__main__":
    print("🧠 Memory Agent MCP Server starting...", file=sys.stderr)
    print(f"   Storage: {MEMORY_DB}", file=sys.stderr)
    mcp.run()

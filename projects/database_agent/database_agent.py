"""
projects/database_agent/database_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project 5: SQLite Database Agent

Gives Claude the ability to:
  • Create and manage SQLite databases
  • Run SQL queries
  • Explore database structure
  • Insert, update, delete records
  • Generate data summaries

SETUP:
  pip install aiosqlite mcp

RUN:
  python database_agent.py

TRY ASKING CLAUDE:
  "Create a database for my bookstore"
  "Add 5 books to the database"
  "Show me all books that cost under $20"
  "How many books do we have in total?"
  "Update the price of Python Programming to $35"
"""

import sys
import os
import json
import asyncio
import aiosqlite
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("database-agent")

# ─── Database location ─────────────────────────────────────────────────────
DB_DIR = Path.home() / "mcp-workspace" / "databases"
DB_DIR.mkdir(parents=True, exist_ok=True)

print(f"[database] DB folder: {DB_DIR}", file=sys.stderr)

# Track currently active database
_current_db: Optional[str] = None


def get_db_path(db_name: str) -> Path:
    """Get the full path for a database file."""
    if not db_name.endswith(".db"):
        db_name += ".db"
    return DB_DIR / db_name


# ─── Database Management Tools ─────────────────────────────────────────────

@mcp.tool()
async def create_database(db_name: str) -> str:
    """
    Create a new SQLite database.

    Args:
        db_name: Name for the database (e.g. "bookstore", "inventory")

    Returns:
        Confirmation with the database location
    """
    global _current_db
    db_path = get_db_path(db_name)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("SELECT 1")  # Test connection

    _current_db = str(db_path)
    return f"✅ Database '{db_name}' created at: {db_path}"


@mcp.tool()
def list_databases() -> list:
    """
    List all available databases.

    Returns:
        List of database names
    """
    dbs = []
    for f in DB_DIR.glob("*.db"):
        size = f.stat().st_size
        dbs.append({
            "name": f.stem,
            "filename": f.name,
            "size_bytes": size,
            "size_human": f"{size/1024:.1f} KB" if size > 1024 else f"{size} B",
            "active": str(f) == _current_db
        })
    return dbs if dbs else [{"message": "No databases found. Use create_database() first."}]


@mcp.tool()
async def use_database(db_name: str) -> str:
    """
    Switch to using a specific database.

    Args:
        db_name: Name of the database to switch to

    Returns:
        Confirmation message
    """
    global _current_db
    db_path = get_db_path(db_name)

    if not db_path.exists():
        return f"Database '{db_name}' does not exist. Use create_database() first."

    _current_db = str(db_path)
    return f"✅ Now using database: {db_name}"


@mcp.tool()
async def create_table(
    db_name: str,
    table_name: str,
    columns: str
) -> str:
    """
    Create a new table in a database.

    Args:
        db_name: Database to create the table in
        table_name: Name for the new table
        columns: Column definitions as SQL.
                 Example: "id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL, quantity INTEGER"

    Returns:
        Success or error message
    """
    db_path = get_db_path(db_name)

    if not db_path.exists():
        return f"Database '{db_name}' not found. Create it first with create_database()."

    sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"

    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(sql)
            await db.commit()

        return f"✅ Table '{table_name}' created in '{db_name}'"

    except Exception as e:
        return f"Error creating table: {e}\nSQL attempted: {sql}"


@mcp.tool()
async def run_query(db_name: str, sql: str) -> dict:
    """
    Execute a SQL query on a database.

    Use this for SELECT queries to retrieve data.

    Args:
        db_name: Database to query
        sql: SQL SELECT statement
             Examples:
             "SELECT * FROM books"
             "SELECT name, price FROM books WHERE price < 20"
             "SELECT COUNT(*) as total FROM books"
             "SELECT * FROM books ORDER BY price DESC LIMIT 5"

    Returns:
        Query results with column names and rows
    """
    db_path = get_db_path(db_name)

    if not db_path.exists():
        return {"error": f"Database '{db_name}' not found."}

    # Safety: only allow SELECT queries through this tool
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT") and not sql_stripped.startswith("WITH"):
        return {
            "error": "This tool only runs SELECT queries. Use insert_record(), update_records(), or delete_records() for changes."
        }

    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql) as cursor:
                rows = await cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []

                results = [dict(row) for row in rows]

                return {
                    "success": True,
                    "query": sql,
                    "columns": columns,
                    "row_count": len(results),
                    "rows": results[:100]  # Limit to 100 rows
                }

    except Exception as e:
        return {"error": str(e), "query": sql}


@mcp.tool()
async def insert_record(db_name: str, table_name: str, data: str) -> str:
    """
    Insert a new record into a table.

    Args:
        db_name: Database name
        table_name: Table to insert into
        data: JSON string of column-value pairs.
              Example: '{"name": "Python Basics", "price": 29.99, "quantity": 100}'

    Returns:
        Success message with the new record's ID
    """
    db_path = get_db_path(db_name)

    if not db_path.exists():
        return f"Database '{db_name}' not found."

    try:
        record = json.loads(data)
    except json.JSONDecodeError as e:
        return f"Invalid JSON data: {e}\nExample format: '{{\"name\": \"value\", \"price\": 9.99}}'"

    columns = ", ".join(record.keys())
    placeholders = ", ".join(["?" for _ in record])
    values = list(record.values())

    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute(sql, values)
            await db.commit()
            new_id = cursor.lastrowid

        return f"✅ Record inserted into '{table_name}' with ID: {new_id}"

    except Exception as e:
        return f"Error inserting record: {e}"


@mcp.tool()
async def insert_many_records(db_name: str, table_name: str, records: str) -> str:
    """
    Insert multiple records at once (faster than inserting one by one).

    Args:
        db_name: Database name
        table_name: Table to insert into
        records: JSON array of records.
                 Example: '[{"name": "Book 1", "price": 15}, {"name": "Book 2", "price": 25}]'

    Returns:
        Number of records inserted
    """
    db_path = get_db_path(db_name)

    if not db_path.exists():
        return f"Database '{db_name}' not found."

    try:
        record_list = json.loads(records)
        if not isinstance(record_list, list):
            return "Data must be a JSON array: [{...}, {...}]"
        if not record_list:
            return "No records to insert."
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    columns = ", ".join(record_list[0].keys())
    placeholders = ", ".join(["?" for _ in record_list[0]])
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    try:
        async with aiosqlite.connect(db_path) as db:
            for record in record_list:
                await db.execute(sql, list(record.values()))
            await db.commit()

        return f"✅ Successfully inserted {len(record_list)} records into '{table_name}'"

    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def get_table_schema(db_name: str, table_name: str) -> dict:
    """
    Show the structure (columns) of a table.

    Args:
        db_name: Database name
        table_name: Table to inspect

    Returns:
        Table structure with column names and types
    """
    db_path = get_db_path(db_name)

    if not db_path.exists():
        return {"error": f"Database '{db_name}' not found."}

    try:
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(f"PRAGMA table_info({table_name})") as cursor:
                columns = await cursor.fetchall()

            if not columns:
                return {"error": f"Table '{table_name}' not found."}

            return {
                "database": db_name,
                "table": table_name,
                "columns": [
                    {
                        "position": col[0],
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default": col[4],
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ]
            }

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def list_tables(db_name: str) -> list:
    """
    List all tables in a database.

    Args:
        db_name: Database name

    Returns:
        List of tables with row counts
    """
    db_path = get_db_path(db_name)

    if not db_path.exists():
        return [{"error": f"Database '{db_name}' not found."}]

    try:
        async with aiosqlite.connect(db_path) as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ) as cursor:
                tables = await cursor.fetchall()

            result = []
            for (table_name,) in tables:
                async with db.execute(f"SELECT COUNT(*) FROM {table_name}") as cur:
                    count = (await cur.fetchone())[0]
                result.append({"table": table_name, "row_count": count})

            return result if result else [{"message": f"No tables in '{db_name}'"}]

    except Exception as e:
        return [{"error": str(e)}]


if __name__ == "__main__":
    print("🗄️  Database Agent MCP Server starting...", file=sys.stderr)
    print(f"   DB location: {DB_DIR}", file=sys.stderr)
    mcp.run()

# 🗄️ Database Agent — MCP Project 5

Gives Claude full SQLite database capabilities.

## What It Does

| Tool | Description |
|------|-------------|
| `create_database` | Create a new SQLite database |
| `list_databases` | See all your databases |
| `use_database` | Switch active database |
| `create_table` | Create tables with custom schemas |
| `list_tables` | List tables with row counts |
| `get_table_schema` | View column structure |
| `run_query` | Execute SELECT queries |
| `insert_record` | Add a single record |
| `insert_many_records` | Bulk insert multiple records |

## Setup

```bash
pip install mcp aiosqlite
python database_agent.py
```

## Claude Desktop Config

```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["/path/to/database_agent.py"]
    }
  }
}
```

## Try These Prompts

- *"Create a database for my bookstore"*
- *"Create a books table with id, title, author, price, quantity"*
- *"Add 5 books to the database"*
- *"Show me all books that cost under $25"*
- *"How many books are in the database?"*
- *"Show me the top 3 most expensive books"*

# 📖 Chapter 2: MCP Architecture

Understanding how MCP works will make building with it much easier. This chapter explains the architecture visually.

---

## 🏗️ The Big Picture

MCP has **three main roles**: Host, Client, and Server.

```
┌─────────────────────────────────────────────────────────┐
│                        HOST                              │
│                 (e.g. Claude Desktop)                    │
│                                                          │
│    ┌──────────────┐         ┌──────────────┐            │
│    │  AI Model    │         │  MCP Client  │            │
│    │  (Claude)    │◄───────►│              │            │
│    └──────────────┘         └──────┬───────┘            │
│                                    │                     │
└────────────────────────────────────│─────────────────────┘
                                     │  JSON-RPC 2.0
                     ┌───────────────┼───────────────┐
                     │               │               │
              ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
              │  MCP Server │ │  MCP Server │ │  MCP Server │
              │  (Weather)  │ │  (GitHub)   │ │  (Database) │
              └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                     │               │               │
                  Weather         GitHub           SQL
                   API             API             DB
```

---

## 🎭 The Three Roles Explained

### 🖥️ Role 1: The HOST

The **Host** is the AI application — the thing the user interacts with.

**Examples:**
- Claude Desktop (Anthropic's desktop app)
- Cursor IDE (AI code editor)
- A custom chat app you build

**Responsibilities:**
- Manages the user interface
- Creates and manages MCP Clients
- Enforces security and user consent
- Passes results back to the AI model

### 🔌 Role 2: The MCP CLIENT

The **Client** lives inside the Host. It handles all communication with MCP Servers.

**Think of it as:** a translator between the AI and the tools

**Responsibilities:**
- Opens connections to MCP Servers
- Sends requests (e.g. "call this tool")
- Receives responses
- Manages the connection lifecycle

> ⚡ **Key insight:** One Host can have MANY Clients — one per MCP Server.

### 🔧 Role 3: The MCP SERVER

The **Server** is what YOU will build in this guide. It exposes tools, resources, and prompts.

**Responsibilities:**
- Registers available tools
- Executes tool requests
- Returns results
- Can be local (on your computer) or remote (on the internet)

---

## 📡 How They Communicate: JSON-RPC 2.0

MCP uses **JSON-RPC 2.0** as its communication format. This is a simple standard for sending requests and getting responses.

### Example: A Tool Call

**Step 1 — Client sends a request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {
      "city": "London"
    }
  }
}
```

**Step 2 — Server sends a response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "London: 18°C, partly cloudy"
      }
    ]
  }
}
```

You don't need to write this JSON manually — the MCP SDK handles it for you!

---

## 🔄 The MCP Lifecycle

Every time a Host connects to an MCP Server, this lifecycle happens:

```
CLIENT                              SERVER
  │                                   │
  │──── initialize ──────────────────►│
  │◄─── initialized ──────────────────│
  │                                   │
  │──── tools/list ──────────────────►│  "What tools do you have?"
  │◄─── [tool list] ──────────────────│  "Here are my tools: ..."
  │                                   │
  │──── tools/call ──────────────────►│  "Execute get_weather"
  │◄─── result ───────────────────────│  "Result: 18°C, cloudy"
  │                                   │
  │──── shutdown ────────────────────►│
  │                                   │
```

### Phase 1: Initialize
Client and Server introduce themselves and agree on capabilities.

### Phase 2: Discovery
Client asks the Server: "What tools/resources/prompts do you have?"

### Phase 3: Operation
The AI uses the discovered tools during conversations.

### Phase 4: Shutdown
Connection closes cleanly.

---

## 🚂 Transport: How Data Travels

MCP supports two transport methods:

### 📍 stdio (Standard Input/Output) — For LOCAL Servers

```
Claude Desktop
      │
      │  (launches as a subprocess)
      │
  Python process
  (your MCP server)
```

- Server runs as a child process on your machine
- Data flows through stdin/stdout
- **Best for:** Local tools, development, Claude Desktop integration

### 🌐 HTTP + SSE — For REMOTE Servers

```
User's Computer          Cloud Server
┌──────────────┐         ┌──────────────┐
│ Claude/Agent │◄───────►│  MCP Server  │
│              │  HTTP   │  (your API)  │
└──────────────┘         └──────────────┘
```

- Server runs as a web service
- Uses HTTP for requests, Server-Sent Events (SSE) for streaming
- **Best for:** Shared tools, production systems, multi-user scenarios

---

## 🔐 Security Architecture

MCP has security built into its design:

```
User
 │
 │  "Allow weather tool to access internet?" [Allow / Deny]
 │
Host (enforces consent)
 │
MCP Client (validates requests)
 │
MCP Server (only sees what it's given)
 │
External Tool
```

**Key security principles:**
1. **User Consent** — User must approve before tools run
2. **Isolation** — Each server only sees its own data
3. **No key sharing** — Servers don't get the user's API keys
4. **Least privilege** — Servers only get access they need

---

## 🧩 Putting It Together: A Real Request Flow

Here's exactly what happens when a user asks Claude "What's the weather in Karachi?":

```
1. USER types: "What's the weather in Karachi?"
        │
2. CLAUDE (AI) understands: I need the weather tool
        │
3. HOST sends a tool call request to the MCP CLIENT
        │
4. MCP CLIENT calls the MCP SERVER:
   → "Execute get_weather with city='Karachi'"
        │
5. MCP SERVER runs your Python function:
   → calls the weather API
   → gets back: "35°C, sunny"
        │
6. MCP SERVER returns result to CLIENT
        │
7. CLIENT returns to HOST → HOST gives to CLAUDE
        │
8. CLAUDE responds to USER:
   "The weather in Karachi is 35°C and sunny!"
```

---

## 📌 Key Takeaways

| Concept | Remember This |
|---------|--------------|
| Host | The AI app the user sees |
| Client | The connector inside the Host |
| Server | What YOU build (tools live here) |
| Transport | stdio for local, HTTP for remote |
| Protocol | JSON-RPC 2.0 messages |
| Security | User consent + isolation built-in |

---

👉 **[Chapter 3: Your First MCP Server →](03_first_server.md)**

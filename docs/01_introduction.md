# 📖 Chapter 1: Introduction to MCP

## What is Model Context Protocol (MCP)?

**Model Context Protocol (MCP)** is an open standard created by Anthropic that allows AI models like Claude to connect to external tools, data sources, and services in a safe, standardized way.

Before MCP, every AI integration was custom-built. After MCP, there is **one universal way** for AI to talk to any tool.

---

## 🔌 The "USB-C for AI" Analogy

Think of MCP like **USB-C** for computers:

| USB-C (Computers) | MCP (AI) |
|-------------------|----------|
| Universal port | Universal protocol |
| Connects any device | Connects any tool |
| One standard, many uses | One standard, many tools |
| Plug and play | Build once, use anywhere |

```
Without MCP:                    With MCP:

Claude ──→ Custom Slack code    Claude
Claude ──→ Custom GitHub code     │
Claude ──→ Custom DB code         ↓
Claude ──→ Custom File code      MCP
                                  │
                            ┌─────┼─────┐
                            ↓     ↓     ↓
                          Slack GitHub  DB
```

---

## 🌍 Real-World MCP Examples

Here is what MCP enables AI models to do:

| Without MCP | With MCP |
|-------------|----------|
| "I can't read files" | Claude reads your project files |
| "I don't know current news" | Claude searches the web |
| "I can't check your database" | Claude queries your database |
| "I can't send messages" | Claude sends Slack messages |

---

## 📅 History: Why Was MCP Created?

**The Problem (before 2024):**

Every company building AI products had to write custom "glue code" to connect AI to their tools. This meant:

- 🔴 Duplicated effort across thousands of companies
- 🔴 Incompatible integrations
- 🔴 Security risks (each custom integration was different)
- 🔴 Hard to maintain

**The Solution:**

Anthropic released MCP in **November 2024** as an open standard. Now:

- ✅ One standard that everyone uses
- ✅ Build a tool once → works with Claude, and any other MCP-compatible AI
- ✅ Security is built into the protocol
- ✅ Community builds shared tools

---

## 🏗️ The Three Things MCP Provides

MCP gives AI models access to three types of capabilities:

### 1️⃣ Tools (Actions)
Functions the AI can **execute**.

```
Examples:
• get_weather("London")       → returns weather data
• send_email(to, subject, body) → sends an email
• query_database(sql)         → runs SQL query
• search_web(query)           → searches internet
```

### 2️⃣ Resources (Data)
Structured data the AI can **read**.

```
Examples:
• docs://user-manual          → documentation text
• db://customers              → customer database
• file://report.pdf           → file contents
• api://product-catalog       → product list
```

### 3️⃣ Prompts (Templates)
Reusable **instructions** for the AI.

```
Examples:
• "Summarize this document in 3 bullet points"
• "Review this code for security issues"
• "Generate a professional email for this request"
```

---

## 🎯 Who Uses MCP?

MCP is already used by major AI companies and tools:

| Company/Tool | MCP Use |
|-------------|---------|
| **Anthropic Claude** | Native MCP support |
| **OpenAI** | MCP-compatible agents |
| **VS Code / Cursor** | MCP for coding assistants |
| **Zed Editor** | MCP server support |
| **Block (Square)** | Enterprise MCP usage |
| **Replit** | MCP in cloud IDE |

---

## 📋 What You Will Build in This Guide

By the end of this guide, you will have built:

1. **Hello World MCP Server** — understand the basics
2. **Weather Tool** — real API integration
3. **File Reader** — access files safely
4. **Multi-Tool Server** — combine multiple capabilities
5. **Claude Integration** — connect to real Claude AI
6. **Production Agent** — deploy a real AI agent

---

## ✅ Prerequisites

To follow this guide, you need:

- Python 3.10 or higher
- Basic Python knowledge (functions, classes, async/await)
- A computer (Windows, Mac, or Linux)
- Claude Desktop app (free) — for testing

**You do NOT need:**
- Prior AI experience
- Machine learning knowledge
- Cloud infrastructure

---

## 🚀 Let's Begin!

Ready to build? Move to the next chapter:

👉 **[Chapter 2: MCP Architecture →](02_architecture.md)**

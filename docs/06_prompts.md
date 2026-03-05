# 📖 Chapter 6: MCP Prompts

Prompts are **reusable message templates** that help AI models perform tasks consistently. They're like keyboard shortcuts for complex instructions.

---

## 🤔 Why Use Prompts?

Without prompts, every user has to write their own instructions:
```
User: "Please review this code, check for bugs, security issues, 
       performance problems, and style issues, and format your 
       response with sections for each type of issue..."
```

With an MCP prompt, the user just selects "code_review" and the full instruction is automatically provided.

---

## 📝 Creating Basic Prompts

```python
# prompts/basic_prompts.py

from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent

mcp = FastMCP("prompt-server")

# ─── Simple prompt ─────────────────────────────────────────────────────────
@mcp.prompt()
def summarize_text(text: str) -> str:
    """
    Create a prompt to summarize any text.
    
    Args:
        text: The text to summarize
    """
    return f"""Please summarize the following text in 3-5 bullet points.
Be concise and focus on the most important information.

TEXT TO SUMMARIZE:
{text}

FORMAT:
• Key point 1
• Key point 2
• Key point 3
(etc.)"""


# ─── Code review prompt ────────────────────────────────────────────────────
@mcp.prompt()
def code_review(code: str, language: str = "Python") -> str:
    """
    Professional code review prompt.
    
    Args:
        code: The code to review
        language: Programming language (default: Python)
    """
    return f"""You are a senior {language} developer doing a code review.

Please review the following {language} code and provide feedback in these sections:

## 1. Bugs & Errors
List any bugs, logic errors, or potential runtime errors.

## 2. Security Issues
Identify any security vulnerabilities or risks.

## 3. Performance
Note any performance improvements that could be made.

## 4. Code Style
Comment on readability, naming, and best practices.

## 5. Suggestions
Provide specific, actionable improvement suggestions.

CODE TO REVIEW:
```{language.lower()}
{code}
```

Be constructive and specific. Prioritize the most important issues."""


# ─── Email writing prompt ──────────────────────────────────────────────────
@mcp.prompt()
def write_email(
    recipient: str,
    subject: str,
    key_points: str,
    tone: str = "professional"
) -> str:
    """
    Write a professional email.
    
    Args:
        recipient: Who the email is to
        subject: Email subject line
        key_points: Main points to cover (comma-separated)
        tone: Tone of the email (professional, friendly, formal)
    """
    return f"""Write an email with the following details:

TO: {recipient}
SUBJECT: {subject}
TONE: {tone}
KEY POINTS TO COVER:
{key_points}

Guidelines:
- Keep it concise (under 200 words unless complex)
- Use {tone} language throughout
- Include a clear call-to-action if needed
- End with an appropriate sign-off

Write ONLY the email body (not a meta-description of the email)."""


if __name__ == "__main__":
    mcp.run()
```

---

## 🎯 Multi-Turn Conversation Prompts

For complex workflows, prompts can define entire conversations:

```python
from mcp.types import PromptMessage, TextContent, Role

@mcp.prompt()
def debug_session(error_message: str, code_context: str) -> list[PromptMessage]:
    """
    Start a debugging session for an error.
    
    Args:
        error_message: The error or exception message
        code_context: The code that caused the error
    """
    return [
        # System sets the context
        PromptMessage(
            role=Role.user,
            content=TextContent(
                type="text",
                text=f"""I'm debugging an error. Here's what happened:

ERROR MESSAGE:
{error_message}

CODE:
```python
{code_context}
```

Please help me understand and fix this error step by step."""
            )
        )
    ]
```

---

## 📁 Code

[examples/04_prompts/](../examples/04_prompts/)

---

👉 **[Chapter 7: MCP Client Features →](07_client_features.md)**

"""
examples/04_prompts/prompts_demo.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Complete demo of MCP Prompts.

Prompts are reusable message templates that give Claude
consistent, well-crafted instructions for common tasks.

Think of them as "keyboard shortcuts" for complex AI instructions.

HOW CLAUDE USES PROMPTS:
  1. User selects a prompt (e.g. "code_review")
  2. Claude fills in the parameters
  3. The full instruction is sent automatically
  4. Claude executes the task with perfect instructions every time

TRY IN CLAUDE DESKTOP:
  Click the "+" button → "Use a prompt" → select one
"""

import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("prompts-demo")


# ══════════════════════════════════════════════════════
# WRITING PROMPTS
# ══════════════════════════════════════════════════════

@mcp.prompt()
def summarize(
    text: str,
    style: str = "bullet_points",
    max_points: int = 5
) -> str:
    """
    Summarize any text in a specified style.

    Args:
        text: The text to summarize
        style: Format style — "bullet_points", "paragraph", "executive", "eli5"
        max_points: Max number of bullet points (for bullet_points style)
    """
    style_instructions = {
        "bullet_points": f"Format as {max_points} clear bullet points. Each bullet should be one complete idea.",
        "paragraph":     "Write a single coherent paragraph. Be concise but complete.",
        "executive":     "Write an executive summary: 1 sentence overview, 3 key points, 1 action item.",
        "eli5":          "Explain it like I'm 5 years old — simple words, relatable examples, no jargon.",
    }

    instruction = style_instructions.get(style, style_instructions["bullet_points"])

    return f"""Please summarize the following text.

STYLE: {instruction}

TEXT TO SUMMARIZE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Focus on the most important information. Be concise."""


@mcp.prompt()
def write_email(
    to: str,
    subject: str,
    key_points: str,
    tone: str = "professional",
    length: str = "medium"
) -> str:
    """
    Write a professional email with the perfect tone and structure.

    Args:
        to: Recipient name or role (e.g. "John", "the hiring manager")
        subject: Email subject line
        key_points: Main points to cover, one per line
        tone: "professional", "friendly", "formal", "urgent", "apologetic"
        length: "short" (under 100 words), "medium" (100-200), "long" (200+)
    """
    tone_guide = {
        "professional": "Clear, respectful, business-appropriate language",
        "friendly":     "Warm, conversational, personable but still professional",
        "formal":       "Formal language, no contractions, traditional structure",
        "urgent":       "Direct and concise, emphasize urgency without being rude",
        "apologetic":   "Sincere, take responsibility, focus on resolution",
    }

    length_guide = {
        "short":  "Under 100 words. Get straight to the point.",
        "medium": "100-200 words. Balanced detail.",
        "long":   "200-300 words. Include full context and details.",
    }

    return f"""Write a complete email with the following specifications:

TO: {to}
SUBJECT: {subject}
TONE: {tone_guide.get(tone, tone_guide['professional'])}
LENGTH: {length_guide.get(length, length_guide['medium'])}

KEY POINTS TO COVER:
{key_points}

REQUIREMENTS:
- Write ONLY the email body (no meta-commentary)
- Include appropriate greeting and sign-off
- Use the specified tone throughout
- Include a clear call-to-action if appropriate
- Do not write "Subject:" in the body"""


@mcp.prompt()
def write_blog_post(
    topic: str,
    audience: str = "general",
    word_count: int = 800,
    include_sections: str = "intro,main_points,conclusion"
) -> str:
    """
    Generate a complete, structured blog post.

    Args:
        topic: The blog post topic
        audience: Target audience — "general", "technical", "beginners", "experts"
        word_count: Approximate word count (default 800)
        include_sections: Comma-separated sections to include
    """
    audience_guide = {
        "general":    "Everyday language, relatable examples, no assumed knowledge",
        "technical":  "Technical accuracy, code examples where relevant, assumes programming knowledge",
        "beginners":  "Very simple language, step-by-step explanations, lots of examples",
        "experts":    "Deep technical detail, industry terminology, assume strong background knowledge",
    }

    return f"""Write a complete blog post with the following specifications:

TOPIC: {topic}
TARGET AUDIENCE: {audience_guide.get(audience, audience_guide['general'])}
APPROXIMATE LENGTH: {word_count} words
SECTIONS TO INCLUDE: {include_sections}

STRUCTURE:
1. Compelling headline (H1)
2. Hook — grab attention in the first 2 sentences
3. Main content with clear H2/H3 subheadings
4. Practical examples or takeaways
5. Strong conclusion with a call-to-action

STYLE GUIDELINES:
- Use short paragraphs (2-4 sentences max)
- Include transition sentences between sections
- Use active voice
- Make it scannable with headers and bold key points
- End with a memorable closing thought"""


# ══════════════════════════════════════════════════════
# CODE PROMPTS
# ══════════════════════════════════════════════════════

@mcp.prompt()
def code_review(
    code: str,
    language: str = "Python",
    focus: str = "all"
) -> str:
    """
    Perform a thorough, structured code review.

    Args:
        code: The code to review
        language: Programming language (Python, JavaScript, TypeScript, etc.)
        focus: Review focus — "all", "security", "performance", "style", "bugs"
    """
    focus_map = {
        "all":         "Bugs, security, performance, readability, and best practices",
        "security":    "Security vulnerabilities ONLY — injections, auth issues, data exposure, etc.",
        "performance": "Performance issues ONLY — complexity, memory, caching opportunities",
        "style":       "Code style ONLY — naming, structure, comments, readability",
        "bugs":        "Bugs and logic errors ONLY — runtime errors, edge cases, incorrect logic",
    }

    return f"""You are a senior {language} engineer performing a code review.

REVIEW FOCUS: {focus_map.get(focus, focus_map['all'])}

CODE TO REVIEW:
```{language.lower()}
{code}
```

REVIEW FORMAT:
## 🐛 Bugs & Logic Errors
[List any bugs, with line references and how to fix them]

## 🔒 Security Issues
[List security vulnerabilities and recommended fixes]

## ⚡ Performance
[List performance improvements with estimated impact]

## 📖 Readability & Style
[Naming, comments, structure improvements]

## ✅ What's Done Well
[Acknowledge good practices — always include positives]

## 🔧 Priority Fixes (Top 3)
[The 3 most important changes to make first]

Be specific. Reference line numbers where possible. Provide corrected code snippets for critical issues."""


@mcp.prompt()
def explain_code(
    code: str,
    language: str = "Python",
    level: str = "intermediate"
) -> str:
    """
    Explain what a piece of code does in plain language.

    Args:
        code: The code to explain
        language: Programming language
        level: Explanation level — "beginner", "intermediate", "expert"
    """
    level_guide = {
        "beginner":     "Assume no programming knowledge. Explain every concept. Use simple analogies.",
        "intermediate": "Assume basic programming knowledge. Explain the logic and patterns used.",
        "expert":       "Assume strong programming knowledge. Focus on architectural decisions and trade-offs.",
    }

    return f"""Explain the following {language} code.

AUDIENCE LEVEL: {level_guide.get(level, level_guide['intermediate'])}

CODE:
```{language.lower()}
{code}
```

EXPLANATION STRUCTURE:
1. **What this code does** (1-2 sentence overview)
2. **How it works** (step-by-step walkthrough)
3. **Key concepts used** (explain any important patterns/functions)
4. **Potential gotchas** (edge cases, limitations, or common mistakes)
5. **Example usage** (show how to use it with a concrete example)"""


@mcp.prompt()
def generate_tests(
    code: str,
    language: str = "Python",
    framework: str = "pytest"
) -> str:
    """
    Generate comprehensive unit tests for a function or class.

    Args:
        code: The code to write tests for
        language: Programming language
        framework: Test framework — "pytest", "unittest", "jest", "mocha"
    """
    return f"""Write comprehensive unit tests for the following {language} code.

TEST FRAMEWORK: {framework}

CODE TO TEST:
```{language.lower()}
{code}
```

GENERATE TESTS FOR:
1. ✅ Happy path — normal inputs that should succeed
2. 🔢 Edge cases — empty inputs, zeros, single items, large values
3. ❌ Error cases — invalid types, out of range, missing required args
4. 🔁 Boundary values — minimum/maximum allowed values

REQUIREMENTS:
- Use descriptive test names that explain what is being tested
- Each test should test ONE thing
- Include docstrings explaining what each test verifies
- Aim for 90%+ code coverage
- Group related tests in test classes"""


# ══════════════════════════════════════════════════════
# ANALYSIS PROMPTS
# ══════════════════════════════════════════════════════

@mcp.prompt()
def analyze_data(
    data: str,
    analysis_type: str = "summary",
    output_format: str = "report"
) -> str:
    """
    Analyze data and generate insights.

    Args:
        data: The data to analyze (CSV, JSON, or plain text table)
        analysis_type: "summary", "trends", "anomalies", "comparison", "forecast"
        output_format: "report", "bullet_points", "table", "narrative"
    """
    analysis_guide = {
        "summary":    "Provide descriptive statistics and key metrics",
        "trends":     "Identify patterns, trends, and changes over time",
        "anomalies":  "Find outliers, unusual values, and data quality issues",
        "comparison": "Compare different groups, categories, or time periods",
        "forecast":   "Predict future trends based on historical patterns",
    }

    return f"""Analyze the following data and provide insights.

ANALYSIS TYPE: {analysis_guide.get(analysis_type, analysis_guide['summary'])}
OUTPUT FORMAT: {output_format}

DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{data}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANALYSIS REQUIREMENTS:
1. Key findings (most important insights)
2. Statistical summary where applicable
3. Notable patterns or anomalies
4. Actionable recommendations based on the data
5. Limitations or caveats in the analysis

Be specific with numbers. Reference actual values from the data."""


@mcp.prompt()
def debug_error(
    error_message: str,
    code_context: str = "",
    language: str = "Python"
) -> str:
    """
    Help debug an error or exception with step-by-step guidance.

    Args:
        error_message: The error or exception message
        code_context: The code that caused the error (optional but helpful)
        language: Programming language
    """
    code_section = f"""
CODE THAT CAUSED THE ERROR:
```{language.lower()}
{code_context}
```""" if code_context else ""

    return f"""Help me debug this {language} error.

ERROR MESSAGE:
```
{error_message}
```
{code_section}

DEBUGGING GUIDE:
1. **Error Explanation** — What does this error mean in plain English?
2. **Root Cause** — What most likely caused this specific error?
3. **Step-by-Step Fix** — Exact steps to resolve it
4. **Code Fix** — Show the corrected code (if code was provided)
5. **Prevention** — How to avoid this error in the future

Be specific and practical. Show actual code fixes, not just abstract advice."""


if __name__ == "__main__":
    print("💬 Prompts Demo MCP Server starting...", file=sys.stderr)
    print("   Available prompts:", file=sys.stderr)
    print("   • summarize       - Summarize any text", file=sys.stderr)
    print("   • write_email     - Write professional emails", file=sys.stderr)
    print("   • write_blog_post - Generate blog posts", file=sys.stderr)
    print("   • code_review     - Review code for issues", file=sys.stderr)
    print("   • explain_code    - Explain what code does", file=sys.stderr)
    print("   • generate_tests  - Write unit tests", file=sys.stderr)
    print("   • analyze_data    - Analyze data and insights", file=sys.stderr)
    print("   • debug_error     - Debug errors step by step", file=sys.stderr)
    mcp.run()

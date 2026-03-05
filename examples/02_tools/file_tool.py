"""
examples/02_tools/file_tool.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Safe file system MCP server.

IMPORTANT SECURITY FEATURES:
  • All file operations are restricted to ~/mcp-workspace/
  • Path traversal attacks are blocked
  • No access to system files or parent directories

TRY ASKING CLAUDE:
  "List my files"
  "Create a file called notes.txt with my shopping list"
  "Read the contents of notes.txt"
  "Search my files for the word 'important'"
"""

import os
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("filesystem")

# ─── Safe workspace — all file access is restricted here ───────────────────
WORKSPACE = Path.home() / "mcp-workspace"
WORKSPACE.mkdir(exist_ok=True)

print(f"[filesystem] Workspace: {WORKSPACE}", file=sys.stderr)


def resolve_safe_path(filename: str) -> Path | None:
    """
    Resolve a filename to an absolute path within the safe workspace.
    Returns None if the path would escape the workspace (security check).
    """
    try:
        # Resolve the full absolute path
        target = (WORKSPACE / filename).resolve()

        # SECURITY: Check it's still inside the workspace
        target.relative_to(WORKSPACE.resolve())

        return target
    except ValueError:
        # Path tried to escape the workspace!
        return None


@mcp.tool()
def list_files(subfolder: str = "") -> dict:
    """
    List all files in the workspace or a specific subfolder.

    Args:
        subfolder: Optional subfolder name to list (default: root workspace)

    Returns:
        Dictionary with files and folders listed separately
    """
    if subfolder:
        target = resolve_safe_path(subfolder)
        if target is None:
            return {"error": "Access denied: Invalid folder path."}
        if not target.exists():
            return {"error": f"Folder '{subfolder}' does not exist."}
        if not target.is_dir():
            return {"error": f"'{subfolder}' is not a folder."}
    else:
        target = WORKSPACE

    files = []
    folders = []

    try:
        for item in sorted(target.iterdir()):
            if item.is_file():
                size = item.stat().st_size
                files.append({
                    "name": item.name,
                    "size_bytes": size,
                    "size_human": f"{size/1024:.1f} KB" if size > 1024 else f"{size} B"
                })
            elif item.is_dir():
                folders.append(item.name)

        return {
            "workspace": str(WORKSPACE),
            "current_folder": subfolder or "/",
            "folders": folders,
            "files": files,
            "total_files": len(files),
            "total_folders": len(folders)
        }

    except PermissionError:
        return {"error": f"Permission denied reading folder."}


@mcp.tool()
def read_file(filename: str) -> str:
    """
    Read and return the contents of a file in the workspace.

    Args:
        filename: The file to read (e.g. "notes.txt" or "projects/plan.md")

    Returns:
        The file contents as text
    """
    path = resolve_safe_path(filename)

    if path is None:
        return "Error: Access denied. Cannot read files outside the workspace."

    if not path.exists():
        return f"Error: File '{filename}' does not exist. Use list_files() to see available files."

    if not path.is_file():
        return f"Error: '{filename}' is a folder, not a file."

    # Size limit — don't read huge files
    file_size = path.stat().st_size
    if file_size > 500_000:  # 500 KB limit
        return f"Error: File too large ({file_size/1024:.0f} KB). Maximum is 500 KB."

    try:
        content = path.read_text(encoding="utf-8")
        return f"{'='*50}\n📄 {filename} ({file_size} bytes)\n{'='*50}\n\n{content}"

    except UnicodeDecodeError:
        return f"Error: '{filename}' appears to be a binary file, not text."
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def write_file(filename: str, content: str, overwrite: bool = False) -> str:
    """
    Create or update a file in the workspace.

    Args:
        filename: Name/path of the file to create (e.g. "notes.txt" or "docs/readme.md")
        content: The text content to write to the file
        overwrite: If True, overwrite existing files. If False, fail if file exists.

    Returns:
        Success or error message
    """
    path = resolve_safe_path(filename)

    if path is None:
        return "Error: Access denied. Cannot write outside the workspace."

    # Check if file already exists
    if path.exists() and not overwrite:
        return (
            f"Error: File '{filename}' already exists. "
            f"Set overwrite=True to replace it, or use a different filename."
        )

    # Create parent directories if needed
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"Error creating directories: {e}"

    # Write the file
    try:
        path.write_text(content, encoding="utf-8")
        char_count = len(content)
        line_count = content.count('\n') + 1
        return (
            f"✅ Successfully wrote '{filename}'\n"
            f"   • {char_count} characters\n"
            f"   • {line_count} lines\n"
            f"   • Saved to: {path}"
        )
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
def append_to_file(filename: str, content: str) -> str:
    """
    Add content to the end of an existing file (or create it if it doesn't exist).

    Args:
        filename: The file to append to
        content: The text to add at the end

    Returns:
        Success or error message
    """
    path = resolve_safe_path(filename)

    if path is None:
        return "Error: Access denied."

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"✅ Appended {len(content)} characters to '{filename}'"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def delete_file(filename: str) -> str:
    """
    Delete a file from the workspace.

    Args:
        filename: The file to delete

    Returns:
        Success or error message
    """
    path = resolve_safe_path(filename)

    if path is None:
        return "Error: Access denied."

    if not path.exists():
        return f"Error: File '{filename}' does not exist."

    if path.is_dir():
        return f"Error: '{filename}' is a folder. Use a specific file path."

    try:
        path.unlink()
        return f"✅ Deleted '{filename}'"
    except Exception as e:
        return f"Error deleting file: {e}"


@mcp.tool()
def search_files(query: str, file_extension: str = "") -> list:
    """
    Search for files containing a specific text string.

    Args:
        query: Text to search for (case-insensitive)
        file_extension: Only search files with this extension (e.g. ".txt", ".py")

    Returns:
        List of matching files with the lines that matched
    """
    results = []
    query_lower = query.lower()

    for file_path in WORKSPACE.rglob("*"):
        if not file_path.is_file():
            continue

        if file_extension and not file_path.suffix == file_extension:
            continue

        # Skip large files
        if file_path.stat().st_size > 100_000:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split('\n')

            matching_lines = []
            for i, line in enumerate(lines, 1):
                if query_lower in line.lower():
                    matching_lines.append(f"  Line {i}: {line.strip()}")

            if matching_lines:
                relative_path = file_path.relative_to(WORKSPACE)
                results.append({
                    "file": str(relative_path),
                    "matches": len(matching_lines),
                    "lines": matching_lines[:5]  # First 5 matches per file
                })

        except Exception:
            continue

    if not results:
        return [f"No files found containing '{query}'"]

    return results


if __name__ == "__main__":
    print(f"📁 Filesystem MCP Server", file=sys.stderr)
    print(f"   Workspace: {WORKSPACE}", file=sys.stderr)
    mcp.run()

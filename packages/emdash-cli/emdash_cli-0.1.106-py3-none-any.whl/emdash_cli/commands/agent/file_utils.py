"""File utilities for the agent CLI.

Handles @file reference expansion and fuzzy file finding.
"""

import fnmatch
import os
import re
from pathlib import Path

from rich.console import Console

console = Console()


def fuzzy_find_files(query: str, limit: int = 10) -> list[Path]:
    """Find files matching a fuzzy query.

    Args:
        query: File name or partial path to search for
        limit: Maximum number of results

    Returns:
        List of matching file paths
    """
    cwd = Path.cwd()
    matches = []

    # Common directories to skip
    skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.emdash'}

    # Walk the directory tree (more control than glob for skipping dirs)
    for root, dirs, files in os.walk(cwd):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]

        rel_root = Path(root).relative_to(cwd)

        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue

            rel_path = rel_root / file if str(rel_root) != '.' else Path(file)
            full_path = cwd / rel_path

            # Check if query matches (case-insensitive)
            path_str = str(rel_path).lower()
            query_lower = query.lower()

            if query_lower in path_str or fnmatch.fnmatch(path_str, f"*{query_lower}*"):
                matches.append(full_path)

                if len(matches) >= limit:
                    return matches

    return matches


def select_file_interactive(matches: list[Path], query: str) -> Path | None:
    """Show interactive file selection menu.

    Args:
        matches: List of matching file paths
        query: Original query string

    Returns:
        Selected file path or None if cancelled
    """
    if not matches:
        return None

    if len(matches) == 1:
        return matches[0]

    cwd = Path.cwd()

    # Print numbered list
    console.print(f"\n[bold cyan]Select file for @{query}:[/bold cyan]\n")

    for i, path in enumerate(matches):
        try:
            rel_path = path.relative_to(cwd)
        except ValueError:
            rel_path = path
        console.print(f"  [bold]{i + 1}[/bold]) {rel_path}")

    console.print(f"\n[dim]Enter number (1-{len(matches)}) or press Enter to cancel:[/dim]")

    try:
        from prompt_toolkit import PromptSession
        selection_session = PromptSession()
        choice = selection_session.prompt("").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(matches):
                return matches[idx]
    except (KeyboardInterrupt, EOFError):
        pass

    return None


def expand_file_references(message: str) -> tuple[str, list[str]]:
    """Expand @file references in a message to include file contents.

    Supports:
    - @file.txt - exact path (relative or absolute)
    - @utils - fuzzy search for files containing "utils"
    - @~/path/file.txt - home directory paths

    Shows interactive selection if multiple files match.

    Args:
        message: User message potentially containing @file references

    Returns:
        Tuple of (expanded_message, list_of_included_files)
    """
    # Pattern to match @word (not followed by space immediately, at least 2 chars)
    pattern = r'@([^\s@]{2,})'

    files_included = []
    file_contents = []
    replacements = {}  # Store replacements to apply after iteration

    # Find all @references
    for match in re.finditer(pattern, message):
        file_query = match.group(1)
        original = match.group(0)

        # Skip if already processed
        if original in replacements:
            continue

        # Expand ~ to home directory
        if file_query.startswith("~"):
            file_query_expanded = os.path.expanduser(file_query)
        else:
            file_query_expanded = file_query

        # Check if it's an exact path first
        path = Path(file_query_expanded)
        if not path.is_absolute():
            path = Path.cwd() / path

        resolved_path = None

        if path.exists() and path.is_file():
            # Exact match
            resolved_path = path
        else:
            # Fuzzy search
            matches = fuzzy_find_files(file_query)
            if matches:
                resolved_path = select_file_interactive(matches, file_query)

        if resolved_path:
            try:
                content = resolved_path.read_text()
                files_included.append(str(resolved_path))
                file_contents.append(f"\n\n**File: {resolved_path.name}**\n```\n{content}\n```")
                replacements[original] = ""  # Remove the @reference
            except Exception:
                pass  # Can't read file, leave as-is

    # Apply replacements
    expanded_message = message
    for original, replacement in replacements.items():
        expanded_message = expanded_message.replace(original, replacement)

    expanded_message = expanded_message.strip()

    # Append file contents to the message
    if file_contents:
        expanded_message = expanded_message + "\n" + "\n".join(file_contents)

    return expanded_message, files_included

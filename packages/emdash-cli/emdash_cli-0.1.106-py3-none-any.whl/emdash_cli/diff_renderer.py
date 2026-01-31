"""Diff rendering utilities for emdash CLI.

Provides GitHub-style diff display with line numbers and syntax highlighting.
"""

import re
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text

from .design import Colors, EM_DASH, STATUS_ACTIVE

# File extension to lexer mapping
EXTENSION_LEXERS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".kt": "kotlin",
    ".swift": "swift",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".toml": "toml",
    ".xml": "xml",
    ".dockerfile": "dockerfile",
}


def get_lexer_for_file(filepath: str) -> str:
    """Get the syntax lexer for a file based on extension."""
    ext = Path(filepath).suffix.lower()

    # Special case for Dockerfile
    if Path(filepath).name.lower() == "dockerfile":
        return "dockerfile"

    return EXTENSION_LEXERS.get(ext, "text")


def render_diff(
    diff_output: str,
    console: Optional[Console] = None,
    compact: bool = False,
    max_lines: int = 50,
) -> None:
    """Render git diff output with line numbers and syntax highlighting.

    Args:
        diff_output: Raw git diff output
        console: Rich console to render to
        compact: If True, show compact view (fewer context lines)
        max_lines: Maximum diff lines to show per file
    """
    if console is None:
        console = Console()

    # Parse diff into files
    files = _parse_diff(diff_output)

    for filepath, hunks in files.items():
        _render_file_diff(console, filepath, hunks, compact, max_lines)


def render_file_change(
    console: Console,
    filepath: str,
    old_content: str = "",
    new_content: str = "",
    diff_lines: Optional[list] = None,
    compact: bool = True,
) -> None:
    """Render a file change as inline diff (for agent edits).

    Args:
        console: Rich console to render to
        filepath: Path to the file
        old_content: Original file content
        new_content: New file content
        diff_lines: Pre-computed diff lines (optional)
        compact: If True, show compact view
    """
    # Try to get git diff if no diff_lines provided
    if not diff_lines:
        diff_lines = _get_git_diff_for_file(filepath)

    # Count changes
    additions = 0
    deletions = 0

    if diff_lines:
        additions = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
        deletions = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    elif old_content and new_content:
        old_lines = set(old_content.split("\n"))
        new_lines = set(new_content.split("\n"))
        additions = len(new_lines - old_lines)
        deletions = len(old_lines - new_lines)

    # Shorten path for display
    display_path = filepath
    if len(display_path) > 50:
        display_path = "..." + display_path[-47:]

    # Header line
    header = Text()
    header.append(f"{STATUS_ACTIVE} ", style=Colors.WARNING)
    header.append("Update", style=f"{Colors.TEXT} bold")
    header.append(f"({display_path})", style=Colors.MUTED)
    console.print(header)

    # Summary line
    if additions or deletions:
        summary = Text()
        summary.append("  └ ", style=Colors.DIM)
        if additions and deletions:
            summary.append(f"Changed ", style=Colors.DIM)
            summary.append(f"{additions + deletions}", style=Colors.TEXT)
            summary.append(" lines", style=Colors.DIM)
        elif additions:
            summary.append("Added ", style=Colors.DIM)
            summary.append(f"{additions}", style=Colors.SUCCESS)
            summary.append(" lines", style=Colors.DIM)
        else:
            summary.append("Removed ", style=Colors.DIM)
            summary.append(f"{deletions}", style=Colors.ERROR)
            summary.append(" lines", style=Colors.DIM)
        console.print(summary)
    else:
        # No diff available - just show modified
        summary = Text()
        summary.append("  └ ", style=Colors.DIM)
        summary.append("modified", style=Colors.MUTED)
        console.print(summary)

    # Render diff lines with line numbers
    if diff_lines:
        _render_diff_lines_compact(console, filepath, diff_lines)


def _get_git_diff_for_file(filepath: str) -> list:
    """Get git diff for a specific file.

    Returns list of diff lines, or empty list if not available.
    """
    try:
        # Try unstaged changes first
        result = subprocess.run(
            ["git", "diff", "--no-color", "--", filepath],
            capture_output=True,
            text=True,
            timeout=5,
        )
        diff_output = result.stdout

        # If no unstaged, try staged
        if not diff_output:
            result = subprocess.run(
                ["git", "diff", "--staged", "--no-color", "--", filepath],
                capture_output=True,
                text=True,
                timeout=5,
            )
            diff_output = result.stdout

        if diff_output:
            # Parse and return just the diff lines (skip headers)
            lines = []
            in_hunk = False
            for line in diff_output.split("\n"):
                if line.startswith("@@"):
                    in_hunk = True
                    lines.append(line)
                elif in_hunk:
                    lines.append(line)
            return lines

    except Exception:
        pass

    return []


def _parse_diff(diff_output: str) -> dict:
    """Parse git diff output into structured format.

    Returns:
        Dict mapping filepath to list of hunks, where each hunk is
        (old_start, old_count, new_start, new_count, lines)
    """
    files = {}
    current_file = None
    current_hunks = []
    current_hunk_lines = []
    hunk_info = None

    for line in diff_output.split("\n"):
        if line.startswith("diff --git"):
            # Save previous file
            if current_file and current_hunks:
                if current_hunk_lines and hunk_info:
                    current_hunks.append((hunk_info, current_hunk_lines))
                files[current_file] = current_hunks

            # Extract filename
            parts = line.split(" b/")
            current_file = parts[-1] if len(parts) > 1 else "unknown"
            current_hunks = []
            current_hunk_lines = []
            hunk_info = None

        elif line.startswith("@@"):
            # New hunk - save previous
            if current_hunk_lines and hunk_info:
                current_hunks.append((hunk_info, current_hunk_lines))

            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if match:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                hunk_info = (old_start, old_count, new_start, new_count)
            else:
                hunk_info = (1, 0, 1, 0)

            current_hunk_lines = []

        elif current_file and hunk_info is not None:
            if not line.startswith("---") and not line.startswith("+++"):
                current_hunk_lines.append(line)

    # Don't forget last file/hunk
    if current_file:
        if current_hunk_lines and hunk_info:
            current_hunks.append((hunk_info, current_hunk_lines))
        if current_hunks:
            files[current_file] = current_hunks

    return files


def _render_file_diff(
    console: Console,
    filepath: str,
    hunks: list,
    compact: bool,
    max_lines: int,
) -> None:
    """Render diff for a single file with line numbers."""
    # Count changes
    additions = 0
    deletions = 0
    for _, lines in hunks:
        for line in lines:
            if line.startswith("+"):
                additions += 1
            elif line.startswith("-"):
                deletions += 1

    # File header
    header = Text()
    header.append(f"{EM_DASH * 3} ", style=Colors.DIM)
    header.append(filepath, style=f"{Colors.PRIMARY} bold")
    header.append(f" {EM_DASH * max(1, 60 - len(filepath))}", style=Colors.DIM)
    console.print()
    console.print(header)

    # Stats line
    stats = Text()
    if additions:
        stats.append(f"+{additions}", style=Colors.SUCCESS)
    if additions and deletions:
        stats.append(" ")
    if deletions:
        stats.append(f"-{deletions}", style=Colors.ERROR)
    if additions or deletions:
        console.print(stats)

    # Get lexer for syntax highlighting
    lexer = get_lexer_for_file(filepath)

    # Render hunks
    total_lines = 0
    for hunk_info, lines in hunks:
        if total_lines >= max_lines:
            remaining = sum(len(h[1]) for h in hunks) - total_lines
            if remaining > 0:
                console.print(f"  [{Colors.DIM}]... {remaining} more lines[/{Colors.DIM}]")
            break

        old_line, _, new_line, _ = hunk_info

        for line in lines:
            if total_lines >= max_lines:
                break

            if line.startswith("+"):
                # Addition
                line_text = Text()
                line_text.append(f"{new_line:4} ", style=Colors.DIM)
                line_text.append("+ ", style=f"{Colors.SUCCESS} bold")
                _append_highlighted(line_text, line[1:], lexer, Colors.SUCCESS)
                console.print(line_text)
                new_line += 1
                total_lines += 1

            elif line.startswith("-"):
                # Deletion
                line_text = Text()
                line_text.append(f"{old_line:4} ", style=Colors.DIM)
                line_text.append("- ", style=f"{Colors.ERROR} bold")
                _append_highlighted(line_text, line[1:], lexer, Colors.ERROR)
                console.print(line_text)
                old_line += 1
                total_lines += 1

            else:
                # Context line
                if not compact or total_lines < 3:
                    line_text = Text()
                    line_text.append(f"{new_line:4} ", style=Colors.DIM)
                    line_text.append("  ", style=Colors.DIM)
                    line_text.append(line[1:] if line.startswith(" ") else line, style=Colors.DIM)
                    console.print(line_text)
                    total_lines += 1

                old_line += 1
                new_line += 1

    console.print()


def _render_diff_lines_compact(
    console: Console,
    filepath: str,
    diff_lines: list,
    max_lines: int = 8,
) -> None:
    """Render diff lines in compact format for inline display."""
    lexer = get_lexer_for_file(filepath)

    shown = 0
    line_num = 1  # Approximate line number

    for line in diff_lines:
        if shown >= max_lines:
            remaining = len(diff_lines) - shown
            if remaining > 0:
                console.print(f"      [{Colors.DIM}]... {remaining} more lines[/{Colors.DIM}]")
            break

        if line.startswith("+") and not line.startswith("+++"):
            line_text = Text()
            line_text.append(f"    {line_num:4} ", style=Colors.DIM)
            line_text.append("+ ", style=f"{Colors.SUCCESS} bold")
            _append_highlighted(line_text, line[1:], lexer, Colors.SUCCESS)
            console.print(line_text)
            shown += 1
            line_num += 1

        elif line.startswith("-") and not line.startswith("---"):
            line_text = Text()
            line_text.append(f"    {line_num:4} ", style=Colors.DIM)
            line_text.append("- ", style=f"{Colors.ERROR} bold")
            _append_highlighted(line_text, line[1:], lexer, Colors.ERROR)
            console.print(line_text)
            shown += 1
            # Don't increment line_num for deletions

        elif not line.startswith("@@") and not line.startswith("---") and not line.startswith("+++"):
            # Context line - show sparingly
            if shown < 2:
                line_text = Text()
                line_text.append(f"    {line_num:4} ", style=Colors.DIM)
                line_text.append("  ", style=Colors.DIM)
                content = line[1:] if line.startswith(" ") else line
                line_text.append(content, style=Colors.DIM)
                console.print(line_text)
                shown += 1
            line_num += 1


def _append_highlighted(text: Text, content: str, lexer: str, base_style: str) -> None:
    """Append syntax-highlighted content to a Text object.

    For simplicity, we apply the base style and let keywords stand out.
    Full syntax highlighting would require more complex handling.
    """
    # Simple keyword highlighting for common languages
    if lexer in ("python", "javascript", "typescript", "java", "go", "rust"):
        keywords = {
            "python": ["def", "class", "import", "from", "if", "else", "elif", "try", "except", "finally", "for", "while", "return", "yield", "with", "as", "None", "True", "False", "and", "or", "not", "in", "is", "lambda", "async", "await"],
            "javascript": ["function", "const", "let", "var", "if", "else", "for", "while", "return", "import", "export", "from", "class", "new", "this", "async", "await", "try", "catch", "finally", "null", "undefined", "true", "false"],
            "typescript": ["function", "const", "let", "var", "if", "else", "for", "while", "return", "import", "export", "from", "class", "new", "this", "async", "await", "try", "catch", "finally", "null", "undefined", "true", "false", "interface", "type", "enum"],
            "java": ["public", "private", "protected", "class", "interface", "extends", "implements", "if", "else", "for", "while", "return", "new", "this", "try", "catch", "finally", "null", "true", "false", "void", "static", "final"],
            "go": ["func", "package", "import", "if", "else", "for", "return", "var", "const", "type", "struct", "interface", "nil", "true", "false", "go", "defer", "chan", "select", "case"],
            "rust": ["fn", "let", "mut", "if", "else", "for", "while", "return", "use", "mod", "pub", "struct", "impl", "trait", "enum", "match", "Some", "None", "Ok", "Err", "self", "Self", "async", "await"],
        }

        kw_list = keywords.get(lexer, [])
        if kw_list:
            # Simple word-based highlighting
            words = re.split(r'(\s+|\W)', content)
            for word in words:
                if word in kw_list:
                    text.append(word, style=f"{Colors.WARNING} bold")
                elif word.startswith('"') or word.startswith("'") or word.startswith('`'):
                    text.append(word, style=Colors.SUCCESS)
                else:
                    text.append(word, style=base_style)
            return

    # Default: just apply base style
    text.append(content, style=base_style)

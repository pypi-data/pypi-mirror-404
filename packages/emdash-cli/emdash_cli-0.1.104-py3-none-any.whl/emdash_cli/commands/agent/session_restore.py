"""Session restore prompt for emdash CLI.

Detects recent sessions and offers to restore them with zen styling.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
from prompt_toolkit.styles import Style

from ...design import (
    Colors,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    DOT_BULLET,
    ARROW_PROMPT,
    header,
    footer,
)

console = Console()


def get_recent_session(client, max_age_hours: int = 24) -> Optional[dict]:
    """Get the most recent session if within max_age.

    Args:
        client: Emdash client instance
        max_age_hours: Maximum age in hours for session to be considered recent

    Returns:
        Session info dict or None
    """
    try:
        sessions = client.list_sessions()
        if not sessions:
            return None

        # Sort by updated_at (most recent first)
        sessions = sorted(sessions, key=lambda s: s.updated_at or "", reverse=True)

        if not sessions:
            return None

        recent = sessions[0]

        # Check if session is recent enough
        if recent.updated_at:
            try:
                updated = datetime.fromisoformat(recent.updated_at.replace("Z", "+00:00"))
                cutoff = datetime.now(updated.tzinfo) - timedelta(hours=max_age_hours)
                if updated < cutoff:
                    return None
            except (ValueError, TypeError):
                pass

        # Only offer to restore if it has messages
        if recent.message_count and recent.message_count > 0:
            return {
                "name": recent.name,
                "summary": recent.summary,
                "mode": recent.mode,
                "message_count": recent.message_count,
                "updated_at": recent.updated_at,
            }

        return None
    except Exception:
        return None


def format_relative_time(iso_time: str) -> str:
    """Format ISO time as relative time (e.g., '2 hours ago')."""
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        delta = now - dt

        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"
    except (ValueError, TypeError):
        return ""


def show_session_restore_prompt(session_info: dict) -> tuple[str, Optional[dict]]:
    """Show prompt to restore a recent session.

    Args:
        session_info: Dict with session details

    Returns:
        Tuple of (choice, session_data) where choice is:
        - 'restore': Restore the session
        - 'new': Start new session
        - 'view': View session details first
    """
    name = session_info.get("name", "unnamed")
    summary = session_info.get("summary", "")
    mode = session_info.get("mode", "code")
    msg_count = session_info.get("message_count", 0)
    updated = session_info.get("updated_at", "")

    relative_time = format_relative_time(updated) if updated else ""

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Session Found', 40)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.DIM}]Previous session from {relative_time}:[/{Colors.DIM}]")
    console.print()
    console.print(f"    {DOT_BULLET} [{Colors.MUTED}]{msg_count} messages[/{Colors.MUTED}]")
    if summary:
        truncated = summary[:60] + "..." if len(summary) > 60 else summary
        console.print(f"    {DOT_BULLET} [{Colors.MUTED}]{truncated}[/{Colors.MUTED}]")
    console.print(f"    {DOT_BULLET} [{Colors.MUTED}]Mode: {mode}[/{Colors.MUTED}]")
    console.print()
    console.print(f"[{Colors.MUTED}]{footer(40)}[/{Colors.MUTED}]")

    selected_index = [0]
    result = [("new", None)]

    options = [
        ("restore", "Restore this session"),
        ("new", "Start new session"),
    ]

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_index[0] = (selected_index[0] - 1) % len(options)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_index[0] = (selected_index[0] + 1) % len(options)

    @kb.add("enter")
    def select(event):
        result[0] = (options[selected_index[0]][0], session_info if options[selected_index[0]][0] == "restore" else None)
        event.app.exit()

    @kb.add("r")
    def restore(event):
        result[0] = ("restore", session_info)
        event.app.exit()

    @kb.add("n")
    def new(event):
        result[0] = ("new", None)
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    def cancel(event):
        result[0] = ("new", None)
        event.app.exit()

    def get_formatted_options():
        lines = []
        for i, (key, desc) in enumerate(options):
            indicator = STATUS_ACTIVE if i == selected_index[0] else STATUS_INACTIVE
            style_class = "selected" if i == selected_index[0] else "option"
            lines.append((f"class:{style_class}", f"  {indicator} {desc}\n"))
        lines.append(("class:hint", f"\n{ARROW_PROMPT} r restore  n new  Esc skip"))
        return lines

    style = Style.from_dict({
        "selected": f"{Colors.SUCCESS} bold",
        "option": Colors.MUTED,
        "hint": f"{Colors.DIM} italic",
    })

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_options),
                height=5,
            ),
        ])
    )

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        full_screen=False,
    )

    console.print()

    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        return ("new", None)

    return result[0]

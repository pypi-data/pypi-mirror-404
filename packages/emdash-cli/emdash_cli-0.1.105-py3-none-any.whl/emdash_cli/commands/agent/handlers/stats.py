"""Handler for /stats command - display user activity statistics."""

from datetime import datetime
from typing import Optional

from rich.box import Box, HEAVY, SQUARE
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from ....design import (
    Colors,
    header,
    footer,
    SEPARATOR_WIDTH,
)
from ....session_store import SessionStore

console = Console()


def _format_number(num: int) -> str:
    """Format a number with K/M suffix."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def _format_date(date_str: Optional[str]) -> str:
    """Format a date string to a readable format."""
    if not date_str:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now()

        # Same day
        if dt.date() == now.date():
            return f"Today {dt.strftime('%H:%M')}"

        # Yesterday
        yesterday = now.date().replace(day=now.day - 1)
        if dt.date() == yesterday:
            return f"Yesterday {dt.strftime('%H:%M')}"

        # This week
        if (now.date() - dt.date()).days < 7:
            return dt.strftime("%a %b %d")

        # This year
        if dt.year == now.year:
            return dt.strftime("%b %d")

        # Older
        return dt.strftime("%b %d, %Y")
    except Exception:
        return date_str[:10] if date_str else "Unknown"


def _make_bar(percentage: float, width: int = 20) -> str:
    """Create a text bar for visualization."""
    filled = int(percentage / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return bar


def _parse_args(args: str) -> dict:
    """Parse command arguments."""
    parsed = {
        "tokens": False,
        "sessions": False,
        "weekly": False,
        "model": None,
    }

    if not args:
        return parsed

    parts = args.split()
    for part in parts:
        if part.startswith("--model="):
            parsed["model"] = part.split("=", 1)[1]
        elif part.startswith("--"):
            key = part.lstrip("-").replace("-", "_")
            if key in parsed:
                parsed[key] = True
        elif part.startswith("-"):
            for char in part[1:]:
                if char in ["t", "s", "w"]:
                    flag_map = {"t": "tokens", "s": "sessions", "w": "weekly"}
                    parsed[flag_map.get(char)] = True

    return parsed


def _show_session_stats(stats: dict) -> None:
    """Display current session statistics.

    Args:
        stats: Session stats dict from API
    """
    model = stats.get("model", "unknown")
    input_tokens = stats.get("input_tokens", 0)
    output_tokens = stats.get("output_tokens", 0)
    thinking_tokens = stats.get("thinking_tokens", 0)
    total_tokens = stats.get("total_tokens", 0)
    cost = stats.get("cost_formatted", "$0.0000")

    console.print(f"[bold cyan]Current Session[/bold cyan] - {model}")
    console.print()
    console.print(
        f"  🧠 Tokens: [{Colors.SUCCESS}]{_format_number(total_tokens)}[/{Colors.SUCCESS}]"
        f"  (in: {_format_number(input_tokens)}, out: {_format_number(output_tokens)}"
        + (f", think: {_format_number(thinking_tokens)}" if thinking_tokens > 0 else "")
        + ")"
    )
    console.print(f"  💰 Session Cost: [{Colors.WARNING}]{cost}[/{Colors.WARNING}]")


def handle_stats(args: str, client=None, session_id: str | None = None) -> None:
    """Handle /stats command - display user activity statistics.

    Args:
        args: Command arguments
        client: EmdashClient instance
        session_id: Current session ID for real-time session stats
    """
    flags = _parse_args(args)

    console.print()

    # Initialize client if needed
    if client is None:
        from ....client import EmdashClient
        client = EmdashClient("http://localhost:8765")

    # Show current session stats first if we have an active session
    session_stats_shown = False
    if session_id:
        try:
            session_stats = client.get_session_stats_realtime(session_id)
            _show_session_stats(session_stats)
            console.print()
            session_stats_shown = True
        except Exception as e:
            console.print(f"[dim]Session stats unavailable: {e}[/dim]")
            console.print()

    # Fetch historical stats from the client
    try:
        user_stats = client.get_user_stats()
        token_breakdown = client.get_token_breakdown()
    except Exception as e:
        console.print(f"  [red]✗[/red] Failed to fetch stats: {e}")
        console.print(f"  [dim]Make sure emdash-core is running.[/dim]")
        return

    # Skip historical section if no data and we already showed session stats
    if user_stats.get("total_sessions", 0) == 0:
        if not session_stats_shown:
            console.print(Panel(
                Text("No stats yet! Start a conversation to see your activity.", justify="center"),
                title="📊 Your Stats",
                border_style="dim",
                box=HEAVY,
            ))
        return

    console.print(f"[bold cyan]Emdash Stats[/bold cyan] - Historical Activity")
    console.print()

    # Format the stats display
    sessions = user_stats.get("total_sessions", 0)
    total_tokens = user_stats.get("total_tokens", 0)
    estimated_cost = user_stats.get("cost_formatted", "$0.0000")
    first_seen = _format_date(user_stats.get("first_seen"))
    last_active = _format_date(user_stats.get("last_active"))

    # Calculate token breakdown percentages
    input_tokens = token_breakdown.get("input", 0)
    output_tokens = token_breakdown.get("output", 0)
    thinking_tokens = token_breakdown.get("thinking", 0)

    if total_tokens > 0:
        input_pct = (input_tokens / total_tokens) * 100
        output_pct = (output_tokens / total_tokens) * 100
        thinking_pct = (thinking_tokens / total_tokens) * 100
    else:
        input_pct = output_pct = thinking_pct = 0

    # Build the main panel content
    content_lines = []

    # Top stats row
    content_lines.append(
        f"  💬 Sessions"
        f"  [{Colors.SUCCESS}]{sessions:,}[/{Colors.SUCCESS}]"
        f"   🧠 Total Tokens"
        f"  [{Colors.SUCCESS}]{_format_number(total_tokens)}[/{Colors.SUCCESS}]"
        f"   💰 Cost"
        f"  [{Colors.WARNING}]{estimated_cost}[/{Colors.WARNING}]"
    )
    content_lines.append(
        f"  📅 First Seen"
        f"  [{Colors.MUTED}]{first_seen}[/{Colors.MUTED}]"
        f"   📅 Last Active"
        f"  [{Colors.MUTED}]{last_active}[/{Colors.MUTED}]"
    )

    # Separator
    content_lines.append("")
    content_lines.append(f"[bold]{'─' * 45}[/bold]")

    # Token breakdown section
    content_lines.append("")
    content_lines.append(f"[bold]📈 Token Breakdown[/bold]")

    # Token bars
    input_bar = _make_bar(input_pct)
    output_bar = _make_bar(output_pct)
    thinking_bar = _make_bar(thinking_pct)

    content_lines.append(f"  ├─ Input     {input_bar}  {_format_number(input_tokens)} ({input_pct:.0f}%)")
    content_lines.append(f"  ├─ Output    {output_bar}  {_format_number(output_tokens)} ({output_pct:.0f}%)")
    content_lines.append(f"  └─ Thinking  {thinking_bar}  {_format_number(thinking_tokens)} ({thinking_pct:.0f}%)")

    # Model usage section
    model_usage = user_stats.get("model_usage", [])
    if model_usage:
        content_lines.append("")
        content_lines.append(f"[bold]🤖 Model Usage[/bold]")

        # Sort by tokens
        model_usage.sort(key=lambda x: x.get("tokens", 0), reverse=True)

        for i, model_info in enumerate(model_usage[:5]):  # Top 5 models
            model_name = model_info.get("model", "Unknown")
            tokens = model_info.get("tokens", 0)
            pct = (tokens / total_tokens * 100) if total_tokens > 0 else 0
            bar = _make_bar(pct)

            if i == len(model_usage[:5]) - 1:
                prefix = "  └─"
            else:
                prefix = "  ├─"

            content_lines.append(f"  {prefix} {model_name[:20]:<20} {bar}  {_format_number(tokens)}")

    # Join and display
    content = "\n".join(content_lines)

    console.print(Panel(
        Text(content, justify="left"),
        title="📊 Your Stats",
        border_style=Colors.PRIMARY,
        box=HEAVY,
    ))

    # Show sessions list if requested
    if flags.get("sessions"):
        console.print()
        console.print(f"[bold cyan]Recent Sessions[/bold cyan]")
        console.print()

        try:
            sessions_data = client.get_session_stats(limit=10)
            sessions_list = sessions_data.get("sessions", [])

            if not sessions_list:
                console.print("  [dim]No sessions found[/dim]")
            else:
                table = Table(show_header=True, box=Box.SQUARE)
                table.add_column("Session ID", style="dim")
                table.add_column("Created", style="dim")
                table.add_column("Tokens")
                table.add_column("Model", style="dim")

                for session in sessions_list:
                    session_id = session.get("session_id", "")[:8]
                    created = _format_date(session.get("created_at"))
                    tokens = _format_number(session.get("token_count", 0))
                    model = session.get("model", "-") or "-"
                    table.add_row(session_id, created, tokens, model[:15])

                console.print(table)
        except Exception as e:
            console.print(f"  [dim]Failed to load sessions: {e}[/dim]")

    console.print()
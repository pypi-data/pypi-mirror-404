"""Handlers for miscellaneous slash commands."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from emdash_cli.design import Colors, EM_DASH, print_error
from emdash_cli.diff_renderer import render_diff

console = Console()


def handle_status(client) -> None:
    """Handle /status command.

    Args:
        client: EmdashClient instance
    """
    console.print("\n[bold cyan]Status[/bold cyan]\n")

    # Index status
    console.print("[bold]Index Status[/bold]")
    try:
        status = client.index_status(str(Path.cwd()))
        is_indexed = status.get("is_indexed", False)
        console.print(f"  Indexed: {'[green]Yes[/green]' if is_indexed else '[yellow]No[/yellow]'}")

        if is_indexed:
            console.print(f"  Files: {status.get('file_count', 0)}")
            console.print(f"  Functions: {status.get('function_count', 0)}")
            console.print(f"  Classes: {status.get('class_count', 0)}")
            console.print(f"  Communities: {status.get('community_count', 0)}")
            if status.get("last_indexed"):
                console.print(f"  Last indexed: {status.get('last_indexed')}")
            if status.get("last_commit"):
                console.print(f"  Last commit: {status.get('last_commit')}")
    except Exception as e:
        print_error(e, "  Error fetching index status")

    console.print()

    # PROJECT.md status
    console.print("[bold]PROJECT.md Status[/bold]")
    projectmd_path = Path.cwd() / "PROJECT.md"
    if projectmd_path.exists():
        stat = projectmd_path.stat()
        modified_time = datetime.fromtimestamp(stat.st_mtime)
        size_kb = stat.st_size / 1024
        console.print(f"  Exists: [green]Yes[/green]")
        console.print(f"  Path: {projectmd_path}")
        console.print(f"  Size: {size_kb:.1f} KB")
        console.print(f"  Last modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        console.print(f"  Exists: [yellow]No[/yellow]")
        console.print("[dim]  Run /projectmd to generate it[/dim]")

    console.print()


def handle_pr(args: str, run_slash_command_task, client, renderer, model, max_iterations) -> None:
    """Handle /pr command.

    Args:
        args: PR URL or number
        run_slash_command_task: Function to run slash command tasks
        client: EmdashClient instance
        renderer: SSERenderer instance
        model: Current model
        max_iterations: Max iterations
    """
    if not args:
        console.print("[yellow]Usage: /pr <pr-url-or-number>[/yellow]")
        console.print("[dim]Example: /pr 123 or /pr https://github.com/org/repo/pull/123[/dim]")
    else:
        console.print(f"[cyan]Reviewing PR: {args}[/cyan]")
        run_slash_command_task(
            client, renderer, model, max_iterations,
            f"Review this pull request and provide feedback: {args}",
            {"mode": "code"}
        )


def handle_projectmd(run_slash_command_task, client, renderer, model, max_iterations) -> None:
    """Handle /projectmd command.

    Args:
        run_slash_command_task: Function to run slash command tasks
        client: EmdashClient instance
        renderer: SSERenderer instance
        model: Current model
        max_iterations: Max iterations
    """
    console.print("[cyan]Generating PROJECT.md...[/cyan]")
    run_slash_command_task(
        client, renderer, model, max_iterations,
        "Analyze this codebase and generate a comprehensive PROJECT.md file that describes the architecture, main components, how to get started, and key design decisions.",
        {"mode": "code"}
    )


def handle_research(args: str, run_slash_command_task, client, renderer, model) -> None:
    """Handle /research command.

    Args:
        args: Research goal
        run_slash_command_task: Function to run slash command tasks
        client: EmdashClient instance
        renderer: SSERenderer instance
        model: Current model
    """
    if not args:
        console.print("[yellow]Usage: /research <goal>[/yellow]")
        console.print("[dim]Example: /research How does authentication work in this codebase?[/dim]")
    else:
        console.print(f"[cyan]Researching: {args}[/cyan]")
        run_slash_command_task(
            client, renderer, model, 50,  # More iterations for research
            f"Conduct deep research on: {args}\n\nExplore the codebase thoroughly, analyze relevant code, and provide a comprehensive answer with references to specific files and functions.",
            {"mode": "plan"}  # Use plan mode for research
        )


def handle_context(renderer) -> None:
    """Handle /context command.

    Args:
        renderer: SSERenderer instance with _last_context_frame attribute
    """
    context_data = getattr(renderer, '_last_context_frame', None)
    if not context_data:
        console.print("\n[dim]No context frame available yet. Run a query first.[/dim]\n")
    else:
        adding = context_data.get("adding") or {}
        reading = context_data.get("reading") or {}

        # Get stats
        step_count = adding.get("step_count", 0)
        entities_found = adding.get("entities_found", 0)
        context_tokens = adding.get("context_tokens", 0)
        context_breakdown = adding.get("context_breakdown", {})

        console.print()
        console.print("[bold cyan]Context Frame[/bold cyan]")
        console.print()

        # Show total context
        if context_tokens > 0:
            console.print(f"[bold]Total:[/bold] {context_tokens:,} tokens")

        # Show breakdown
        if context_breakdown:
            console.print(f"\n[bold]Breakdown:[/bold]")
            for key, tokens in context_breakdown.items():
                if tokens > 0:
                    console.print(f"  {key}: {tokens:,}")

        # Show stats
        if step_count > 0 or entities_found > 0:
            console.print(f"\n[bold]Stats:[/bold]")
            if step_count > 0:
                console.print(f"  Steps: {step_count}")
            if entities_found > 0:
                console.print(f"  Entities: {entities_found}")

        # Show reranking query
        query = reading.get("query")
        if query:
            console.print(f"\n[bold]Reranking Query:[/bold]")
            console.print(f"  [yellow]{query}[/yellow]")

        # Show reranked items
        items = reading.get("items", [])
        if items:
            console.print(f"\n[bold]Reranked Items ({len(items)}):[/bold]")
            for i, item in enumerate(items, 1):
                name = item.get("name", "?")
                item_type = item.get("type", "?")
                score = item.get("score")
                file_path = item.get("file", "")
                description = item.get("description", "")
                touch_count = item.get("touch_count", 0)
                neighbors = item.get("neighbors", [])

                score_str = f"[cyan]{score:.3f}[/cyan]" if score is not None else "[dim]n/a[/dim]"
                touch_str = f"[magenta]×{touch_count}[/magenta]" if touch_count > 1 else ""

                console.print(f"\n  [bold white]{i}.[/bold white] [dim]{item_type}[/dim] [bold]{name}[/bold]")
                console.print(f"     Score: {score_str} {touch_str}")
                if file_path:
                    console.print(f"     File: [dim]{file_path}[/dim]")
                if description:
                    desc_preview = description[:100] + "..." if len(description) > 100 else description
                    console.print(f"     Desc: [dim]{desc_preview}[/dim]")
                if neighbors:
                    console.print(f"     Neighbors: [dim]{', '.join(neighbors)}[/dim]")
        else:
            debug_info = reading.get("debug", "")
            if debug_info:
                console.print(f"\n[dim]No reranked items: {debug_info}[/dim]")
            else:
                console.print(f"\n[dim]No reranked items yet. Items appear after exploration (file reads, searches).[/dim]")

        # Show full context frame as JSON
        console.print(f"\n[bold]Full Context Frame:[/bold]")
        context_json = json.dumps(context_data, indent=2, default=str)
        syntax = Syntax(context_json, "json", theme="monokai", line_numbers=False)
        console.print(syntax)
        console.print()


def handle_messages(client, session_id: str | None) -> None:
    """Handle /messages command.

    Shows the current session messages in JSON format.

    Args:
        client: EmdashClient instance
        session_id: Current session ID (if any)
    """
    if not session_id:
        console.print("\n[dim]No active session. Start a conversation first.[/dim]\n")
        return

    try:
        data = client.get_session_messages(session_id)
        messages = data.get("messages", [])

        if not messages:
            console.print("\n[dim]No messages in current session.[/dim]\n")
            return

        console.print()
        console.print(f"[bold cyan]Session Messages[/bold cyan] ({len(messages)} messages)")
        console.print()

        # Display messages with proper formatting
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Role color
            role_color = {"user": "green", "assistant": "cyan", "system": "yellow"}.get(role, "white")
            console.print(f"[bold {role_color}][{i}] {role}[/bold {role_color}]")

            # Content - print as plain text to avoid truncation
            if isinstance(content, str):
                # Truncate very long messages for display
                if len(content) > 5000:
                    console.print(content[:5000])
                    console.print(f"[dim]... ({len(content) - 5000} more chars)[/dim]")
                else:
                    console.print(content)
            else:
                # For non-string content (lists, etc.), use JSON
                console.print(json.dumps(content, indent=2, default=str))

            console.print()  # Blank line between messages
        console.print()

    except Exception as e:
        console.print(f"\n[red]Error getting messages: {e}[/red]\n")


def handle_compact(client, session_id: str | None) -> None:
    """Handle /compact command.

    Manually triggers message history compaction using LLM summarization.

    Args:
        client: EmdashClient instance
        session_id: Current session ID (if any)
    """
    if not session_id:
        console.print("\n[yellow]No active session. Start a conversation first.[/yellow]\n")
        return

    console.print("\n[bold cyan]Compacting message history...[/bold cyan]\n")

    try:
        response = client.post(f"/api/agent/chat/{session_id}/compact")

        if response.status_code == 404:
            console.print("[yellow]Session not found.[/yellow]\n")
            return

        if response.status_code != 200:
            console.print(f"[red]Error: {response.text}[/red]\n")
            return

        data = response.json()

        if not data.get("compacted"):
            reason = data.get("reason", "Unknown reason")
            console.print(f"[yellow]Could not compact: {reason}[/yellow]\n")
            return

        # Show stats
        original_msgs = data.get("original_message_count", 0)
        new_msgs = data.get("new_message_count", 0)
        original_tokens = data.get("original_tokens", 0)
        new_tokens = data.get("new_tokens", 0)
        reduction = data.get("reduction_percent", 0)
        llm_summary = data.get("llm_summary", False)
        error = data.get("error")

        if llm_summary:
            console.print("[green]✓ Compaction complete (LLM summary generated)[/green]\n")
        elif error:
            console.print(f"[yellow]⚠ Compaction used truncation: {error}[/yellow]\n")
        else:
            console.print("[yellow]⚠ Compaction complete (truncation only, no LLM summary)[/yellow]\n")

        console.print(f"[bold]Messages:[/bold] {original_msgs} → {new_msgs}")
        console.print(f"[bold]Tokens:[/bold] {original_tokens:,} → {new_tokens:,} ([green]-{reduction}%[/green])")

        # Show the summary
        summary = data.get("summary")
        if summary:
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"[dim]{'─' * 60}[/dim]")
            console.print(summary)
            console.print(f"[dim]{'─' * 60}[/dim]")
        elif not llm_summary:
            console.print(f"\n[dim]No summary was generated. Check server logs for LLM errors.[/dim]")

        console.print()

    except Exception as e:
        print_error(e, "Error during compaction")
        console.print()


def handle_diff(args: str = "") -> None:
    """Handle /diff command - show uncommitted changes in GitHub-style diff view.

    Args:
        args: Optional file path to show diff for specific file
    """
    try:
        # Build git diff command
        cmd = ["git", "diff", "--no-color"]
        if args:
            cmd.append(args)

        # Also include staged changes
        result_unstaged = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path.cwd()
        )

        cmd_staged = ["git", "diff", "--staged", "--no-color"]
        if args:
            cmd_staged.append(args)

        result_staged = subprocess.run(
            cmd_staged, capture_output=True, text=True, cwd=Path.cwd()
        )

        # Combine diffs
        diff_output = ""
        if result_staged.stdout:
            diff_output += result_staged.stdout
        if result_unstaged.stdout:
            if diff_output:
                diff_output += "\n"
            diff_output += result_unstaged.stdout

        if not diff_output:
            console.print(f"\n[{Colors.MUTED}]No uncommitted changes.[/{Colors.MUTED}]\n")
            return

        # Render diff with line numbers and syntax highlighting
        render_diff(diff_output, console)

    except FileNotFoundError:
        console.print(f"\n[{Colors.ERROR}]Git not found. Make sure git is installed.[/{Colors.ERROR}]\n")
    except Exception as e:
        console.print(f"\n[{Colors.ERROR}]Error running git diff: {e}[/{Colors.ERROR}]\n")

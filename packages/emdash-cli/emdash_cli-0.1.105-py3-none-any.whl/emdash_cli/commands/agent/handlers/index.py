"""Handler for /index command."""

import os
from pathlib import Path

from rich.console import Console

from ....design import print_error

console = Console()


def handle_index(args: str, client) -> None:
    """Handle /index command.

    Args:
        args: Command arguments (status, start, hook install/uninstall)
        client: EmdashClient instance
    """
    # Parse subcommand
    subparts = args.split(maxsplit=1) if args else []
    subcommand = subparts[0].lower() if subparts else "status"
    subargs = subparts[1].strip() if len(subparts) > 1 else ""

    repo_path = os.getcwd()

    if subcommand == "status":
        _show_status(client, repo_path)

    elif subcommand == "start":
        _start_index(client, repo_path, subargs)

    elif subcommand == "hook":
        _handle_hook(repo_path, subargs)

    else:
        console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")
        console.print("[dim]Usage: /index [status|start|hook][/dim]")
        console.print("[dim]  /index              - Show index status[/dim]")
        console.print("[dim]  /index start        - Start incremental indexing[/dim]")
        console.print("[dim]  /index start --full - Force full reindex[/dim]")
        console.print("[dim]  /index hook install - Install post-commit hook[/dim]")
        console.print("[dim]  /index hook uninstall - Remove post-commit hook[/dim]")


def _show_status(client, repo_path: str) -> None:
    """Show index status."""
    try:
        status = client.index_status(repo_path)

        console.print("\n[bold cyan]Index Status[/bold cyan]\n")
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
                console.print(f"  Last commit: {status.get('last_commit')[:8]}")

        # Check hook status
        hooks_dir = Path(repo_path) / ".git" / "hooks"
        hook_path = hooks_dir / "post-commit"
        if hook_path.exists() and "emdash" in hook_path.read_text():
            console.print(f"  Auto-index: [green]Enabled[/green] (post-commit hook)")
        else:
            console.print(f"  Auto-index: [dim]Disabled[/dim] (run /index hook install)")

        console.print()

    except Exception as e:
        print_error(e, "Error getting status")


def _start_index(client, repo_path: str, args: str) -> None:
    """Start indexing."""
    import json
    from rich.progress import Progress, BarColumn, TaskProgressColumn, TextColumn

    # Parse options
    full = "--full" in args

    console.print(f"\n[bold cyan]Indexing[/bold cyan] {repo_path}\n")

    try:
        with Progress(
            TextColumn("[bold cyan]{task.description}[/bold cyan]"),
            BarColumn(bar_width=40, complete_style="cyan", finished_style="green"),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Starting...", total=100)

            for line in client.index_start_stream(repo_path, not full):
                line = line.strip()
                if line.startswith("event: "):
                    continue
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        step = data.get("step") or data.get("message", "")
                        percent = data.get("percent")

                        if step:
                            progress.update(task, description=step)
                        if percent is not None:
                            progress.update(task, completed=percent)
                    except json.JSONDecodeError:
                        pass

            progress.update(task, completed=100, description="Complete")

        console.print("[bold green]Indexing complete![/bold green]\n")

    except Exception as e:
        print_error(e)


def _handle_hook(repo_path: str, args: str) -> None:
    """Handle hook install/uninstall."""
    action = args.lower() if args else ""

    if action not in ("install", "uninstall"):
        console.print("[yellow]Usage: /index hook [install|uninstall][/yellow]")
        return

    hooks_dir = Path(repo_path) / ".git" / "hooks"
    hook_path = hooks_dir / "post-commit"

    if not hooks_dir.exists():
        console.print(f"[red]Error:[/red] Not a git repository: {repo_path}")
        return

    hook_content = """#!/bin/sh
# emdash post-commit hook - auto-reindex on commit
# Installed by: emdash index hook install

# Run indexing in background to not block the commit
emdash index start > /dev/null 2>&1 &
"""

    if action == "install":
        if hook_path.exists():
            existing = hook_path.read_text()
            if "emdash" in existing:
                console.print("[yellow]Hook already installed[/yellow]")
                return
            else:
                console.print("[yellow]Appending to existing post-commit hook[/yellow]")
                with open(hook_path, "a") as f:
                    f.write("\n# emdash auto-index\nemdash index start > /dev/null 2>&1 &\n")
        else:
            hook_path.write_text(hook_content)

        hook_path.chmod(0o755)
        console.print(f"[green]Post-commit hook installed[/green]")
        console.print("[dim]Index will update automatically after each commit[/dim]")

    elif action == "uninstall":
        if not hook_path.exists():
            console.print("[yellow]No post-commit hook found[/yellow]")
            return

        existing = hook_path.read_text()
        if "emdash" not in existing:
            console.print("[yellow]No emdash hook found in post-commit[/yellow]")
            return

        if existing.strip() == hook_content.strip():
            hook_path.unlink()
            console.print("[green]Post-commit hook removed[/green]")
        else:
            lines = existing.split("\n")
            new_lines = [
                line for line in lines
                if "emdash" not in line and "auto-reindex" not in line
            ]
            hook_path.write_text("\n".join(new_lines))
            console.print("[green]Emdash hook lines removed from post-commit[/green]")

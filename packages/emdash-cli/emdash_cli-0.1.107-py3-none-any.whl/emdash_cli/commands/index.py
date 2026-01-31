"""Index command - parse and index a codebase."""

import json
import os

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from rich.table import Table

from ..client import EmdashClient
from ..server_manager import get_server_manager

console = Console()


@click.group()
def index():
    """Index a codebase into the knowledge graph."""
    pass


@index.command("start")
@click.argument("repo_path", required=False)
@click.option("--full", is_flag=True, help="Force full reindex (default: incremental)")
@click.option("--with-git", is_flag=True, help="Include git history (Layer B)")
@click.option("--with-github", is_flag=True, help="Include GitHub PRs (Layer C)")
@click.option("--github-prs", default=50, help="Number of GitHub PRs to index (when --with-github)")
@click.option("--detect-communities", is_flag=True, default=True, help="Run community detection")
@click.option("--describe-communities", is_flag=True, help="Use LLM to describe communities")
@click.option("--model", "-m", default=None, help="Model for community descriptions")
def index_start(
    repo_path: str | None,
    full: bool,
    with_git: bool,
    with_github: bool,
    github_prs: int,
    detect_communities: bool,
    describe_communities: bool,
    model: str | None,
):
    """Index a repository into the knowledge graph.

    If REPO_PATH is not provided, indexes the current directory.

    By default, indexes only code structure (Layer A - AST parsing).
    Git history (Layer B) and GitHub PRs (Layer C) are skipped unless enabled.

    Environment variables:
        EMDASH_INDEX_GIT=true      Enable git history indexing
        EMDASH_INDEX_GITHUB=true   Enable GitHub PR indexing

    Examples:
        emdash index start                    # Code only (Layer A)
        emdash index start --with-git         # Include git history
        emdash index start --with-github      # Include GitHub PRs
        emdash index start --full             # Force full reindex
    """
    # Default to current directory
    if not repo_path:
        repo_path = os.getcwd()

    # Ensure server is running
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    console.print(f"\n[bold cyan]Indexing[/bold cyan] {repo_path}\n")

    # Check environment variables for Layer B and C
    env_index_git = os.environ.get("EMDASH_INDEX_GIT", "").lower() == "true"
    env_index_github = os.environ.get("EMDASH_INDEX_GITHUB", "").lower() == "true"

    # Enable git/github if flag passed OR env var set
    index_git = with_git or env_index_git
    index_github = with_github or env_index_github

    # Build options
    # Incremental mode is default (changed_only=True), unless --full is passed
    options = {
        "changed_only": not full,
        "index_git": index_git,
        "index_github": github_prs if index_github else 0,
        "detect_communities": detect_communities,
        "describe_communities": describe_communities,
    }
    if model:
        options["model"] = model

    try:
        # Stream indexing progress with progress bar
        final_stats = {}

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

                        # Capture final stats from response event
                        if data.get("success") and data.get("stats"):
                            final_stats = data.get("stats", {})

                        if step:
                            progress.update(task, description=step)
                        if percent is not None:
                            progress.update(task, completed=percent)
                    except json.JSONDecodeError:
                        pass

            # Complete the progress bar
            progress.update(task, completed=100, description="Complete")

        # Show completion with sense of accomplishment
        _show_completion(repo_path, final_stats, client)

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise click.Abort()


def _show_completion(repo_path: str, stats: dict, client: EmdashClient) -> None:
    """Show a nice completion message with stats."""
    # If we don't have stats from the stream, fetch from status endpoint
    if not stats:
        try:
            status_data = client.index_status(repo_path)
            stats = {
                "files": status_data.get("file_count", 0),
                "functions": status_data.get("function_count", 0),
                "classes": status_data.get("class_count", 0),
                "communities": status_data.get("community_count", 0),
            }
        except Exception:
            stats = {}

    # Build completion message
    console.print()

    if stats:
        # Create a summary table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Label", style="dim")
        table.add_column("Value", style="bold")

        if stats.get("files"):
            table.add_row("Files", str(stats["files"]))
        if stats.get("functions"):
            table.add_row("Functions", str(stats["functions"]))
        if stats.get("classes"):
            table.add_row("Classes", str(stats["classes"]))
        if stats.get("communities"):
            table.add_row("Communities", str(stats["communities"]))

        panel = Panel(
            table,
            title="[bold green]Indexing Complete[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
        console.print(panel)
    else:
        console.print("[bold green]Indexing complete![/bold green]")

    console.print()


@index.command("hook")
@click.argument("action", type=click.Choice(["install", "uninstall"]))
@click.argument("repo_path", required=False)
def index_hook(action: str, repo_path: str | None):
    """Install or uninstall the post-commit hook for automatic indexing.

    The hook runs 'emdash index start' after each commit to keep the index updated.

    Examples:
        emdash index hook install             # Install in current repo
        emdash index hook install /path/repo  # Install in specific repo
        emdash index hook uninstall           # Remove the hook
    """
    from pathlib import Path

    # Default to current directory
    if not repo_path:
        repo_path = os.getcwd()

    hooks_dir = Path(repo_path) / ".git" / "hooks"
    hook_path = hooks_dir / "post-commit"

    if not hooks_dir.exists():
        console.print(f"[red]Error:[/red] Not a git repository: {repo_path}")
        raise click.Abort()

    hook_content = """#!/bin/sh
# emdash post-commit hook - auto-reindex on commit
# Installed by: emdash index hook install

# Run indexing in background to not block the commit
emdash index start > /dev/null 2>&1 &
"""

    if action == "install":
        # Check if hook already exists
        if hook_path.exists():
            existing = hook_path.read_text()
            if "emdash" in existing:
                console.print("[yellow]Hook already installed[/yellow]")
                return
            else:
                # Append to existing hook
                console.print("[yellow]Appending to existing post-commit hook[/yellow]")
                with open(hook_path, "a") as f:
                    f.write("\n# emdash auto-index\nemdash index start > /dev/null 2>&1 &\n")
        else:
            # Create new hook
            hook_path.write_text(hook_content)

        # Make executable
        hook_path.chmod(0o755)
        console.print(f"[green]Post-commit hook installed:[/green] {hook_path}")

    elif action == "uninstall":
        if not hook_path.exists():
            console.print("[yellow]No post-commit hook found[/yellow]")
            return

        existing = hook_path.read_text()
        if "emdash" not in existing:
            console.print("[yellow]No emdash hook found in post-commit[/yellow]")
            return

        # Check if it's our hook entirely or just contains our line
        if existing.strip() == hook_content.strip():
            # It's only our hook, remove the file
            hook_path.unlink()
            console.print("[green]Post-commit hook removed[/green]")
        else:
            # Remove just our lines
            lines = existing.split("\n")
            new_lines = [
                line for line in lines
                if "emdash" not in line and "auto-reindex" not in line
            ]
            hook_path.write_text("\n".join(new_lines))
            console.print("[green]Emdash hook lines removed from post-commit[/green]")


@index.command("status")
@click.argument("repo_path", required=False)
def index_status(repo_path: str | None):
    """Show current indexing status.

    If REPO_PATH is not provided, checks the current directory.

    Example:
        emdash index status
        emdash index status /path/to/repo
    """
    # Default to current directory
    if not repo_path:
        repo_path = os.getcwd()

    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        status = client.index_status(repo_path)

        console.print("\n[bold]Index Status[/bold]")
        console.print(f"  Indexed: {'[green]Yes[/green]' if status.get('is_indexed') else '[yellow]No[/yellow]'}")

        if status.get("is_indexed"):
            console.print(f"  Files: {status.get('file_count', 0)}")
            console.print(f"  Functions: {status.get('function_count', 0)}")
            console.print(f"  Classes: {status.get('class_count', 0)}")
            console.print(f"  Communities: {status.get('community_count', 0)}")

            if status.get("last_indexed"):
                console.print(f"  Last indexed: {status.get('last_indexed')}")
            if status.get("last_commit"):
                console.print(f"  Last commit: {status.get('last_commit')}")

        console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise click.Abort()

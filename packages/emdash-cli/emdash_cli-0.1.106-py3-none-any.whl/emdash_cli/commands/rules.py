"""Rules/templates management CLI commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..design import print_error

console = Console()


@click.group()
def rules():
    """Manage .emdash-rules templates."""
    pass


@rules.command("init")
@click.option("--global", "global_", is_flag=True, help="Save to ~/.emdash-rules instead of ./.emdash-rules")
@click.option("--force", is_flag=True, help="Overwrite existing templates")
def rules_init(global_: bool, force: bool):
    """Initialize custom templates in .emdash-rules directory."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.rules_init(global_templates=global_, force=force)

        if result.get("success"):
            path = result.get("path")
            templates = result.get("templates", [])
            console.print(f"[green]Templates initialized at {path}[/green]")
            console.print(f"[dim]Copied {len(templates)} templates[/dim]")
        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")

    except Exception as e:
        print_error(e)
        raise click.Abort()


@rules.command("show")
@click.argument("template", type=click.Choice(["spec", "tasks", "project", "focus", "pr-review"]))
def rules_show(template: str):
    """Show the active template and its source."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.rules_get(template)

        source = result.get("source", "unknown")
        content = result.get("content", "")

        console.print(Panel(
            content,
            title=f"[cyan]{template}[/cyan] [dim]({source})[/dim]",
            border_style="dim",
        ))

    except Exception as e:
        print_error(e)
        raise click.Abort()


@rules.command("list")
def rules_list():
    """List all templates and their active sources."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        templates = client.rules_list()

        table = Table(title="Templates")
        table.add_column("Name", style="cyan")
        table.add_column("Source")
        table.add_column("Description")

        for t in templates:
            table.add_row(
                t.get("name", ""),
                t.get("source", ""),
                t.get("description", ""),
            )

        console.print(table)

    except Exception as e:
        print_error(e)
        raise click.Abort()

"""Database CLI commands."""

import click
from rich.console import Console
from rich.table import Table

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..design import print_error

console = Console()


@click.group()
def db():
    """Database management commands."""
    pass


@db.command("init")
def db_init():
    """Initialize the Kuzu database schema."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.db_init()
        if result.get("success"):
            console.print("[green]Database schema initialized successfully![/green]")
        else:
            console.print(f"[red]Error: {result.get('message')}[/red]")
    except Exception as e:
        print_error(e)
        raise click.Abort()


@db.command("clear")
@click.confirmation_option(prompt="Are you sure you want to clear all data?")
def db_clear():
    """Clear all data from the database."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.db_clear(confirm=True)
        if result.get("success"):
            console.print("[green]Database cleared successfully![/green]")
        else:
            console.print(f"[red]Error: {result.get('message')}[/red]")
    except Exception as e:
        print_error(e)
        raise click.Abort()


@db.command("stats")
def db_stats():
    """Show database statistics."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        stats = client.db_stats()

        table = Table(title="Database Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right")

        table.add_row("Files", str(stats.get("file_count", 0)))
        table.add_row("Functions", str(stats.get("function_count", 0)))
        table.add_row("Classes", str(stats.get("class_count", 0)))
        table.add_row("Communities", str(stats.get("community_count", 0)))
        table.add_row("Total Nodes", str(stats.get("node_count", 0)))
        table.add_row("Relationships", str(stats.get("relationship_count", 0)))

        console.print(table)
    except Exception as e:
        print_error(e)
        raise click.Abort()


@db.command("test")
def db_test():
    """Test the database connection."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.db_test()
        if result.get("connected"):
            console.print("[green]Database connection successful![/green]")
            console.print(f"[dim]Path: {result.get('database_path')}[/dim]")
        else:
            console.print(f"[red]Connection failed: {result.get('message')}[/red]")
    except Exception as e:
        print_error(e)
        raise click.Abort()

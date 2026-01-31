"""Embedding management CLI commands."""

import click
from rich.console import Console
from rich.table import Table

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..design import print_error

console = Console()


@click.group()
def embed():
    """Embedding management commands."""
    pass


@embed.command("index")
@click.option("--prs/--no-prs", default=True, help="Index PR embeddings")
@click.option("--functions/--no-functions", default=True, help="Index function embeddings")
@click.option("--classes/--no-classes", default=True, help="Index class embeddings")
@click.option("--reindex", is_flag=True, help="Re-generate all embeddings")
def embed_index(prs: bool, functions: bool, classes: bool, reindex: bool):
    """Generate embeddings for graph entities."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        console.print("[cyan]Generating embeddings...[/cyan]")

        result = client.embed_index(
            include_prs=prs,
            include_functions=functions,
            include_classes=classes,
            reindex=reindex,
        )

        if result.get("success"):
            indexed = result.get("indexed", 0)
            skipped = result.get("skipped", 0)
            console.print(f"[green]Indexed {indexed} entities ({skipped} skipped)[/green]")
        else:
            console.print(f"[red]Error: {result.get('error')}[/red]")

    except Exception as e:
        print_error(e)
        raise click.Abort()


@embed.command("status")
def embed_status():
    """Show embedding coverage statistics."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        status = client.embed_status()

        table = Table(title="Embedding Coverage")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Total Entities", str(status.get("total_entities", 0)))
        table.add_row("Embedded", str(status.get("embedded_entities", 0)))
        table.add_row("Coverage", f"{status.get('coverage_percent', 0):.1f}%")
        table.add_row("PRs", str(status.get("pr_count", 0)))
        table.add_row("Functions", str(status.get("function_count", 0)))
        table.add_row("Classes", str(status.get("class_count", 0)))

        console.print(table)

    except Exception as e:
        print_error(e)
        raise click.Abort()


@embed.command("models")
def embed_models():
    """List all available embedding models."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        models = client.embed_models()

        table = Table(title="Available Embedding Models")
        table.add_column("Name", style="cyan")
        table.add_column("Dimension", justify="right")
        table.add_column("Description")

        for model in models:
            table.add_row(
                model.get("name", ""),
                str(model.get("dimension", 0)),
                model.get("description", ""),
            )

        console.print(table)

    except Exception as e:
        print_error(e)
        raise click.Abort()

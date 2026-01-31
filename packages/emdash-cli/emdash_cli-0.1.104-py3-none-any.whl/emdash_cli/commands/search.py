"""Search CLI command."""

import click
from rich.console import Console
from rich.table import Table

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..design import print_error

console = Console()


@click.command("search")
@click.argument("query")
@click.option("--semantic/--text", default=True, help="Use semantic search (default) or text search")
@click.option("--limit", default=20, help="Maximum results")
def search(query: str, semantic: bool, limit: int):
    """Search codebase by semantic similarity or text.

    Examples:
        emdash search "authentication flow"
        emdash search "login" --text
        emdash search "error handling" --limit 10
    """
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        search_type = "semantic" if semantic else "text"
        result = client.search(query=query, search_type=search_type, limit=limit)

        results = result.get("results", [])

        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        table = Table(title=f"Search Results ({len(results)})")
        table.add_column("Score", justify="right", style="dim")
        table.add_column("Type")
        table.add_column("Name", style="cyan")
        table.add_column("File")

        for r in results:
            table.add_row(
                f"{r.get('score', 0):.3f}",
                r.get("type", ""),
                r.get("name", ""),
                r.get("file", ""),
            )

        console.print(table)

    except Exception as e:
        print_error(e)
        raise click.Abort()

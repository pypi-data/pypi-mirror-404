"""Planning CLI commands."""

import json

import click
from rich.console import Console
from rich.table import Table

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..design import print_error

console = Console()


@click.group()
def plan():
    """Feature planning commands."""
    pass


@plan.command("context")
@click.argument("description")
@click.option("--similar-prs", default=5, help="Number of similar PRs to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def plan_context(description: str, similar_prs: int, output_json: bool):
    """Get planning context for a feature.

    Finds similar PRs and relevant code patterns to help plan
    the implementation of a new feature.

    Examples:
        emdash plan context "add dark mode toggle"
        emdash plan context "user authentication" --similar-prs 10
    """
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.plan_context(
            description=description,
            similar_prs=similar_prs,
        )

        if output_json:
            console.print(json.dumps(result, indent=2))
            return

        # Display similar PRs
        prs = result.get("similar_prs", [])
        if prs:
            table = Table(title="Similar PRs")
            table.add_column("Score", justify="right", style="dim")
            table.add_column("PR", style="cyan")
            table.add_column("Title")

            for pr in prs:
                table.add_row(
                    f"{pr.get('score', 0):.3f}",
                    f"#{pr.get('number', '')}",
                    pr.get("title", ""),
                )

            console.print(table)
        else:
            console.print("[dim]No similar PRs found[/dim]")

        # Display relevant patterns
        patterns = result.get("patterns", [])
        if patterns:
            console.print()
            console.print("[bold]Relevant Patterns[/bold]")
            for pattern in patterns:
                console.print(f"  • {pattern}")

    except Exception as e:
        print_error(e)
        raise click.Abort()

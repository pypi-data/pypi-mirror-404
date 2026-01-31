"""Team analysis CLI commands."""

import click
from rich.console import Console
from rich.markdown import Markdown

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..design import print_error

console = Console()


@click.group()
def team():
    """Team activity and collaboration analysis commands."""
    pass


@team.command("focus")
@click.option("--days", default=14, help="Days to look back")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def team_focus(days: int, model: str, output_json: bool):
    """Get team's recent focus and work-in-progress.

    Analyzes recent commits, PRs, and code changes to identify
    what the team is working on.

    Examples:
        emdash team focus
        emdash team focus --days 7
    """
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.team_focus(days=days, model=model)

        if output_json:
            import json
            console.print(json.dumps(result, indent=2))
        else:
            content = result.get("content", "")
            if content:
                console.print(Markdown(content))
            else:
                console.print("[yellow]No focus data available[/yellow]")

    except Exception as e:
        print_error(e)
        raise click.Abort()

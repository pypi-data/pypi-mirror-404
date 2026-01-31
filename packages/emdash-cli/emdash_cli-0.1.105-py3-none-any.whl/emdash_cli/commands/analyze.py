"""Analytics CLI commands."""

import click
from rich.console import Console
from rich.table import Table

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..design import print_error

console = Console()


@click.group()
def analyze():
    """Run graph analytics."""
    pass


@analyze.command("pagerank")
@click.option("--top", default=20, help="Number of results to show")
@click.option("--damping", default=0.85, help="Damping factor")
def analyze_pagerank(top: int, damping: float):
    """Compute PageRank scores to identify important code entities."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.analyze_pagerank(top=top, damping=damping)

        entities = result.get("entities", [])

        table = Table(title=f"Top {top} by PageRank")
        table.add_column("Rank", justify="right", style="dim")
        table.add_column("Entity", style="cyan")
        table.add_column("Type")
        table.add_column("Score", justify="right")

        for i, entity in enumerate(entities, 1):
            table.add_row(
                str(i),
                entity.get("name", ""),
                entity.get("type", ""),
                f"{entity.get('score', 0):.4f}",
            )

        console.print(table)

    except Exception as e:
        print_error(e)
        raise click.Abort()


@analyze.command("communities")
@click.option("--resolution", default=1.0, help="Resolution parameter")
@click.option("--min-size", default=3, help="Minimum community size")
@click.option("--top", default=20, help="Number of communities to show")
def analyze_communities(resolution: float, min_size: int, top: int):
    """Detect code communities using Louvain algorithm."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.analyze_communities(
            resolution=resolution,
            min_size=min_size,
            top=top,
        )

        communities = result.get("communities", [])

        table = Table(title=f"Top {top} Communities")
        table.add_column("ID", justify="right", style="dim")
        table.add_column("Size", justify="right")
        table.add_column("Members", style="cyan")

        for comm in communities:
            members = comm.get("members", [])
            member_str = ", ".join(members[:5])
            if len(members) > 5:
                member_str += f" (+{len(members) - 5} more)"

            table.add_row(
                str(comm.get("id", "")),
                str(comm.get("size", 0)),
                member_str,
            )

        console.print(table)

    except Exception as e:
        print_error(e)
        raise click.Abort()


@analyze.command("areas")
@click.option("--depth", default=2, help="Directory depth")
@click.option("--days", default=30, help="Days to look back for focus")
@click.option("--top", default=20, help="Number of results")
@click.option("--sort", type=click.Choice(["focus", "importance", "commits", "authors"]),
              default="focus", help="Sort metric")
@click.option("--files", is_flag=True, help="Show individual files instead of directories")
def analyze_areas(depth: int, days: int, top: int, sort: str, files: bool):
    """Get importance metrics by directory/area or individual files."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.analyze_areas(
            depth=depth,
            days=days,
            top=top,
            sort=sort,
            files=files,
        )

        areas = result.get("areas", [])

        title = f"Top {top} {'Files' if files else 'Areas'} by {sort.title()}"
        table = Table(title=title)
        table.add_column("Path", style="cyan")
        table.add_column("Commits", justify="right")
        table.add_column("Authors", justify="right")
        table.add_column("Focus %", justify="right")

        for area in areas:
            table.add_row(
                area.get("path", ""),
                str(area.get("commits", 0)),
                str(area.get("authors", 0)),
                f"{area.get('focus_pct', 0):.1f}%",
            )

        console.print(table)

    except Exception as e:
        print_error(e)
        raise click.Abort()

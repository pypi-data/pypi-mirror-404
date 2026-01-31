"""Tasks generation CLI command."""

import click
from rich.console import Console

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..sse_renderer import SSERenderer
from ..design import print_error

console = Console()


@click.command("tasks")
@click.argument("spec_name", required=False)
@click.option("--save", is_flag=True, help="Save tasks to spec directory")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--quiet", "-q", is_flag=True, help="Hide progress output")
def tasks(spec_name: str, save: bool, model: str, quiet: bool):
    """Generate implementation tasks from a specification.

    If spec_name is provided, loads the spec from specs/<spec_name>/spec.json.
    Otherwise, uses the most recent spec from the current session.

    Examples:
        emdash tasks
        emdash tasks "user-authentication" --save
    """
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())
    renderer = SSERenderer(console=console, verbose=not quiet)

    try:
        if spec_name:
            console.print(f"[cyan]Generating tasks for: {spec_name}[/cyan]")
        else:
            console.print("[cyan]Generating tasks from current spec...[/cyan]")
        console.print()

        stream = client.tasks_generate_stream(
            spec_name=spec_name,
            model=model,
            save=save,
        )
        renderer.render_stream(stream)

        if save:
            console.print()
            console.print("[green]Tasks saved[/green]")

    except Exception as e:
        print_error(e)
        raise click.Abort()

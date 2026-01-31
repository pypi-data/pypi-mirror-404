"""Spec generation CLI command."""

import click
from rich.console import Console

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..sse_renderer import SSERenderer
from ..design import print_error

console = Console()


@click.command("spec")
@click.argument("feature")
@click.option("--save", is_flag=True, help="Save spec to specs/<feature>/")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--quiet", "-q", is_flag=True, help="Hide exploration progress")
def spec(feature: str, save: bool, model: str, quiet: bool):
    """Generate a detailed specification for a feature.

    Explores the codebase to understand existing patterns and generates
    a comprehensive specification document.

    Examples:
        emdash spec "user authentication"
        emdash spec "dark mode toggle" --save
    """
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())
    renderer = SSERenderer(console=console, verbose=not quiet)

    try:
        console.print(f"[cyan]Generating spec for: {feature}[/cyan]")
        console.print()

        stream = client.spec_generate_stream(
            feature=feature,
            model=model,
            save=save,
        )
        renderer.render_stream(stream)

        if save:
            console.print()
            console.print(f"[green]Spec saved to specs/{feature}/[/green]")

    except Exception as e:
        print_error(e)
        raise click.Abort()

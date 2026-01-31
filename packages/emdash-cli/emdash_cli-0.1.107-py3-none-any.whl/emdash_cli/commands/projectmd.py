"""PROJECT.md generation CLI command."""

import click
from rich.console import Console

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..sse_renderer import SSERenderer
from ..design import print_error

console = Console()


@click.command("projectmd")
@click.option("--output", "-o", default="PROJECT.md", help="Output file path")
@click.option("--save/--no-save", default=True, help="Save to file")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--quiet", "-q", is_flag=True, help="Hide exploration progress")
def projectmd(output: str, save: bool, model: str, quiet: bool):
    """Generate PROJECT.md by exploring the codebase.

    Uses AI to analyze the code graph and generate a comprehensive
    project document that describes architecture, patterns, and
    key components.

    Examples:
        emdash projectmd
        emdash projectmd --output docs/PROJECT.md
        emdash projectmd --model gpt-4
    """
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())
    renderer = SSERenderer(console=console, verbose=not quiet)

    try:
        console.print("[cyan]Generating PROJECT.md...[/cyan]")
        console.print()

        stream = client.projectmd_generate_stream(
            output=output,
            save=save,
            model=model,
        )
        result = renderer.render_stream(stream)

        if save:
            console.print()
            console.print(f"[green]Saved to {output}[/green]")

    except Exception as e:
        print_error(e)
        raise click.Abort()

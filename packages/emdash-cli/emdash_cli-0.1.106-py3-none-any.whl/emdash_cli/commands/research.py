"""Research CLI command."""

import click
from rich.console import Console

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..sse_renderer import SSERenderer
from ..design import print_error

console = Console()


@click.command("research")
@click.argument("goal")
@click.option("--max-iterations", default=10, help="Maximum research iterations")
@click.option("--budget", default=50, help="Token budget (in thousands)")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--quiet", "-q", is_flag=True, help="Hide progress output")
def research(goal: str, max_iterations: int, budget: int, model: str, quiet: bool):
    """Deep research with multi-LLM loops and critic evaluation.

    Performs iterative research on a goal, using a planner, researcher,
    and critic to synthesize comprehensive answers.

    Examples:
        emdash research "How does authentication work?"
        emdash research "What are the main API endpoints?" --max-iterations 15
    """
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())
    renderer = SSERenderer(console=console, verbose=not quiet)

    try:
        console.print(f"[cyan]Researching: {goal}[/cyan]")
        console.print()

        stream = client.research_stream(
            goal=goal,
            max_iterations=max_iterations,
            budget=budget,
            model=model,
        )
        renderer.render_stream(stream)

    except Exception as e:
        print_error(e)
        raise click.Abort()

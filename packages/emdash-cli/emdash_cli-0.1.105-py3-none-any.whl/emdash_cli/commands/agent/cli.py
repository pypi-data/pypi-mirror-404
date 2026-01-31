"""Click CLI commands for the agent."""

import os

import click
from rich.console import Console

from ...client import EmdashClient
from ...server_manager import get_server_manager
from ...sse_renderer import SSERenderer
from .interactive import run_interactive, run_single_task

console = Console()


@click.group()
def agent():
    """AI agent commands."""
    pass


@agent.command("code")
@click.argument("task", required=False)
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--mode", type=click.Choice(["plan", "code"]), default="code",
              help="Starting mode")
@click.option("--quiet", "-q", is_flag=True, help="Less verbose output")
@click.option("--max-iterations", default=int(os.getenv("EMDASH_MAX_ITERATIONS", "100")), help="Max agent iterations")
@click.option("--no-graph-tools", is_flag=True, help="Skip graph exploration tools")
@click.option("--save", is_flag=True, help="Save specs to specs/<feature>/")
def agent_code(
    task: str | None,
    model: str | None,
    mode: str,
    quiet: bool,
    max_iterations: int,
    no_graph_tools: bool,
    save: bool,
):
    """Start the coding agent.

    With TASK: Run single task and exit
    Without TASK: Start interactive REPL mode

    MODES:
      plan   - Explore codebase and create plans (read-only)
      code   - Execute code changes (default)

    SLASH COMMANDS (in interactive mode):
      /plan   - Switch to plan mode
      /code   - Switch to code mode
      /help   - Show available commands
      /reset  - Reset session

    Examples:
        emdash                                         # Interactive code mode
        emdash agent code                              # Same as above
        emdash agent code --mode plan                  # Start in plan mode
        emdash agent code "Fix the login bug"          # Single task
    """
    # Get server URL (starts server if needed)
    server = get_server_manager()
    base_url = server.get_server_url()

    client = EmdashClient(base_url)
    renderer = SSERenderer(console=console, verbose=not quiet)

    options = {
        "mode": mode,
        "no_graph_tools": no_graph_tools,
        "save": save,
    }

    if task:
        # Single task mode
        run_single_task(client, renderer, task, model, max_iterations, options)
    else:
        # Interactive REPL mode
        run_interactive(client, renderer, model, max_iterations, options)


@agent.command("sessions")
def list_sessions():
    """List active agent sessions."""
    server = get_server_manager()
    base_url = server.get_server_url()

    client = EmdashClient(base_url)
    sessions = client.list_sessions()

    if not sessions:
        console.print("[dim]No active sessions[/dim]")
        return

    for s in sessions:
        console.print(
            f"  {s['session_id'][:8]}... "
            f"[dim]({s.get('model', 'unknown')}, "
            f"{s.get('message_count', 0)} messages)[/dim]"
        )

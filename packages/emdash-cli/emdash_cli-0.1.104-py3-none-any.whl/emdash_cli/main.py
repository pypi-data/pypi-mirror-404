"""Main CLI entry point for emdash-cli."""

import os
import subprocess
import sys

import click

from . import __version__
from .commands import (
    agent,
    db,
    auth,
    analyze,
    embed,
    index,
    plan,
    registry,
    rules,
    search,
    server,
    skills,
    team,
    projectmd,
    research,
    spec,
    tasks,
)


@click.group()
@click.version_option(version=__version__, prog_name="emdash")
def cli():
    """EmDash - The 'Senior Engineer' Context Engine.

    A graph-based coding intelligence system powered by AI.
    """
    pass


# Register command groups
cli.add_command(agent)
cli.add_command(db)
cli.add_command(auth)
cli.add_command(analyze)
cli.add_command(embed)
cli.add_command(index)
cli.add_command(plan)
cli.add_command(registry)
cli.add_command(rules)
cli.add_command(server)
cli.add_command(skills)
cli.add_command(team)

# Register standalone commands
cli.add_command(search)
cli.add_command(projectmd)
cli.add_command(research)
cli.add_command(spec)
cli.add_command(tasks)

# Add killall as top-level alias for server killall
from .commands.server import server_killall
cli.add_command(server_killall, name="killall")


# Update command - runs install.sh to update emdash
@click.command()
@click.option("--with-graph", is_flag=True, help="Install with graph database support")
@click.option("--reinstall", is_flag=True, help="Force reinstall (removes existing installation)")
def update(with_graph: bool, reinstall: bool):
    """Update emdash to the latest version.

    Downloads and runs the official install script from GitHub.

    Examples:
        emdash update              # Update to latest
        emdash update --with-graph # Update with graph support
        emdash update --reinstall  # Force reinstall
    """
    install_url = "https://raw.githubusercontent.com/mendyEdri/emdash.dev/main/scripts/install.sh"

    # Build command
    cmd = f"curl -sSL {install_url} | bash"
    if with_graph or reinstall:
        args = []
        if with_graph:
            args.append("--with-graph")
        if reinstall:
            args.append("--reinstall")
        cmd = f"curl -sSL {install_url} | bash -s -- {' '.join(args)}"

    click.echo("Updating emdash...")
    click.echo()

    # Run the install script
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
        )
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        click.echo("\nUpdate cancelled.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Update failed: {e}", err=True)
        sys.exit(1)


cli.add_command(update)


# Direct entry point for `em` command - wraps agent_code with click
@click.command()
@click.version_option(version=__version__, prog_name="em")
@click.argument("task", required=False)
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--mode", type=click.Choice(["plan", "tasks", "code"]), default="code",
              help="Starting mode")
@click.option("--quiet", "-q", is_flag=True, help="Less verbose output")
@click.option("--max-iterations", default=int(os.getenv("EMDASH_MAX_ITERATIONS", "100")), help="Max agent iterations")
@click.option("--no-graph-tools", is_flag=True, help="Skip graph exploration tools")
@click.option("--save", is_flag=True, help="Save specs to specs/<feature>/")
@click.option("--cli", is_flag=True, help="Use classic CLI mode (default is TUI)")
def start_coding_agent(
    task: str | None,
    model: str | None,
    mode: str,
    quiet: bool,
    max_iterations: int,
    no_graph_tools: bool,
    save: bool,
    cli: bool,
):
    """EmDash Coding Agent - AI-powered code assistant.

    Start interactive mode or run a single task.
    Default is TUI mode which supports native text selection.

    Examples:
        em                        # Interactive TUI mode
        em "Fix the login bug"    # Single task in TUI
        em --mode plan            # Start in plan mode
        em --cli                  # Classic CLI mode
    """
    # CLI mode (classic Rich-based interface)
    if cli:
        from .commands.agent import agent_code as _agent_code
        ctx = click.Context(_agent_code)
        ctx.invoke(
            _agent_code,
            task=task,
            model=model,
            mode=mode,
            quiet=quiet,
            max_iterations=max_iterations,
            no_graph_tools=no_graph_tools,
            save=save,
        )
        return

    # TUI mode is the default (Ink-based, supports native text selection)
    import asyncio
    from .tui_ink import run_ink_tui
    from .handlers import create_agent_handler

    # Get model from env or default
    model_name = model or os.getenv("EMDASH_MODEL", "claude-sonnet-4")

    # Create handler that connects to the agent
    handler = create_agent_handler(
        model=model_name,
        mode=mode,
        max_iterations=max_iterations,
    )

    # Run TUI
    asyncio.run(run_ink_tui(
        on_submit=handler,
        model=model_name,
        mode=mode,
    ))


# Direct entry point for `co` command - CoworkerAgent (non-coding)
# Uses the same server infrastructure as `em` but with agent_type=coworker
@click.command()
@click.version_option(version=__version__, prog_name="co")
@click.argument("task", required=False)
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--personality", "-p",
              type=click.Choice(["helpful_professional", "creative_collaborator",
                                "analytical_researcher", "friendly_coach"]),
              default="helpful_professional",
              help="Agent personality style")
@click.option("--context", "-c", default=None, help="Domain context (e.g., 'marketing team')")
@click.option("--quiet", "-q", is_flag=True, help="Less verbose output")
@click.option("--max-iterations", default=50, help="Max agent iterations")
def start_coworker_agent(
    task: str | None,
    model: str | None,
    personality: str,
    context: str | None,
    quiet: bool,
    max_iterations: int,
):
    """EmDash Coworker Agent - AI-powered general assistant.

    A non-coding assistant for research, planning, and collaboration.
    No file modifications or code execution - safe for general use.

    Personalities:
        helpful_professional  - Clear, practical, organized
        creative_collaborator - Creative, brainstorming-focused
        analytical_researcher - Thorough, evidence-based
        friendly_coach        - Supportive, encouraging

    Examples:
        co                                    # Interactive mode
        co "Research competitor products"     # Single task
        co -p creative_collaborator           # Creative mode
        co -c "marketing team" "Plan Q3"      # With domain context
    """
    from rich.console import Console

    from .client import EmdashClient
    from .server_manager import get_server_manager
    from .sse_renderer import SSERenderer
    from .commands.agent.interactive import run_interactive, run_single_task

    console = Console()

    # Get server URL (starts server if needed)
    server = get_server_manager()
    base_url = server.get_server_url()

    client = EmdashClient(base_url)
    renderer = SSERenderer(console=console, verbose=not quiet)

    # Build options with coworker-specific settings
    options = {
        "agent_type": "coworker",
        "personality": personality,
        "domain_context": f"You are helping a {context}." if context else None,
    }

    if task:
        # Single task mode
        run_single_task(client, renderer, task, model, max_iterations, options)
    else:
        # Interactive REPL mode (same as em but with coworker options)
        run_interactive(client, renderer, model, max_iterations, options)


if __name__ == "__main__":
    cli()

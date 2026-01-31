"""Handler for /registry command."""

from rich.console import Console

console = Console()


def handle_registry(args: str) -> None:
    """Handle /registry command.

    Args:
        args: Command arguments (list, show, install, search)
    """
    from emdash_cli.commands.registry import (
        _show_registry_wizard,
        _fetch_registry,
        registry_list,
        registry_show,
        registry_install,
        registry_search,
    )

    # Parse subcommand
    subparts = args.split(maxsplit=1) if args else []
    subcommand = subparts[0].lower() if subparts else ""
    subargs = subparts[1] if len(subparts) > 1 else ""

    # Component types as shortcuts for list
    component_types = ["skills", "rules", "agents", "verifiers"]

    if subcommand == "" or subcommand == "wizard":
        # Show interactive wizard (default)
        _show_registry_wizard()

    elif subcommand in component_types:
        # Shortcut: /registry agents -> /registry list agents
        registry_list.callback(subcommand)

    elif subcommand == "list":
        # List components
        component_type = subargs if subargs else None
        if component_type and component_type not in ["skills", "rules", "agents", "verifiers"]:
            console.print(f"[yellow]Unknown type: {component_type}[/yellow]")
            console.print("[dim]Types: skills, rules, agents, verifiers[/dim]")
            return
        # Invoke click command
        registry_list.callback(component_type)

    elif subcommand == "show":
        if not subargs:
            console.print("[yellow]Usage: /registry show type:name[/yellow]")
            console.print("[dim]Example: /registry show skill:frontend-design[/dim]")
            return
        registry_show.callback(subargs)

    elif subcommand == "install":
        if not subargs:
            console.print("[yellow]Usage: /registry install type:name [type:name ...][/yellow]")
            console.print("[dim]Example: /registry install skill:frontend-design rule:typescript[/dim]")
            return
        component_ids = tuple(subargs.split())
        registry_install.callback(component_ids)

    elif subcommand == "search":
        if not subargs:
            console.print("[yellow]Usage: /registry search query[/yellow]")
            console.print("[dim]Example: /registry search frontend[/dim]")
            return
        # Simple search without tag filtering from slash command
        registry_search.callback(subargs, ())

    else:
        console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")
        console.print("[dim]Usage: /registry [list|show|install|search|<type>][/dim]")
        console.print("[dim]  /registry           - Interactive wizard[/dim]")
        console.print("[dim]  /registry list      - List all components[/dim]")
        console.print("[dim]  /registry agents    - List agents (shortcut)[/dim]")
        console.print("[dim]  /registry skills    - List skills (shortcut)[/dim]")
        console.print("[dim]  /registry rules     - List rules (shortcut)[/dim]")
        console.print("[dim]  /registry verifiers - List verifiers (shortcut)[/dim]")
        console.print("[dim]  /registry show x:y  - Show component details[/dim]")
        console.print("[dim]  /registry install x:y - Install components[/dim]")
        console.print("[dim]  /registry search q  - Search registry[/dim]")

"""Handler for /hooks command."""

import hashlib
from pathlib import Path

from rich.console import Console

from ....design import print_error

console = Console()


def handle_hooks(args: str) -> None:
    """Handle /hooks command.

    Args:
        args: Command arguments
    """
    from emdash_core.agent.hooks import HookManager, HookConfig, HookEventType

    manager = HookManager(Path.cwd())

    # Parse subcommand
    subparts = args.split(maxsplit=1) if args else []
    subcommand = subparts[0].lower() if subparts else "list"
    subargs = subparts[1].strip() if len(subparts) > 1 else ""

    if subcommand == "list" or subcommand == "":
        # List all hooks
        hooks = manager.get_hooks()
        if hooks:
            console.print("\n[bold cyan]Configured Hooks[/bold cyan]\n")
            for hook in hooks:
                status = "[green]enabled[/green]" if hook.enabled else "[dim]disabled[/dim]"
                console.print(f"  [cyan]{hook.id}[/cyan] ({status})")
                console.print(f"    Event: [yellow]{hook.event.value}[/yellow]")
                console.print(f"    Command: [dim]{hook.command}[/dim]")
            console.print()
            console.print(f"[dim]Config file: {manager.hooks_file_path}[/dim]\n")
        else:
            console.print("\n[dim]No hooks configured.[/dim]")
            console.print("[dim]Add with: /hooks add <event> <command>[/dim]")
            console.print(f"[dim]Events: {', '.join(e.value for e in HookEventType)}[/dim]\n")

    elif subcommand == "add":
        # Add a new hook: /hooks add <event> <command>
        if not subargs:
            console.print("[yellow]Usage: /hooks add <event> <command>[/yellow]")
            console.print(f"[dim]Events: {', '.join(e.value for e in HookEventType)}[/dim]")
            console.print("[dim]Example: /hooks add session_end notify-send 'Agent done'[/dim]")
        else:
            # Parse event and command
            add_parts = subargs.split(maxsplit=1)
            if len(add_parts) < 2:
                console.print("[yellow]Usage: /hooks add <event> <command>[/yellow]")
            else:
                event_str = add_parts[0].lower()
                hook_command = add_parts[1]

                # Validate event type
                try:
                    event_type = HookEventType(event_str)
                except ValueError:
                    console.print(f"[red]Invalid event: {event_str}[/red]")
                    console.print(f"[dim]Valid events: {', '.join(e.value for e in HookEventType)}[/dim]")
                    return

                # Generate a unique ID
                hook_id = f"hook-{hashlib.md5(f'{event_str}{hook_command}'.encode()).hexdigest()[:8]}"

                try:
                    hook = HookConfig(
                        id=hook_id,
                        event=event_type,
                        command=hook_command,
                        enabled=True,
                    )
                    manager.add_hook(hook)
                    console.print(f"[green]Added hook '{hook_id}'[/green]")
                    console.print(f"[dim]Event: {event_type.value}, Command: {hook_command}[/dim]")
                except ValueError as e:
                    print_error(e)

    elif subcommand == "remove":
        if not subargs:
            console.print("[yellow]Usage: /hooks remove <hook-id>[/yellow]")
        else:
            if manager.remove_hook(subargs):
                console.print(f"[green]Removed hook '{subargs}'[/green]")
            else:
                console.print(f"[yellow]Hook '{subargs}' not found[/yellow]")

    elif subcommand == "toggle":
        if not subargs:
            console.print("[yellow]Usage: /hooks toggle <hook-id>[/yellow]")
        else:
            new_state = manager.toggle_hook(subargs)
            if new_state is not None:
                state_str = "[green]enabled[/green]" if new_state else "[dim]disabled[/dim]"
                console.print(f"Hook '{subargs}' is now {state_str}")
            else:
                console.print(f"[yellow]Hook '{subargs}' not found[/yellow]")

    elif subcommand == "events":
        # List available event types
        console.print("\n[bold cyan]Available Hook Events[/bold cyan]\n")
        event_descriptions = {
            HookEventType.TOOL_START: "Triggered before a tool executes",
            HookEventType.TOOL_RESULT: "Triggered after a tool completes",
            HookEventType.SESSION_START: "Triggered when agent session starts",
            HookEventType.SESSION_END: "Triggered when agent session ends",
            HookEventType.RESPONSE: "Triggered when agent produces a response",
            HookEventType.ERROR: "Triggered when an error occurs",
        }
        for event_type in HookEventType:
            desc = event_descriptions.get(event_type, "")
            console.print(f"  [cyan]{event_type.value}[/cyan]")
            console.print(f"    [dim]{desc}[/dim]")
        console.print()

    else:
        console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")
        console.print("[dim]Usage: /hooks [list|add|remove|toggle|events][/dim]")

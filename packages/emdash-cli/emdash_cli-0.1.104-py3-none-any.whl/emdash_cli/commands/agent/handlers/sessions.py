"""Handler for /session command."""

from pathlib import Path

from rich.console import Console

from ..menus import show_sessions_interactive_menu, confirm_session_delete
from ..constants import AgentMode

console = Console()


def handle_session(
    args: str,
    client,
    model: str | None,
    session_id_ref: list,
    current_spec_ref: list,
    current_mode_ref: list,
    loaded_messages_ref: list,
) -> None:
    """Handle /session command.

    Args:
        args: Command arguments
        client: EmdashClient instance
        model: Current model
        session_id_ref: Reference to session_id (list wrapper for mutation)
        current_spec_ref: Reference to current_spec (list wrapper for mutation)
        current_mode_ref: Reference to current_mode (list wrapper for mutation)
        loaded_messages_ref: Reference to loaded_messages (list wrapper for mutation)
    """
    from ....session_store import SessionStore

    store = SessionStore(Path.cwd())

    # Parse subcommand
    subparts = args.split(maxsplit=1) if args else []
    subcommand = subparts[0].lower() if subparts else ""
    subargs = subparts[1].strip() if len(subparts) > 1 else ""

    def _load_session(name: str) -> bool:
        """Load a session by name. Returns True if successful."""
        session_data = store.load_session(name)
        if session_data:
            session_id_ref[0] = None
            current_spec_ref[0] = session_data.spec
            if session_data.mode == "plan":
                current_mode_ref[0] = AgentMode.PLAN
            else:
                current_mode_ref[0] = AgentMode.CODE
            loaded_messages_ref[0] = session_data.messages
            store.set_active_session(name)
            console.print(f"[green]Loaded session '{name}'[/green]")
            console.print(f"[dim]{len(session_data.messages)} messages restored, mode: {current_mode_ref[0].value}[/dim]")
            if current_spec_ref[0]:
                console.print("[dim]Spec restored[/dim]")
            return True
        else:
            console.print(f"[yellow]Session '{name}' not found[/yellow]")
            return False

    def _delete_session(name: str) -> bool:
        """Delete a session by name with confirmation."""
        if confirm_session_delete(name):
            success, msg = store.delete_session(name)
            if success:
                console.print(f"[green]{msg}[/green]")
                return True
            else:
                console.print(f"[yellow]{msg}[/yellow]")
        else:
            console.print("[dim]Cancelled[/dim]")
        return False

    if subcommand == "" or subcommand == "list":
        # Interactive menu (or list if no sessions)
        sessions = store.list_sessions()
        if sessions:
            if subcommand == "list":
                # Just list, don't show interactive menu
                console.print("\n[bold cyan]Saved Sessions[/bold cyan]\n")
                for s in sessions:
                    mode_color = "green" if s.mode == "code" else "yellow"
                    active_marker = " [bold green]*[/bold green]" if store.get_active_session() == s.name else ""
                    console.print(f"  [cyan]{s.name}[/cyan]{active_marker} [{mode_color}]{s.mode}[/{mode_color}]")
                    console.print(f"    [dim]{s.message_count} messages | {s.updated_at[:10]}[/dim]")
                    if s.summary:
                        summary = s.summary[:60] + "..." if len(s.summary) > 60 else s.summary
                        console.print(f"    [dim]{summary}[/dim]")
                console.print()
            else:
                # Interactive menu
                while True:
                    action, session_name = show_sessions_interactive_menu(
                        sessions, store.get_active_session()
                    )
                    if action == "cancel":
                        break
                    elif action == "load":
                        _load_session(session_name)
                        break
                    elif action == "delete":
                        if _delete_session(session_name):
                            # Refresh sessions list
                            sessions = store.list_sessions()
                            if not sessions:
                                console.print("\n[dim]No more sessions.[/dim]\n")
                                break
                    # Continue showing menu
        else:
            console.print("\n[dim]No saved sessions.[/dim]")
            console.print("[dim]Save with: /session save <name>[/dim]\n")

    elif subcommand == "save":
        if not subargs:
            console.print("[yellow]Usage: /session save <name>[/yellow]")
            console.print("[dim]Example: /session save auth-feature[/dim]")
        else:
            # Get current messages from the API session
            if session_id_ref[0]:
                try:
                    export_resp = client.get(f"/api/agent/chat/{session_id_ref[0]}/export")
                    if export_resp.status_code == 200:
                        data = export_resp.json()
                        messages = data.get("messages", [])
                    else:
                        messages = []
                except Exception:
                    messages = []
            else:
                messages = []

            success, msg = store.save_session(
                name=subargs,
                messages=messages,
                mode=current_mode_ref[0].value,
                spec=current_spec_ref[0],
                model=model,
            )
            if success:
                store.set_active_session(subargs)
                console.print(f"[green]{msg}[/green]")
            else:
                console.print(f"[yellow]{msg}[/yellow]")

    elif subcommand == "load":
        if not subargs:
            console.print("[yellow]Usage: /session load <name>[/yellow]")
        else:
            _load_session(subargs)

    elif subcommand == "delete":
        if not subargs:
            console.print("[yellow]Usage: /session delete <name>[/yellow]")
        else:
            _delete_session(subargs)

    elif subcommand == "clear":
        session_id_ref[0] = None
        current_spec_ref[0] = None
        loaded_messages_ref[0] = []
        store.set_active_session(None)
        console.print("[green]Session cleared[/green]")

    else:
        console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")
        console.print("[dim]Usage: /session [list|save|load|delete|clear] [name][/dim]")

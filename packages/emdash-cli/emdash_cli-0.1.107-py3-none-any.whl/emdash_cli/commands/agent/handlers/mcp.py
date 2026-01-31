"""Handler for /mcp command."""

import json
import os
import subprocess
from pathlib import Path

from rich.console import Console

from ....design import print_error

console = Console()


def handle_mcp(args: str) -> None:
    """Handle /mcp command.

    Args:
        args: Command arguments
    """
    from emdash_core.agent.mcp.manager import get_mcp_manager
    from emdash_core.agent.mcp.config import get_default_mcp_config_path

    manager = get_mcp_manager(config_path=get_default_mcp_config_path(Path.cwd()))

    # Parse subcommand
    subparts = args.split(maxsplit=1) if args else []
    subcommand = subparts[0].lower() if subparts else ""

    def _show_mcp_interactive():
        """Show interactive MCP server list with toggle."""
        from prompt_toolkit import Application
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import Layout, Window, FormattedTextControl
        from prompt_toolkit.styles import Style

        servers = manager.list_servers()
        if not servers:
            console.print("\n[dim]No global MCP servers configured.[/dim]")
            console.print(f"[dim]Edit {manager.config_path} to add servers[/dim]\n")
            return None

        selected_index = [0]
        server_names = [s["name"] for s in servers]

        kb = KeyBindings()

        @kb.add("up")
        @kb.add("k")
        def move_up(event):
            selected_index[0] = (selected_index[0] - 1) % len(servers)

        @kb.add("down")
        @kb.add("j")
        def move_down(event):
            selected_index[0] = (selected_index[0] + 1) % len(servers)

        @kb.add("enter")
        @kb.add("space")
        def toggle_server(event):
            # Toggle the selected server's enabled status
            server_name = server_names[selected_index[0]]
            config_path = manager.config_path

            # Read current config
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
            else:
                config = {"mcpServers": {}}

            # Toggle enabled status
            if server_name in config.get("mcpServers", {}):
                current = config["mcpServers"][server_name].get("enabled", True)
                config["mcpServers"][server_name]["enabled"] = not current

                # Save config
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2)

                # Reload manager
                manager.reload_config()

                # Update local servers list
                servers[:] = manager.list_servers()

        @kb.add("e")
        def edit_config(event):
            event.app.exit(result="edit")

        @kb.add("q")
        @kb.add("escape")
        def quit_menu(event):
            event.app.exit()

        def get_formatted_content():
            lines = []
            lines.append(("class:title", "Global MCP Servers\n"))
            lines.append(("class:dim", f"Config: {manager.config_path}\n\n"))

            for i, server in enumerate(servers):
                if server["enabled"]:
                    if server["running"]:
                        status = "running"
                        status_style = "class:running"
                    else:
                        status = "enabled"
                        status_style = "class:enabled"
                else:
                    status = "disabled"
                    status_style = "class:disabled"

                if i == selected_index[0]:
                    lines.append(("class:selected", f"  > {server['name']}"))
                else:
                    lines.append(("class:normal", f"    {server['name']}"))

                lines.append((status_style, f" ({status})\n"))

            lines.append(("class:hint", "\n↑/↓ navigate • Enter toggle • e edit • q quit"))
            return lines

        style = Style.from_dict({
            "title": "#00cc66 bold",
            "dim": "#888888",
            "selected": "#00cc66 bold",
            "normal": "#cccccc",
            "running": "#00cc66",
            "enabled": "#cccc00",
            "disabled": "#888888",
            "hint": "#888888 italic",
        })

        layout = Layout(Window(FormattedTextControl(get_formatted_content)))
        app = Application(layout=layout, key_bindings=kb, style=style, full_screen=False)

        result = app.run()
        if result == "edit":
            return "edit"
        return None

    if subcommand == "" or subcommand == "list":
        # Show interactive menu (default)
        result = _show_mcp_interactive()
        if result == "edit":
            subcommand = "edit"
        else:
            # Don't continue to edit
            subcommand = "done"

    if subcommand == "edit":
        # Open MCP config in editor
        config_path = manager.config_path

        # Create default config if it doesn't exist
        if not config_path.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text('{\n  "mcpServers": {}\n}\n')
            console.print(f"[dim]Created {config_path}[/dim]")

        editor = os.environ.get("EDITOR", "")
        if not editor:
            for ed in ["code", "vim", "nano", "vi"]:
                try:
                    subprocess.run(["which", ed], capture_output=True, check=True)
                    editor = ed
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

        if editor:
            console.print(f"[dim]Opening {config_path} in {editor}...[/dim]")
            try:
                subprocess.run([editor, str(config_path)])
                manager.reload_config()
                console.print("[dim]Config reloaded[/dim]")
            except Exception as e:
                print_error(e, "Failed to open editor")
        else:
            console.print(f"[yellow]No editor found. Edit manually:[/yellow]")
            console.print(f"  {config_path}")

    elif subcommand != "done":
        console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")
        console.print("[dim]Usage: /mcp [list|edit][/dim]")

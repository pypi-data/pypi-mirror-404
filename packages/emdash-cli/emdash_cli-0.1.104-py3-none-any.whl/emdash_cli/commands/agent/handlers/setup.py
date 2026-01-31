"""Setup wizard for configuring rules, agents, skills, and verifiers.

This is a dedicated flow separate from the main agent interaction,
specialized for configuration management with its own permissions.
"""

import json
from pathlib import Path
from enum import Enum

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from ....design import print_error

console = Console()


class SetupMode(Enum):
    """Available setup modes."""
    RULES = "rules"
    AGENTS = "agents"
    SKILLS = "skills"
    VERIFIERS = "verifiers"


# Templates for each config type
TEMPLATES = {
    SetupMode.RULES: {
        "file": ".emdash/rules.md",
        "example": """# Project Rules

## Code Style
- Use TypeScript for all new code
- Follow the existing patterns in the codebase

## Testing
- Write tests for all new features
- Maintain >80% code coverage
""",
        "description": "Rules guide the agent's behavior and coding standards",
    },
    SetupMode.AGENTS: {
        "dir": ".emdash/agents",
        "example": """---
name: {name}
description: {description}
tools:
  - read_file
  - edit_file
  - bash
---

You are a specialized agent for {purpose}.

## Your Role
{role_description}

## Guidelines
- Follow project conventions
- Be concise and accurate
""",
        "description": "Custom agents with specialized system prompts and tools",
    },
    SetupMode.SKILLS: {
        "dir": ".emdash/skills",
        "example": """---
name: {name}
description: {description}
---

## Skill: {name}

When this skill is invoked, you should:

1. {step1}
2. {step2}
3. {step3}

## Output Format
{output_format}
""",
        "description": "Reusable skills that can be invoked with /skill-name",
    },
    SetupMode.VERIFIERS: {
        "file": ".emdash/verifiers.json",
        "example": {
            "verifiers": [
                {"type": "command", "name": "tests", "command": "npm test", "timeout": 120},
                {"type": "command", "name": "lint", "command": "npm run lint"},
                {"type": "llm", "name": "review", "prompt": "Review for bugs and issues", "model": "haiku"}
            ],
            "max_retries": 3
        },
        "description": "Verification checks (commands or LLM reviews) to validate work",
    },
}


def show_setup_menu() -> SetupMode | None:
    """Show the main setup menu and return selected mode."""
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    options = [
        (SetupMode.RULES, "Rules", "Define coding standards and guidelines for the agent"),
        (SetupMode.AGENTS, "Agents", "Create custom agents with specialized prompts"),
        (SetupMode.SKILLS, "Skills", "Add reusable skills invokable via slash commands"),
        (SetupMode.VERIFIERS, "Verifiers", "Set up verification checks for your work"),
        (None, "Quit", "Exit setup wizard"),
    ]

    selected_index = [0]
    result = [None]

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_index[0] = (selected_index[0] - 1) % len(options)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_index[0] = (selected_index[0] + 1) % len(options)

    @kb.add("enter")
    def select(event):
        result[0] = options[selected_index[0]][0]
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    @kb.add("q")
    def cancel(event):
        result[0] = None
        event.app.exit()

    def get_formatted_menu():
        lines = [
            ("class:title", "Emdash Setup Wizard\n"),
            ("class:subtitle", "Configure your project's rules, agents, skills, and verifiers.\n\n"),
        ]

        for i, (mode, name, desc) in enumerate(options):
            is_selected = i == selected_index[0]
            prefix = "❯ " if is_selected else "  "

            if mode is None:  # Quit option
                if is_selected:
                    lines.append(("class:quit-selected", f"{prefix}{name}\n"))
                else:
                    lines.append(("class:quit", f"{prefix}{name}\n"))
            else:
                if is_selected:
                    lines.append(("class:item-selected", f"{prefix}{name}"))
                    lines.append(("class:desc-selected", f"  {desc}\n"))
                else:
                    lines.append(("class:item", f"{prefix}{name}"))
                    lines.append(("class:desc", f"  {desc}\n"))

        lines.append(("class:hint", "\n↑/↓ navigate • Enter select • q quit"))
        return lines

    style = Style.from_dict({
        "title": "#00ccff bold",
        "subtitle": "#888888",
        "item": "#00ccff",
        "item-selected": "#00cc66 bold",
        "desc": "#666666",
        "desc-selected": "#00cc66",
        "quit": "#888888",
        "quit-selected": "#ff6666 bold",
        "hint": "#888888 italic",
    })

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_menu),
                height=len(options) + 5,
            ),
        ])
    )

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        full_screen=False,
    )

    console.print()

    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        result[0] = None

    console.print()
    return result[0]


def show_action_menu(mode: SetupMode) -> str | None:
    """Show action menu for a mode (add/edit/list/delete)."""
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    options = [
        ("add", "Add new", f"Create a new {mode.value[:-1]}"),
        ("edit", "Edit existing", f"Modify an existing {mode.value[:-1]}"),
        ("list", "List all", f"Show all configured {mode.value}"),
        ("delete", "Delete", f"Remove a {mode.value[:-1]}"),
        ("back", "Back", "Return to main menu"),
    ]

    selected_index = [0]
    result = [None]

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_index[0] = (selected_index[0] - 1) % len(options)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_index[0] = (selected_index[0] + 1) % len(options)

    @kb.add("enter")
    def select(event):
        result[0] = options[selected_index[0]][0]
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    @kb.add("b")
    def go_back(event):
        result[0] = "back"
        event.app.exit()

    def get_formatted_menu():
        lines = [
            ("class:title", f"{mode.value.title()} Configuration\n\n"),
        ]

        for i, (action, name, desc) in enumerate(options):
            is_selected = i == selected_index[0]
            prefix = "❯ " if is_selected else "  "

            if action == "back":
                if is_selected:
                    lines.append(("class:back-selected", f"{prefix}{name}\n"))
                else:
                    lines.append(("class:back", f"{prefix}{name}\n"))
            else:
                if is_selected:
                    lines.append(("class:item-selected", f"{prefix}{name}"))
                    lines.append(("class:desc-selected", f"  {desc}\n"))
                else:
                    lines.append(("class:item", f"{prefix}{name}"))
                    lines.append(("class:desc", f"  {desc}\n"))

        lines.append(("class:hint", "\n↑/↓ navigate • Enter select • b back"))
        return lines

    style = Style.from_dict({
        "title": "#00ccff bold",
        "item": "#00ccff",
        "item-selected": "#00cc66 bold",
        "desc": "#666666",
        "desc-selected": "#00cc66",
        "back": "#888888",
        "back-selected": "#ffcc00 bold",
        "hint": "#888888 italic",
    })

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_menu),
                height=len(options) + 4,
            ),
        ])
    )

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        full_screen=False,
    )

    console.print()

    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        result[0] = "back"

    console.print()
    return result[0]


def get_existing_items(mode: SetupMode) -> list[str]:
    """Get list of existing items for a mode."""
    cwd = Path.cwd()

    if mode == SetupMode.RULES:
        rules_file = cwd / ".emdash" / "rules.md"
        return ["rules.md"] if rules_file.exists() else []

    elif mode == SetupMode.AGENTS:
        agents_dir = cwd / ".emdash" / "agents"
        if agents_dir.exists():
            return [f.stem for f in agents_dir.glob("*.md")]
        return []

    elif mode == SetupMode.SKILLS:
        skills_dir = cwd / ".emdash" / "skills"
        if skills_dir.exists():
            return [f.stem for f in skills_dir.glob("*.md")]
        return []

    elif mode == SetupMode.VERIFIERS:
        verifiers_file = cwd / ".emdash" / "verifiers.json"
        if verifiers_file.exists():
            try:
                data = json.loads(verifiers_file.read_text())
                return [v.get("name", "unnamed") for v in data.get("verifiers", [])]
            except Exception:
                pass
        return []

    return []


def list_items(mode: SetupMode) -> None:
    """List existing items for a mode."""
    items = get_existing_items(mode)

    console.print()
    if not items:
        console.print(f"[yellow]No {mode.value} configured yet.[/yellow]")
    else:
        console.print(f"[bold]Existing {mode.value}:[/bold]")
        for item in items:
            console.print(f"  • {item}")
    console.print()


def run_ai_assisted_setup(
    mode: SetupMode,
    action: str,
    client,
    renderer,
    model: str,
    item_name: str | None = None,
) -> bool:
    """Run AI-assisted setup flow for creating/editing config.

    Args:
        mode: The setup mode (rules, agents, skills, verifiers)
        action: The action (add, edit)
        client: EmDash client
        renderer: SSE renderer
        model: Model to use
        item_name: Name of item to edit (for edit action)

    Returns:
        True if successful, False otherwise
    """
    cwd = Path.cwd()
    template = TEMPLATES[mode]

    # Build the system context for the AI
    if mode == SetupMode.RULES:
        target_file = cwd / ".emdash" / "rules.md"
        current_content = target_file.read_text() if target_file.exists() else None
        file_info = f"File: `{target_file}`"

    elif mode == SetupMode.AGENTS:
        if action == 'add':
            # Prompt for agent name
            ps = PromptSession()
            console.print()
            item_name = ps.prompt("Agent name: ").strip()
            if not item_name:
                console.print("[yellow]Agent name is required[/yellow]")
                return False

        target_file = cwd / ".emdash" / "agents" / f"{item_name}.md"
        current_content = target_file.read_text() if target_file.exists() else None
        file_info = f"File: `{target_file}`"

    elif mode == SetupMode.SKILLS:
        if action == 'add':
            ps = PromptSession()
            console.print()
            item_name = ps.prompt("Skill name: ").strip()
            if not item_name:
                console.print("[yellow]Skill name is required[/yellow]")
                return False

        target_file = cwd / ".emdash" / "skills" / f"{item_name}.md"
        current_content = target_file.read_text() if target_file.exists() else None
        file_info = f"File: `{target_file}`"

    elif mode == SetupMode.VERIFIERS:
        target_file = cwd / ".emdash" / "verifiers.json"
        current_content = target_file.read_text() if target_file.exists() else None
        file_info = f"File: `{target_file}`"

    # Build initial message for AI
    example = template["example"]
    if isinstance(example, dict):
        example = json.dumps(example, indent=2)

    if action == 'add' and current_content:
        action_desc = "add to or modify"
    elif action == 'add':
        action_desc = "create"
    else:
        action_desc = "modify"

    initial_message = f"""I want to {action_desc} my {mode.value} configuration.

{file_info}

**What {mode.value} do:** {template['description']}

**Example format:**
```
{example}
```
"""

    if current_content:
        initial_message += f"""
**Current content:**
```
{current_content}
```
"""

    initial_message += """
Help me configure this. Ask me what I want to achieve, then create/update the file using the Edit or Write tool.

IMPORTANT: You have permission to write to the .emdash/ directory. Use the Write tool to create the file."""

    # Run interactive AI session
    console.print()
    console.print(Panel(
        f"[bold cyan]AI-Assisted {mode.value.title()} Setup[/bold cyan]\n\n"
        f"Chat with the AI to configure your {mode.value}.\n"
        "Type [bold]done[/bold] when finished, [bold]cancel[/bold] to abort.",
        border_style="cyan",
    ))
    console.print()

    # Start the AI conversation
    session_id = None
    ps = PromptSession(history=InMemoryHistory())

    # Send initial message
    try:
        stream = client.agent_chat_stream(
            message=initial_message,
            model=model,
            max_iterations=10,
            options={"mode": "code"},
        )

        # Render with interrupt support - function defined at end of this file
        result = render_with_interrupt(renderer, stream, client=client)

        if result and result.get("session_id"):
            session_id = result["session_id"]

    except Exception as e:
        print_error(e)
        return False

    # Interactive loop
    while True:
        try:
            console.print()
            user_input = ps.prompt("[setup] > ").strip()

            if not user_input:
                continue

            if user_input.lower() in ('done', 'finish', 'exit'):
                console.print()
                console.print("[green]Setup complete![/green]")
                return True

            if user_input.lower() in ('cancel', 'abort', 'quit'):
                console.print()
                console.print("[yellow]Setup cancelled.[/yellow]")
                return False

            # Continue the conversation
            if session_id:
                stream = client.agent_continue_stream(session_id, user_input)
            else:
                stream = client.agent_chat_stream(
                    message=user_input,
                    model=model,
                    max_iterations=10,
                    options={"mode": "code"},
                )

            result = render_with_interrupt(renderer, stream, client=client)

            if result and result.get("session_id"):
                session_id = result["session_id"]

        except KeyboardInterrupt:
            console.print()
            console.print("[yellow]Setup interrupted.[/yellow]")
            return False
        except EOFError:
            break

    return True


def select_item_to_edit(mode: SetupMode) -> str | None:
    """Let user select an item to edit."""
    items = get_existing_items(mode)

    if not items:
        console.print(f"[yellow]No {mode.value} to edit. Create one first.[/yellow]")
        return None

    console.print()
    console.print(f"[bold]Select {mode.value[:-1]} to edit:[/bold]")
    for i, item in enumerate(items, 1):
        console.print(f"  [cyan]{i}[/cyan]. {item}")
    console.print()

    try:
        ps = PromptSession()
        choice = ps.prompt(f"Select [1-{len(items)}]: ").strip()

        idx = int(choice) - 1
        if 0 <= idx < len(items):
            return items[idx]
        else:
            console.print("[yellow]Invalid choice[/yellow]")
            return None
    except (ValueError, KeyboardInterrupt, EOFError):
        return None


def select_item_to_delete(mode: SetupMode) -> str | None:
    """Let user select an item to delete."""
    items = get_existing_items(mode)

    if not items:
        console.print(f"[yellow]No {mode.value} to delete.[/yellow]")
        return None

    console.print()
    console.print(f"[bold]Select {mode.value[:-1]} to delete:[/bold]")
    for i, item in enumerate(items, 1):
        console.print(f"  [cyan]{i}[/cyan]. {item}")
    console.print()

    try:
        ps = PromptSession()
        choice = ps.prompt(f"Select [1-{len(items)}]: ").strip()

        idx = int(choice) - 1
        if 0 <= idx < len(items):
            return items[idx]
        else:
            console.print("[yellow]Invalid choice[/yellow]")
            return None
    except (ValueError, KeyboardInterrupt, EOFError):
        return None


def delete_item(mode: SetupMode, item_name: str) -> bool:
    """Delete an item."""
    cwd = Path.cwd()

    try:
        if mode == SetupMode.RULES:
            target = cwd / ".emdash" / "rules.md"
            if target.exists():
                target.unlink()
                console.print(f"[green]Deleted rules.md[/green]")
                return True

        elif mode == SetupMode.AGENTS:
            target = cwd / ".emdash" / "agents" / f"{item_name}.md"
            if target.exists():
                target.unlink()
                console.print(f"[green]Deleted agent: {item_name}[/green]")
                return True

        elif mode == SetupMode.SKILLS:
            target = cwd / ".emdash" / "skills" / f"{item_name}.md"
            if target.exists():
                target.unlink()
                console.print(f"[green]Deleted skill: {item_name}[/green]")
                return True

        elif mode == SetupMode.VERIFIERS:
            target = cwd / ".emdash" / "verifiers.json"
            if target.exists():
                data = json.loads(target.read_text())
                data["verifiers"] = [
                    v for v in data.get("verifiers", [])
                    if v.get("name") != item_name
                ]
                target.write_text(json.dumps(data, indent=2))
                console.print(f"[green]Deleted verifier: {item_name}[/green]")
                return True

        console.print(f"[yellow]Item not found: {item_name}[/yellow]")
        return False

    except Exception as e:
        print_error(e, "Error deleting")
        return False


def render_with_interrupt(renderer, stream, client=None) -> dict:
    """Render stream with interrupt support.

    This is a simplified version for the setup wizard.

    Args:
        renderer: SSE renderer instance
        stream: SSE stream iterator
        client: Optional API client for abort support
    """
    import threading
    from ....keyboard import KeyListener

    interrupt_event = threading.Event()

    def on_escape():
        interrupt_event.set()

    listener = KeyListener(on_escape)

    try:
        listener.start()
        result = renderer.render_stream(stream, interrupt_event=interrupt_event)

        # If interrupted and we have a client, call abort to stop the server-side agent
        if result.get("interrupted") and client and result.get("session_id"):
            try:
                client.abort_chat(result["session_id"])
            except Exception:
                pass  # Ignore abort errors - agent may have already stopped

        return result
    finally:
        listener.stop()


def handle_setup(
    args: str,
    client,
    renderer,
    model: str,
) -> None:
    """Handle /setup command - open the setup wizard.

    Args:
        args: Command arguments (unused currently)
        client: EmDash client for AI interactions
        renderer: SSE renderer
        model: Model to use for AI assistance
    """
    console.print()
    console.print("[bold cyan]━━━ Setup Wizard ━━━[/bold cyan]")

    while True:
        # Show main menu
        mode = show_setup_menu()
        if mode is None:
            console.print()
            console.print("[dim]Exiting setup wizard.[/dim]")
            break

        # Show action menu
        while True:
            action = show_action_menu(mode)

            if action is None or action == 'back':
                break

            if action == 'list':
                list_items(mode)

            elif action == 'add':
                run_ai_assisted_setup(mode, 'add', client, renderer, model)

            elif action == 'edit':
                item = select_item_to_edit(mode)
                if item:
                    run_ai_assisted_setup(mode, 'edit', client, renderer, model, item)

            elif action == 'delete':
                item = select_item_to_delete(mode)
                if item:
                    # Confirm deletion
                    ps = PromptSession()
                    confirm = ps.prompt(f"Delete '{item}'? [y/N]: ").strip().lower()
                    if confirm in ('y', 'yes'):
                        delete_item(mode, item)

    console.print()

"""Handler for /rules command."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from ....design import (
    Colors,
    header,
    footer,
    SEPARATOR_WIDTH,
    STATUS_ACTIVE,
    ARROW_PROMPT,
    print_error,
)

console = Console()


def get_rules_dir() -> Path:
    """Get the rules directory path."""
    return Path.cwd() / ".emdash" / "rules"


def list_rules() -> list[dict]:
    """List all rules files.

    Returns:
        List of dicts with name, file_path, and preview
    """
    rules_dir = get_rules_dir()
    rules = []

    if not rules_dir.exists():
        return rules

    for md_file in sorted(rules_dir.glob("*.md")):
        try:
            content = md_file.read_text().strip()
            # Get first non-empty line as preview
            lines = [l for l in content.split("\n") if l.strip()]
            preview = lines[0][:60] + "..." if lines and len(lines[0]) > 60 else (lines[0] if lines else "")
            # Remove markdown heading prefix
            if preview.startswith("#"):
                preview = preview.lstrip("#").strip()

            rules.append({
                "name": md_file.stem,
                "file_path": str(md_file),
                "preview": preview,
            })
        except Exception:
            rules.append({
                "name": md_file.stem,
                "file_path": str(md_file),
                "preview": "(error reading file)",
            })

    return rules


def show_rules_interactive_menu() -> tuple[str, str]:
    """Show interactive rules menu.

    Returns:
        Tuple of (action, rule_name) where action is one of:
        - 'view': View rule details
        - 'create': Create new rule
        - 'delete': Delete rule
        - 'cancel': User cancelled
    """
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    rules = list_rules()

    # Build menu items: (name, preview, is_action)
    menu_items = []

    for rule in rules:
        menu_items.append((rule["name"], rule["preview"], False))

    # Add action items at the bottom
    menu_items.append(("+ Create New Rule", "Create a new rule with AI assistance", True))

    if not menu_items:
        menu_items.append(("+ Create New Rule", "Create a new rule with AI assistance", True))

    selected_index = [0]
    result = [("cancel", "")]

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_index[0] = (selected_index[0] - 1) % len(menu_items)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_index[0] = (selected_index[0] + 1) % len(menu_items)

    @kb.add("enter")
    def select(event):
        item = menu_items[selected_index[0]]
        name, preview, is_action = item
        if is_action:
            if "Create" in name:
                result[0] = ("create", "")
        else:
            result[0] = ("view", name)
        event.app.exit()

    @kb.add("d")
    def delete_rule(event):
        item = menu_items[selected_index[0]]
        name, preview, is_action = item
        if not is_action:
            result[0] = ("delete", name)
            event.app.exit()

    @kb.add("n")
    def new_rule(event):
        result[0] = ("create", "")
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    @kb.add("q")
    def cancel(event):
        result[0] = ("cancel", "")
        event.app.exit()

    def get_formatted_menu():
        lines = [("class:title", f"─── Rules {'─' * 35}\n\n")]

        if not rules:
            lines.append(("class:dim", "  No rules defined yet.\n\n"))

        for i, (name, preview, is_action) in enumerate(menu_items):
            is_selected = i == selected_index[0]
            prefix = "▸ " if is_selected else "  "

            if is_action:
                if is_selected:
                    lines.append(("class:action-selected", f"  {prefix}{name}\n"))
                else:
                    lines.append(("class:action", f"  {prefix}{name}\n"))
            else:
                if is_selected:
                    lines.append(("class:rule-selected", f"  {prefix}{name}"))
                    lines.append(("class:preview-selected", f"  {preview}\n"))
                else:
                    lines.append(("class:rule", f"  {prefix}{name}"))
                    lines.append(("class:preview", f"  {preview}\n"))

        lines.append(("class:hint", f"\n{'─' * 45}\n  ↑↓ navigate  Enter view  n new  d delete  q quit"))
        return lines

    style = Style.from_dict({
        "title": f"{Colors.MUTED}",
        "dim": f"{Colors.DIM}",
        "rule": f"{Colors.PRIMARY}",
        "rule-selected": f"{Colors.SUCCESS} bold",
        "action": f"{Colors.WARNING}",
        "action-selected": f"{Colors.WARNING} bold",
        "preview": f"{Colors.DIM}",
        "preview-selected": f"{Colors.SUCCESS}",
        "hint": f"{Colors.DIM}",
    })

    height = len(menu_items) + 5  # items + title + hint + padding

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_menu),
                height=height,
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
        result[0] = ("cancel", "")

    # Clear menu visually with separator
    console.print()

    return result[0]


def show_rule_details(name: str) -> None:
    """Show detailed view of a rule."""
    rules_dir = get_rules_dir()
    rule_file = rules_dir / f"{name}.md"

    console.print()
    console.print(f"[{Colors.MUTED}]{header(name, SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    if rule_file.exists():
        try:
            content = rule_file.read_text()
            console.print(f"  [{Colors.DIM}]file[/{Colors.DIM}]  {rule_file}")
            console.print()

            # Show content with indentation
            for line in content.split('\n'):
                if line.startswith('#'):
                    console.print(f"  [{Colors.PRIMARY}]{line}[/{Colors.PRIMARY}]")
                else:
                    console.print(f"  [{Colors.MUTED}]{line}[/{Colors.MUTED}]")

        except Exception as e:
            console.print(f"  [{Colors.ERROR}]Error reading rule: {e}[/{Colors.ERROR}]")
    else:
        console.print(f"  [{Colors.WARNING}]Rule '{name}' not found[/{Colors.WARNING}]")

    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")


def confirm_delete(rule_name: str) -> bool:
    """Confirm rule deletion."""
    from prompt_toolkit import PromptSession

    console.print()
    console.print(f"[yellow]Delete rule '{rule_name}'?[/yellow]")
    console.print("[dim]This will remove the rule file. Type 'yes' to confirm.[/dim]")

    try:
        session = PromptSession()
        response = session.prompt("Confirm > ").strip().lower()
        return response in ("yes", "y")
    except (KeyboardInterrupt, EOFError):
        return False


def delete_rule(name: str) -> bool:
    """Delete a rule file."""
    rules_dir = get_rules_dir()
    rule_file = rules_dir / f"{name}.md"

    if not rule_file.exists():
        console.print(f"[yellow]Rule file not found: {rule_file}[/yellow]")
        return False

    if confirm_delete(name):
        rule_file.unlink()
        console.print(f"[green]Deleted rule: {name}[/green]")
        return True
    else:
        console.print("[dim]Cancelled[/dim]")
        return False


def chat_create_rule(client, renderer, model, max_iterations, render_with_interrupt) -> None:
    """Start a chat session to create a new rule with AI assistance."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style

    rules_dir = get_rules_dir()

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Create Rule', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.DIM}]Describe your rule. AI will help write it.[/{Colors.DIM}]")
    console.print(f"  [{Colors.DIM}]Type 'done' to finish.[/{Colors.DIM}]")
    console.print()

    chat_style = Style.from_dict({
        "prompt": f"{Colors.PRIMARY} bold",
    })

    ps = PromptSession(style=chat_style)
    chat_session_id = None
    first_message = True

    # Ensure rules directory exists
    rules_dir.mkdir(parents=True, exist_ok=True)

    # Chat loop
    while True:
        try:
            user_input = ps.prompt([("class:prompt", "› ")]).strip()

            if not user_input:
                continue

            if user_input.lower() in ("done", "quit", "exit", "q"):
                console.print("[dim]Finished[/dim]")
                break

            # First message includes context about rules
            if first_message:
                message_with_context = f"""I want to create a new rule file for my project.

**Rules directory:** `{rules_dir}`

Rules are markdown files that define guidelines for the AI agent. They are stored in `.emdash/rules/` and get injected into the agent's system prompt.

Example rule file:
```markdown
# Code Style Guidelines

- Use meaningful variable names
- Keep functions small and focused
- Add comments for complex logic
```

**My request:** {user_input}

Please help me create a rule file. Ask me questions if needed to understand what rules I want, then use the Write tool to create the file at `{rules_dir}/<rule-name>.md`."""
                stream = client.agent_chat_stream(
                    message=message_with_context,
                    model=model,
                    max_iterations=max_iterations,
                    options={"mode": "code"},
                )
                first_message = False
            elif chat_session_id:
                stream = client.agent_continue_stream(
                    chat_session_id, user_input
                )
            else:
                stream = client.agent_chat_stream(
                    message=user_input,
                    model=model,
                    max_iterations=max_iterations,
                    options={"mode": "code"},
                )

            result = render_with_interrupt(renderer, stream)
            if result and result.get("session_id"):
                chat_session_id = result["session_id"]

        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print("[dim]Cancelled[/dim]")
            break
        except Exception as e:
            print_error(e)


def handle_rules(args: str, client, renderer, model, max_iterations, render_with_interrupt) -> None:
    """Handle /rules command."""
    from prompt_toolkit import PromptSession

    # Handle subcommands
    if args:
        subparts = args.split(maxsplit=1)
        subcommand = subparts[0].lower()
        subargs = subparts[1] if len(subparts) > 1 else ""

        if subcommand == "list":
            rules = list_rules()
            if rules:
                console.print("\n[bold cyan]Rules[/bold cyan]\n")
                for rule in rules:
                    console.print(f"  [cyan]{rule['name']}[/cyan] - {rule['preview']}")
                console.print()
            else:
                console.print("\n[dim]No rules defined yet.[/dim]")
                console.print(f"[dim]Rules directory: {get_rules_dir()}[/dim]\n")
        elif subcommand == "show" and subargs:
            show_rule_details(subargs.strip())
        elif subcommand == "delete" and subargs:
            delete_rule(subargs.strip())
        elif subcommand == "add" or subcommand == "create" or subcommand == "new":
            chat_create_rule(client, renderer, model, max_iterations, render_with_interrupt)
        else:
            console.print("[yellow]Usage: /rules [list|show|add|delete] [name][/yellow]")
            console.print("[dim]Or just /rules for interactive menu[/dim]")
    else:
        # Interactive menu
        while True:
            action, rule_name = show_rules_interactive_menu()

            if action == "cancel":
                break
            elif action == "view":
                show_rule_details(rule_name)
                # After viewing, show options
                try:
                    console.print("[red]'d'[/red] delete • [dim]Enter back[/dim]", end="")
                    ps = PromptSession()
                    resp = ps.prompt(" ").strip().lower()
                    if resp == 'd':
                        delete_rule(rule_name)
                    console.print()
                except (KeyboardInterrupt, EOFError):
                    break
            elif action == "create":
                chat_create_rule(client, renderer, model, max_iterations, render_with_interrupt)
                # Refresh menu after creating
            elif action == "delete":
                delete_rule(rule_name)

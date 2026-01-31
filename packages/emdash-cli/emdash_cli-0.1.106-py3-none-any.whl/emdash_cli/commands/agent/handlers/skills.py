"""Handler for /skills command."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from ....design import print_error

console = Console()


def _get_skills_dir() -> Path:
    """Get the skills directory path."""
    return Path.cwd() / ".emdash" / "skills"


def _get_builtin_skills_dir() -> Path:
    """Get the built-in skills directory."""
    try:
        from emdash_core.agent.skills import _get_builtin_skills_dir as get_builtin
        return get_builtin()
    except ImportError:
        return Path()


def list_skills() -> list[dict]:
    """List all skills (both user and built-in).

    Returns:
        List of dicts with name, description, user_invocable, is_builtin, file_path, scripts
    """
    from emdash_core.agent.skills import SkillRegistry

    skills_dir = _get_skills_dir()
    registry = SkillRegistry.get_instance()
    registry.load_skills(skills_dir)

    all_skills = registry.get_all_skills()
    skills = []

    for skill in all_skills.values():
        skills.append({
            "name": skill.name,
            "description": skill.description,
            "user_invocable": skill.user_invocable,
            "is_builtin": getattr(skill, "_builtin", False),
            "file_path": str(skill.file_path) if skill.file_path else None,
            "scripts": [str(s) for s in skill.scripts] if skill.scripts else [],
        })

    return skills


def show_skills_interactive_menu() -> tuple[str, str]:
    """Show interactive skills menu.

    Returns:
        Tuple of (action, skill_name) where action is one of:
        - 'view': View skill details
        - 'create': Create new skill
        - 'delete': Delete skill
        - 'cancel': User cancelled
    """
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    skills = list_skills()

    # Build menu items: (name, description, is_builtin, is_action)
    menu_items = []

    for skill in skills:
        builtin_marker = " [built-in]" if skill["is_builtin"] else ""
        scripts_marker = f" [{len(skill['scripts'])} scripts]" if skill.get("scripts") else ""
        menu_items.append((skill["name"], skill["description"] + builtin_marker + scripts_marker, skill["is_builtin"], False))

    # Add action items at the bottom
    menu_items.append(("+ Create New Skill", "Create a new skill with AI assistance", False, True))

    if not menu_items:
        menu_items.append(("+ Create New Skill", "Create a new skill with AI assistance", False, True))

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
        name, desc, is_builtin, is_action = item
        if is_action:
            if "Create" in name:
                result[0] = ("create", "")
        else:
            result[0] = ("view", name)
        event.app.exit()

    @kb.add("d")
    def delete_skill(event):
        item = menu_items[selected_index[0]]
        name, desc, is_builtin, is_action = item
        if not is_action and not is_builtin:
            result[0] = ("delete", name)
            event.app.exit()
        elif is_builtin:
            # Can't delete built-in skills
            pass

    @kb.add("n")
    def new_skill(event):
        result[0] = ("create", "")
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    @kb.add("q")
    def cancel(event):
        result[0] = ("cancel", "")
        event.app.exit()

    def get_formatted_menu():
        lines = [("class:title", "Skills\n\n")]

        if not skills:
            lines.append(("class:dim", "No skills defined yet.\n\n"))

        for i, (name, desc, is_builtin, is_action) in enumerate(menu_items):
            is_selected = i == selected_index[0]
            prefix = ">" if is_selected else "  "

            if is_action:
                if is_selected:
                    lines.append(("class:action-selected", f"{prefix}{name}\n"))
                else:
                    lines.append(("class:action", f"{prefix}{name}\n"))
            else:
                if is_selected:
                    lines.append(("class:skill-selected", f"{prefix}{name}"))
                    lines.append(("class:desc-selected", f" - {desc}\n"))
                else:
                    lines.append(("class:skill", f"{prefix}{name}"))
                    lines.append(("class:desc", f" - {desc}\n"))

        lines.append(("class:hint", "\n[up]/[down] navigate | Enter view | n new | d delete | q quit"))
        return lines

    style = Style.from_dict({
        "title": "#00ccff bold",
        "dim": "#666666",
        "skill": "#00ccff",
        "skill-selected": "#00cc66 bold",
        "action": "#ffcc00",
        "action-selected": "#ffcc00 bold",
        "desc": "#666666",
        "desc-selected": "#00cc66",
        "hint": "#888888 italic",
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


def show_skill_details(name: str) -> None:
    """Show detailed view of a skill."""
    from emdash_core.agent.skills import SkillRegistry

    skills_dir = _get_skills_dir()
    registry = SkillRegistry.get_instance()
    registry.load_skills(skills_dir)

    skill = registry.get_skill(name)

    console.print()
    console.print("[dim]" + "-" * 50 + "[/dim]")
    console.print()

    if skill:
        builtin_marker = " [built-in]" if getattr(skill, "_builtin", False) else ""
        invocable = f"Yes (/{skill.name})" if skill.user_invocable else "No"
        tools = ", ".join(skill.tools) if skill.tools else "None"

        console.print(f"[bold cyan]{skill.name}[/bold cyan]{builtin_marker}\n")
        console.print(f"[bold]Description:[/bold] {skill.description}")
        console.print(f"[bold]User Invocable:[/bold] {invocable}")
        console.print(f"[bold]Tools:[/bold] {tools}")

        # Show scripts
        if skill.scripts:
            console.print(f"[bold]Scripts:[/bold] {len(skill.scripts)}")
            for script in skill.scripts:
                console.print(f"  [yellow]{script.name}[/yellow]: {script}")
        else:
            console.print(f"[bold]Scripts:[/bold] None")

        console.print(f"[bold]File:[/bold] {skill.file_path}\n")
        console.print("[bold]Instructions:[/bold]")
        console.print(Panel(skill.instructions, border_style="dim"))
    else:
        console.print(f"[yellow]Skill '{name}' not found[/yellow]")

    console.print()
    console.print("[dim]" + "-" * 50 + "[/dim]")


def confirm_delete(skill_name: str) -> bool:
    """Confirm skill deletion."""
    from prompt_toolkit import PromptSession

    console.print()
    console.print(f"[yellow]Delete skill '{skill_name}'?[/yellow]")
    console.print("[dim]This will remove the skill directory. Type 'yes' to confirm.[/dim]")

    try:
        session = PromptSession()
        response = session.prompt("Confirm > ").strip().lower()
        return response in ("yes", "y")
    except (KeyboardInterrupt, EOFError):
        return False


def delete_skill(name: str) -> bool:
    """Delete a skill directory."""
    import shutil

    skills_dir = _get_skills_dir()
    skill_dir = skills_dir / name

    if not skill_dir.exists():
        console.print(f"[yellow]Skill directory not found: {skill_dir}[/yellow]")
        return False

    # Check if it's a built-in skill
    from emdash_core.agent.skills import SkillRegistry
    registry = SkillRegistry.get_instance()
    registry.load_skills(skills_dir)
    skill = registry.get_skill(name)

    if skill and getattr(skill, "_builtin", False):
        console.print(f"[red]Cannot delete built-in skill '{name}'[/red]")
        return False

    if confirm_delete(name):
        shutil.rmtree(skill_dir)
        console.print(f"[green]Deleted skill: {name}[/green]")
        return True
    else:
        console.print("[dim]Cancelled[/dim]")
        return False


def chat_create_skill(client, renderer, model, max_iterations, render_with_interrupt) -> None:
    """Start a chat session to create a new skill with AI assistance."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style

    skills_dir = _get_skills_dir()

    console.print()
    console.print("[bold cyan]Create New Skill[/bold cyan]")
    console.print("[dim]Describe what skill you want to create. The AI will help you write it.[/dim]")
    console.print("[dim]Type 'done' to finish, Ctrl+C to cancel[/dim]")
    console.print()

    chat_style = Style.from_dict({
        "prompt": "#00cc66 bold",
    })

    ps = PromptSession(style=chat_style)
    chat_session_id = None
    first_message = True

    # Ensure skills directory exists
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Chat loop
    while True:
        try:
            user_input = ps.prompt([("class:prompt", "> ")]).strip()

            if not user_input:
                continue

            if user_input.lower() in ("done", "quit", "exit", "q"):
                console.print("[dim]Finished[/dim]")
                break

            # First message includes context about skills
            if first_message:
                message_with_context = f"""I want to create a new skill for my AI agent.

**Skills directory:** `{skills_dir}`

Skills are markdown files (SKILL.md) with YAML frontmatter that define reusable instructions for the agent.

SKILL.md format:
```markdown
---
name: skill-name
description: When to use this skill
user_invocable: true
tools: [tool1, tool2]
---

# Skill Title

Instructions for the skill...

## Scripts (optional)

If scripts are included, document them here.
```

**Frontmatter fields:**
- `name`: Unique skill identifier (lowercase, hyphens allowed)
- `description`: Brief description of when to use this skill
- `user_invocable`: Whether skill can be invoked with /name (true/false)
- `tools`: List of tools this skill needs (optional)

**Skill Scripts (optional):**
Skills can include executable bash scripts in the same directory as SKILL.md. These scripts:
- Must be self-contained bash executables (with shebang like `#!/bin/bash`)
- Are automatically discovered and made available to the agent
- Can be named anything (e.g., `run.sh`, `deploy.sh`, `validate.sh`)
- Are executed by the agent using the Bash tool when needed

Example script (`run.sh`):
```bash
#!/bin/bash
set -e
echo "Running skill script..."
# Add script logic here
```

**My request:** {user_input}

Please help me create a skill. Ask me questions if needed to understand what I want:
1. What should the skill do?
2. Does it need any scripts to execute code?

Then use the Write tool to create:
1. The SKILL.md file at `{skills_dir}/<skill-name>/SKILL.md`
2. Any scripts the user wants (e.g., `{skills_dir}/<skill-name>/run.sh`)

Remember to make scripts executable by including the shebang."""
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


def handle_skills(args: str, client, renderer, model, max_iterations, render_with_interrupt) -> None:
    """Handle /skills command."""
    from prompt_toolkit import PromptSession

    # Handle subcommands
    if args:
        subparts = args.split(maxsplit=1)
        subcommand = subparts[0].lower()
        subargs = subparts[1] if len(subparts) > 1 else ""

        if subcommand == "list":
            skills = list_skills()
            if skills:
                console.print("\n[bold cyan]Skills[/bold cyan]\n")
                for skill in skills:
                    builtin = " [built-in]" if skill["is_builtin"] else ""
                    invocable = f" (/{skill['name']})" if skill["user_invocable"] else ""
                    console.print(f"  [cyan]{skill['name']}[/cyan]{builtin}{invocable} - {skill['description']}")
                console.print()
            else:
                console.print("\n[dim]No skills defined yet.[/dim]")
                console.print(f"[dim]Skills directory: {_get_skills_dir()}[/dim]\n")
        elif subcommand == "show" and subargs:
            show_skill_details(subargs.strip())
        elif subcommand == "delete" and subargs:
            delete_skill(subargs.strip())
        elif subcommand in ("add", "create", "new"):
            chat_create_skill(client, renderer, model, max_iterations, render_with_interrupt)
        else:
            console.print("[yellow]Usage: /skills [list|show|add|delete] [name][/yellow]")
            console.print("[dim]Or just /skills for interactive menu[/dim]")
    else:
        # Interactive menu
        while True:
            action, skill_name = show_skills_interactive_menu()

            if action == "cancel":
                break
            elif action == "view":
                show_skill_details(skill_name)
                # After viewing, show options
                try:
                    # Check if it's a built-in skill
                    from emdash_core.agent.skills import SkillRegistry
                    registry = SkillRegistry.get_instance()
                    skill = registry.get_skill(skill_name)
                    is_builtin = skill and getattr(skill, "_builtin", False)

                    if is_builtin:
                        console.print("[dim]Enter to go back[/dim]", end="")
                    else:
                        console.print("[red]'d'[/red] delete • [dim]Enter back[/dim]", end="")
                    ps = PromptSession()
                    resp = ps.prompt(" ").strip().lower()
                    if resp == 'd' and not is_builtin:
                        delete_skill(skill_name)
                    console.print()
                except (KeyboardInterrupt, EOFError):
                    break
            elif action == "create":
                chat_create_skill(client, renderer, model, max_iterations, render_with_interrupt)
                # Refresh menu after creating
            elif action == "delete":
                delete_skill(skill_name)

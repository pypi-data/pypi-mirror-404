"""Registry CLI commands for browsing and installing community components."""

import json
import shutil
from pathlib import Path
from typing import Literal

import click
import httpx
from rich.console import Console

from ..design import (
    Colors,
    header,
    footer,
    SEPARATOR_WIDTH,
    STATUS_ACTIVE,
)

console = Console()

# GitHub raw URL base for the registry
GITHUB_REPO = "mendyEdri/emdash-registry"
GITHUB_BRANCH = "main"
REGISTRY_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"


ComponentType = Literal["skill", "rule", "agent", "verifier"]


def _fetch_registry() -> dict | None:
    """Fetch the registry.json from GitHub."""
    url = f"{REGISTRY_BASE_URL}/registry.json"
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        console.print(f"  [{Colors.ERROR}]error:[/{Colors.ERROR}] Failed to fetch registry: {e}")
        return None


def _fetch_component(path: str) -> str | None:
    """Fetch a component file from GitHub."""
    url = f"{REGISTRY_BASE_URL}/{path}"
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        console.print(f"  [{Colors.ERROR}]error:[/{Colors.ERROR}] Failed to fetch component: {e}")
        return None


def _get_emdash_dir() -> Path:
    """Get the .emdash directory."""
    return Path.cwd() / ".emdash"


def _install_skill(name: str, content: str) -> bool:
    """Install a skill to .emdash/skills/."""
    skill_dir = _get_emdash_dir() / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(content)
    return True


def _install_rule(name: str, content: str) -> bool:
    """Install a rule to .emdash/rules/."""
    rules_dir = _get_emdash_dir() / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    rule_file = rules_dir / f"{name}.md"
    rule_file.write_text(content)
    return True


def _install_agent(name: str, content: str) -> bool:
    """Install an agent to .emdash/agents/."""
    agents_dir = _get_emdash_dir() / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    agent_file = agents_dir / f"{name}.md"
    agent_file.write_text(content)
    return True


def _install_verifier(name: str, content: str) -> bool:
    """Install a verifier to .emdash/verifiers.json."""
    verifiers_file = _get_emdash_dir() / "verifiers.json"

    # Load or create verifiers config
    if verifiers_file.exists():
        existing = json.loads(verifiers_file.read_text())
    else:
        _get_emdash_dir().mkdir(parents=True, exist_ok=True)
        existing = {"verifiers": [], "max_attempts": 3}

    # Parse new verifier
    new_verifier = json.loads(content)

    # Check if already exists
    existing_names = [v.get("name") for v in existing.get("verifiers", [])]
    if name in existing_names:
        # Update existing
        existing["verifiers"] = [
            new_verifier if v.get("name") == name else v
            for v in existing["verifiers"]
        ]
    else:
        existing["verifiers"].append(new_verifier)

    verifiers_file.write_text(json.dumps(existing, indent=2))
    return True


@click.group(invoke_without_command=True)
@click.pass_context
def registry(ctx):
    """Browse and install community skills, rules, agents, and verifiers.

    Run without arguments to open the interactive wizard.
    """
    if ctx.invoked_subcommand is None:
        # Interactive wizard mode
        _show_registry_wizard()


@registry.command("list")
@click.argument("component_type", required=False,
                type=click.Choice(["skills", "rules", "agents", "verifiers"]))
def registry_list(component_type: str | None):
    """List available components from the registry."""
    reg = _fetch_registry()
    if not reg:
        return

    types_to_show = [component_type] if component_type else ["skills", "rules", "agents", "verifiers"]

    for ctype in types_to_show:
        components = reg.get(ctype, {})
        if not components:
            continue

        console.print()
        console.print(f"[{Colors.MUTED}]{header(ctype.title(), SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
        console.print()

        for name, info in components.items():
            tags = ", ".join(info.get("tags", []))
            desc = info.get("description", "")
            console.print(f"  [{Colors.PRIMARY}]{name}[/{Colors.PRIMARY}]")
            if desc:
                console.print(f"      [{Colors.MUTED}]{desc}[/{Colors.MUTED}]")
            if tags:
                console.print(f"      [{Colors.DIM}]{tags}[/{Colors.DIM}]")

        console.print()
        console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
        console.print()


@registry.command("show")
@click.argument("component_id")
def registry_show(component_id: str):
    """Show details of a component.

    COMPONENT_ID format: type:name (e.g., skill:frontend-design)
    """
    if ":" not in component_id:
        console.print(f"  [{Colors.ERROR}]error:[/{Colors.ERROR}] Invalid format. Use type:name (e.g., skill:frontend-design)")
        return

    ctype, name = component_id.split(":", 1)
    type_plural = ctype + "s" if not ctype.endswith("s") else ctype

    reg = _fetch_registry()
    if not reg:
        return

    components = reg.get(type_plural, {})
    if name not in components:
        console.print(f"  [{Colors.WARNING}]{ctype.title()} '{name}' not found in registry.[/{Colors.WARNING}]")
        return

    info = components[name]

    # Fetch the content
    content = _fetch_component(info["path"])
    if not content:
        return

    console.print()
    console.print(f"[{Colors.MUTED}]{header(f'{ctype}:{name}', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    if info.get('description'):
        console.print(f"  [{Colors.DIM}]desc[/{Colors.DIM}]    {info.get('description', '')}")
    if info.get('tags'):
        console.print(f"  [{Colors.DIM}]tags[/{Colors.DIM}]    {', '.join(info.get('tags', []))}")
    if info.get('path'):
        console.print(f"  [{Colors.DIM}]path[/{Colors.DIM}]    {info.get('path', '')}")

    console.print()
    console.print(f"  [{Colors.DIM}]content:[/{Colors.DIM}]")
    console.print()

    # Show content with indentation
    for line in content.split('\n')[:30]:  # Limit preview lines
        if line.startswith('#'):
            console.print(f"    [{Colors.PRIMARY}]{line}[/{Colors.PRIMARY}]")
        else:
            console.print(f"    [{Colors.MUTED}]{line}[/{Colors.MUTED}]")

    if len(content.split('\n')) > 30:
        console.print(f"    [{Colors.DIM}]... ({len(content.split(chr(10))) - 30} more lines)[/{Colors.DIM}]")

    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")


@registry.command("install")
@click.argument("component_ids", nargs=-1)
def registry_install(component_ids: tuple[str, ...]):
    """Install components from the registry.

    COMPONENT_IDS format: type:name (e.g., skill:frontend-design rule:typescript)
    """
    if not component_ids:
        console.print()
        console.print(f"  [{Colors.WARNING}]usage:[/{Colors.WARNING}] emdash registry install type:name")
        console.print(f"  [{Colors.DIM}]example: emdash registry install skill:frontend-design rule:typescript[/{Colors.DIM}]")
        console.print()
        return

    reg = _fetch_registry()
    if not reg:
        return

    console.print()
    for component_id in component_ids:
        if ":" not in component_id:
            console.print(f"  [{Colors.ERROR}]error:[/{Colors.ERROR}] Invalid format: {component_id}. Use type:name")
            continue

        ctype, name = component_id.split(":", 1)
        type_plural = ctype + "s" if not ctype.endswith("s") else ctype

        components = reg.get(type_plural, {})
        if name not in components:
            console.print(f"  [{Colors.WARNING}]not found:[/{Colors.WARNING}] {ctype}:{name}")
            continue

        info = components[name]
        content = _fetch_component(info["path"])
        if not content:
            continue

        # Install based on type
        installers = {
            "skill": _install_skill,
            "rule": _install_rule,
            "agent": _install_agent,
            "verifier": _install_verifier,
        }

        installer = installers.get(ctype)
        if not installer:
            console.print(f"  [{Colors.ERROR}]error:[/{Colors.ERROR}] Unknown component type: {ctype}")
            continue

        try:
            installer(name, content)
            console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] [{Colors.MUTED}]installed:[/{Colors.MUTED}] {ctype}:{name}")
        except Exception as e:
            console.print(f"  [{Colors.ERROR}]error:[/{Colors.ERROR}] {ctype}:{name} - {e}")
    console.print()


@registry.command("search")
@click.argument("query")
@click.option("--tag", "-t", multiple=True, help="Filter by tag")
def registry_search(query: str, tag: tuple[str, ...]):
    """Search the registry by name or description."""
    reg = _fetch_registry()
    if not reg:
        return

    query_lower = query.lower()
    tags_lower = [t.lower() for t in tag]

    results = []

    for ctype in ["skills", "rules", "agents", "verifiers"]:
        components = reg.get(ctype, {})
        for name, info in components.items():
            # Match query
            matches_query = (
                query_lower in name.lower() or
                query_lower in info.get("description", "").lower()
            )

            # Match tags
            component_tags = [t.lower() for t in info.get("tags", [])]
            matches_tags = not tags_lower or any(t in component_tags for t in tags_lower)

            if matches_query and matches_tags:
                results.append((ctype[:-1], name, info))  # Remove 's' from type

    console.print()
    if not results:
        console.print(f"  [{Colors.DIM}]no results for '{query}'[/{Colors.DIM}]")
        console.print()
        return

    console.print(f"[{Colors.MUTED}]{header(f'Search: {query}', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    for ctype, name, info in results:
        tags = ", ".join(info.get("tags", []))
        desc = info.get("description", "")
        console.print(f"  [{Colors.PRIMARY}]{ctype}:{name}[/{Colors.PRIMARY}]")
        if desc:
            console.print(f"      [{Colors.MUTED}]{desc}[/{Colors.MUTED}]")
        if tags:
            console.print(f"      [{Colors.DIM}]{tags}[/{Colors.DIM}]")

    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print(f"  [{Colors.DIM}]{len(results)} result{'s' if len(results) != 1 else ''}[/{Colors.DIM}]")
    console.print()


def _show_registry_wizard():
    """Show interactive registry wizard."""
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Registry', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.DIM}]browse and install community components[/{Colors.DIM}]")
    console.print()

    # Fetch registry
    console.print(f"  [{Colors.DIM}]fetching...[/{Colors.DIM}]", end="\r")
    reg = _fetch_registry()
    console.print("                    ", end="\r")  # Clear fetching message

    if not reg:
        return

    # Build menu items
    categories = [
        ("skills", "Skills", "specialized capabilities"),
        ("rules", "Rules", "coding standards"),
        ("agents", "Agents", "custom configurations"),
        ("verifiers", "Verifiers", "verification configs"),
    ]

    selected_category = [0]
    result = [None]

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_category[0] = (selected_category[0] - 1) % len(categories)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_category[0] = (selected_category[0] + 1) % len(categories)

    @kb.add("enter")
    def select(event):
        result[0] = categories[selected_category[0]][0]
        event.app.exit()

    @kb.add("1")
    def select_1(event):
        result[0] = "skills"
        event.app.exit()

    @kb.add("2")
    def select_2(event):
        result[0] = "rules"
        event.app.exit()

    @kb.add("3")
    def select_3(event):
        result[0] = "agents"
        event.app.exit()

    @kb.add("4")
    def select_4(event):
        result[0] = "verifiers"
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    @kb.add("q")
    def cancel(event):
        result[0] = None
        event.app.exit()

    def get_formatted_menu():
        lines = [("class:title", f"─── Categories {'─' * 30}\n\n")]

        for i, (key, name, desc) in enumerate(categories):
            count = len(reg.get(key, {}))
            is_selected = i == selected_category[0]
            prefix = "▸ " if is_selected else "  "

            if is_selected:
                lines.append(("class:selected", f"  {prefix}{name}"))
                lines.append(("class:count-selected", f"  {count}"))
                lines.append(("class:desc-selected", f"  {desc}\n"))
            else:
                lines.append(("class:option", f"  {prefix}{name}"))
                lines.append(("class:count", f"  {count}"))
                lines.append(("class:desc", f"  {desc}\n"))

        lines.append(("class:hint", f"\n{'─' * 45}\n  ↑↓ navigate  Enter select  1-4 quick  q quit"))
        return lines

    style = Style.from_dict({
        "title": f"{Colors.MUTED}",
        "selected": f"{Colors.SUCCESS} bold",
        "count-selected": f"{Colors.SUCCESS}",
        "desc-selected": f"{Colors.SUCCESS}",
        "option": f"{Colors.PRIMARY}",
        "count": f"{Colors.MUTED}",
        "desc": f"{Colors.DIM}",
        "hint": f"{Colors.DIM}",
    })

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_menu),
                height=len(categories) + 5,
            ),
        ])
    )

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        full_screen=False,
    )

    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        return

    console.print()

    if result[0] is None:
        return

    # Show components in selected category
    _show_component_picker(reg, result[0])


def _show_component_picker(reg: dict, category: str):
    """Show interactive component picker for a category."""
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    components = reg.get(category, {})
    if not components:
        console.print(f"  [{Colors.WARNING}]No {category} available.[/{Colors.WARNING}]")
        return

    # Build items list
    items = [(name, info) for name, info in components.items()]

    selected_index = [0]
    selected_items = set()  # For multi-select
    result = [None]  # "install", "back", or None

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_index[0] = (selected_index[0] - 1) % len(items)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_index[0] = (selected_index[0] + 1) % len(items)

    @kb.add("space")
    def toggle_select(event):
        name = items[selected_index[0]][0]
        if name in selected_items:
            selected_items.remove(name)
        else:
            selected_items.add(name)

    @kb.add("enter")
    def install_selected(event):
        if selected_items:
            result[0] = "install"
        else:
            # Install current item
            selected_items.add(items[selected_index[0]][0])
            result[0] = "install"
        event.app.exit()

    @kb.add("a")
    def select_all(event):
        for name, _ in items:
            selected_items.add(name)

    @kb.add("b")
    @kb.add("escape")
    def go_back(event):
        result[0] = "back"
        event.app.exit()

    @kb.add("c-c")
    @kb.add("q")
    def cancel(event):
        result[0] = None
        event.app.exit()

    def get_formatted_menu():
        lines = [("class:title", f"─── {category.title()} {'─' * (40 - len(category))}\n\n")]

        for i, (name, info) in enumerate(items):
            is_selected = i == selected_index[0]
            is_checked = name in selected_items
            prefix = "▸ " if is_selected else "  "
            checkbox = "●" if is_checked else "○"

            desc = info.get("description", "")
            if len(desc) > 45:
                desc = desc[:42] + "..."

            if is_selected:
                lines.append(("class:selected", f"  {prefix}{checkbox} {name}"))
                lines.append(("class:desc-selected", f"  {desc}\n"))
            else:
                style_class = "class:checked" if is_checked else "class:option"
                lines.append((style_class, f"  {prefix}{checkbox} {name}"))
                lines.append(("class:desc", f"  {desc}\n"))

        selected_count = len(selected_items)
        if selected_count > 0:
            lines.append(("class:status", f"\n  {selected_count} selected"))

        lines.append(("class:hint", f"\n{'─' * 45}\n  ↑↓ navigate  Space toggle  Enter install  a all  b back"))
        return lines

    style = Style.from_dict({
        "title": f"{Colors.MUTED}",
        "selected": f"{Colors.SUCCESS} bold",
        "checked": f"{Colors.WARNING}",
        "desc-selected": f"{Colors.SUCCESS}",
        "option": f"{Colors.PRIMARY}",
        "desc": f"{Colors.DIM}",
        "status": f"{Colors.WARNING} bold",
        "hint": f"{Colors.DIM}",
    })

    height = len(items) + 6

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

    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        return

    console.print()

    if result[0] == "back":
        _show_registry_wizard()
        return

    if result[0] == "install" and selected_items:
        singular = category[:-1]
        component_ids = [f"{singular}:{name}" for name in selected_items]

        console.print()
        for cid in component_ids:
            ctype, name = cid.split(":", 1)
            info = components[name]

            console.print(f"  [{Colors.DIM}]installing {cid}...[/{Colors.DIM}]", end="\r")
            content = _fetch_component(info["path"])
            console.print("                                        ", end="\r")  # Clear

            if not content:
                continue

            installers = {
                "skill": _install_skill,
                "rule": _install_rule,
                "agent": _install_agent,
                "verifier": _install_verifier,
            }

            installer = installers.get(ctype)
            if installer:
                try:
                    installer(name, content)
                    console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] [{Colors.MUTED}]installed:[/{Colors.MUTED}] {cid}")
                except Exception as e:
                    console.print(f"  [{Colors.ERROR}]error:[/{Colors.ERROR}] {cid} - {e}")

        console.print()

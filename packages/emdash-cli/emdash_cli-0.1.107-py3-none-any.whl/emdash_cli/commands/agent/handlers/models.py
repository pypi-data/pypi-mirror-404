"""Handler for /model slash command - switch models interactively."""

import json
import os
from pathlib import Path

from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style

from rich.console import Console

from emdash_cli.design import Colors

console = Console()


def _update_env_file(key: str, value: str) -> bool:
    """Update or add a key=value in the .env file.

    Args:
        key: Environment variable name
        value: Value to set

    Returns:
        True if successful, False otherwise
    """
    env_path = Path.cwd() / ".env"

    lines = []
    key_found = False

    # Read existing .env if it exists
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                # Check if this line sets our key
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    lines.append(line)

    # If key wasn't found, add it
    if not key_found:
        # Add newline if file doesn't end with one
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.append(f"{key}={value}\n")

    # Write back
    try:
        with open(env_path, "w") as f:
            f.writelines(lines)
        return True
    except Exception:
        return False


def _load_models_config() -> dict:
    """Load models configuration from JSON file."""
    config_path = Path(__file__).parent.parent / "models.json"
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return json.load(f)


def _get_short_name(model: str) -> str:
    """Get short display name from full model path."""
    if "/" in model:
        return model.split("/")[-1]
    return model


def _interactive_select(items: list[tuple[str, str]], title: str, hint: str = "") -> str | None:
    """Show interactive selection menu.

    Args:
        items: List of (value, display_name) tuples
        title: Title to show above the menu
        hint: Hint text to show below

    Returns:
        Selected value or None if cancelled
    """
    if not items:
        return None

    selected_index = [0]
    result = [None]

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(_event):
        selected_index[0] = (selected_index[0] - 1) % len(items)

    @kb.add("down")
    @kb.add("j")
    def move_down(_event):
        selected_index[0] = (selected_index[0] + 1) % len(items)

    @kb.add("enter")
    def select(event):
        result[0] = items[selected_index[0]][0]
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    @kb.add("q")
    def cancel(event):
        result[0] = None
        event.app.exit()

    def get_formatted_menu():
        lines = [("class:title", f"{title}\n\n")]

        for i, (value, display) in enumerate(items):
            is_selected = i == selected_index[0]
            prefix = "▸ " if is_selected else "  "

            if is_selected:
                lines.append(("class:selected", f"{prefix}{display}\n"))
            else:
                lines.append(("class:item", f"{prefix}{display}\n"))

        hint_text = hint or "[↑/↓] navigate | Enter select | q cancel"
        lines.append(("class:hint", f"\n{hint_text}"))
        return lines

    style = Style.from_dict({
        "title": "#00ccff bold",
        "item": "#aaaaaa",
        "selected": "#00cc66 bold",
        "hint": "#666666 italic",
    })

    height = len(items) + 5

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_menu),
                height=height,
            )
        ])
    )

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        full_screen=False,
        mouse_support=True,
    )

    app.run()
    return result[0]


def handle_model(args: str, current_model: str) -> str | None:
    """Handle /model command - select provider and model.

    Args:
        args: Optional provider name (fireworks, openai, anthropic)
        current_model: Current model string

    Returns:
        New model string if changed, None otherwise
    """
    config = _load_models_config()

    if not config:
        console.print(f"[{Colors.ERROR}]Models config not found[/{Colors.ERROR}]")
        return None

    # If args provided, go directly to that provider
    provider = args.lower() if args else None

    # If no provider specified, show provider selection
    if not provider:
        provider_items = [
            (key, f"{info['name']} ({key})")
            for key, info in config.items()
        ]

        console.print()
        if current_model:
            console.print(f"[dim]Current: {current_model}[/dim]")
            console.print()

        provider = _interactive_select(
            provider_items,
            "Select Provider",
        )

        if not provider:
            return None

    # Validate provider
    if provider not in config:
        console.print(f"[{Colors.ERROR}]Unknown provider: {provider}[/{Colors.ERROR}]")
        console.print(f"[dim]Available: {', '.join(config.keys())}[/dim]")
        return None

    # Show models for selected provider
    provider_info = config[provider]
    models = provider_info["models"]

    model_items = [
        (model, _get_short_name(model))
        for model in models
    ]

    selected_model = _interactive_select(
        model_items,
        f"{provider_info['name']} Models",
    )

    if not selected_model:
        return None

    # Use model path directly (no prefix needed)
    full_model = selected_model

    # Set environment variable for this session
    os.environ["EMDASH_MODEL"] = full_model

    # Persist to .env file
    if _update_env_file("EMDASH_MODEL", full_model):
        console.print()
        console.print(f"[{Colors.SUCCESS}]Model: {full_model}[/{Colors.SUCCESS}]")
        console.print(f"[dim]Saved to .env[/dim]")
    else:
        console.print()
        console.print(f"[{Colors.SUCCESS}]Model: {full_model}[/{Colors.SUCCESS}]")
        console.print(f"[{Colors.WARNING}]Could not save to .env[/{Colors.WARNING}]")
    console.print()

    return full_model

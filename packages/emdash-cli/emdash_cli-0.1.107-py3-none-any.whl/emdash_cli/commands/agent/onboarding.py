"""First-run onboarding wizard for emdash CLI.

Provides an animated, guided setup experience for new users with zen styling.
"""

import sys
import time
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit import Application

from ...design import (
    Colors,
    ANSI,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    STATUS_ERROR,
    DOT_BULLET,
    DOT_WAITING,
    DOT_ACTIVE,
    ARROW_PROMPT,
    ARROW_RIGHT,
    EM_DASH,
    header,
    footer,
    step_progress,
    SEPARATOR_WIDTH,
    SPINNER_FRAMES,
    LOGO,
)

console = Console()


# ─────────────────────────────────────────────────────────────────────────────
# Animation Utilities
# ─────────────────────────────────────────────────────────────────────────────

def typewriter(text: str, delay: float = 0.02, style: str = "") -> None:
    """Print text with typewriter animation."""
    for char in text:
        if style:
            console.print(char, end="", style=style)
        else:
            console.print(char, end="")
        sys.stdout.flush()
        time.sleep(delay)
    console.print()  # newline


def animate_line(text: str, style: str = "", delay: float = 0.03) -> None:
    """Animate a single line appearing character by character."""
    for i in range(len(text) + 1):
        sys.stdout.write(f"\r{text[:i]}")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def animate_dots(message: str, duration: float = 1.0, style: str = "") -> None:
    """Show animated dots for a duration."""
    frames = len(SPINNER_FRAMES)
    start = time.time()
    i = 0
    while time.time() - start < duration:
        spinner = SPINNER_FRAMES[i % frames]
        sys.stdout.write(f"\r  {spinner} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
    sys.stdout.flush()


def reveal_lines(lines: list[tuple[str, str]], delay: float = 0.15) -> None:
    """Reveal lines one by one with a fade-in effect."""
    for text, style in lines:
        if style:
            console.print(text, style=style)
        else:
            console.print(text)
        time.sleep(delay)


def animated_progress_bar(steps: int, current: int, width: int = 30) -> str:
    """Create an animated-style progress bar."""
    filled = int(width * current / steps)
    empty = width - filled
    bar = f"{'█' * filled}{'░' * empty}"
    return bar


def pulse_text(text: str, cycles: int = 3) -> None:
    """Pulse text brightness."""
    styles = [Colors.DIM, Colors.MUTED, Colors.PRIMARY, Colors.MUTED, Colors.DIM]
    for _ in range(cycles):
        for style in styles:
            sys.stdout.write(f"\r  [{style}]{text}[/{style}]")
            sys.stdout.flush()
            time.sleep(0.08)


# ─────────────────────────────────────────────────────────────────────────────
# First Run Detection
# ─────────────────────────────────────────────────────────────────────────────

def is_first_run() -> bool:
    """Check if this is the first time running emdash."""
    emdash_dir = Path.home() / ".emdash"
    markers = [
        emdash_dir / "cli_history",
        emdash_dir / "config.json",
        emdash_dir / "sessions",
    ]
    return not any(m.exists() for m in markers)


# ─────────────────────────────────────────────────────────────────────────────
# Animated Welcome Screen
# ─────────────────────────────────────────────────────────────────────────────

def show_welcome_screen() -> bool:
    """Show clean welcome screen.

    Returns:
        True if user wants to proceed with onboarding, False to skip.
    """
    console.print()

    # Simple, clean header
    console.print(f"[{Colors.MUTED}]{header('emdash', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.PRIMARY} bold]Welcome[/{Colors.PRIMARY} bold]")
    console.print()
    console.print(f"  [{Colors.DIM}]Let's get you set up.[/{Colors.DIM}]")
    console.print()

    # Clean step list
    console.print(f"  [{Colors.MUTED}]{DOT_WAITING}[/{Colors.MUTED}] Connect to GitHub [{Colors.DIM}](optional)[/{Colors.DIM}]")
    console.print(f"  [{Colors.MUTED}]{DOT_WAITING}[/{Colors.MUTED}] Create your first rule")
    console.print(f"  [{Colors.MUTED}]{DOT_WAITING}[/{Colors.MUTED}] Start building")
    console.print()

    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    # Prompt
    console.print(f"  [{Colors.DIM}]Enter to begin · s to skip[/{Colors.DIM}]")
    console.print()

    try:
        session = PromptSession()
        response = session.prompt(f"  {ARROW_PROMPT} ").strip().lower()
        return response != 's'
    except (KeyboardInterrupt, EOFError):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Step Headers
# ─────────────────────────────────────────────────────────────────────────────

def show_step_header(step: int, total: int, title: str) -> None:
    """Show step header with progress indicator."""
    console.print()
    console.print(f"[{Colors.MUTED}]{header(title, SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print(f"  [{Colors.DIM}]step {step} of {total}[/{Colors.DIM}]")
    console.print()


def show_step_complete(message: str) -> None:
    """Show step completion."""
    console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] {message}")


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: GitHub Authentication
# ─────────────────────────────────────────────────────────────────────────────

def step_github_auth() -> bool:
    """Step 1: GitHub authentication (optional).

    Returns:
        True if completed or skipped, False if cancelled.
    """
    show_step_header(1, 3, "Connect GitHub")

    console.print(f"  [{Colors.PRIMARY}]GitHub connection enables:[/{Colors.PRIMARY}]")
    console.print()
    console.print(f"    [{Colors.MUTED}]{DOT_BULLET} PR reviews and creation[/{Colors.MUTED}]")
    console.print(f"    [{Colors.MUTED}]{DOT_BULLET} Issue management[/{Colors.MUTED}]")
    console.print(f"    [{Colors.MUTED}]{DOT_BULLET} Repository insights[/{Colors.MUTED}]")
    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    # Interactive menu
    selected_index = [0]
    result = [None]

    options = [
        ("connect", "Connect GitHub account", "Opens browser for OAuth"),
        ("skip", "Skip for now", "Can connect later with /auth"),
    ]

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

    @kb.add("c")
    def connect(event):
        result[0] = "connect"
        event.app.exit()

    @kb.add("s")
    def skip(event):
        result[0] = "skip"
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    def cancel(event):
        result[0] = "cancel"
        event.app.exit()

    def get_formatted_options():
        lines = []
        for i, (key, desc, hint) in enumerate(options):
            indicator = STATUS_ACTIVE if i == selected_index[0] else STATUS_INACTIVE
            if i == selected_index[0]:
                lines.append(("class:selected", f"  {indicator} {desc}\n"))
                lines.append(("class:hint-selected", f"      {hint}\n"))
            else:
                lines.append(("class:option", f"  {indicator} {desc}\n"))
                lines.append(("class:hint-dim", f"      {hint}\n"))
        lines.append(("class:hint", f"\n{ARROW_PROMPT} c connect  s skip  Esc cancel"))
        return lines

    style = Style.from_dict({
        "selected": f"{Colors.SUCCESS} bold",
        "hint-selected": Colors.SUCCESS,
        "option": Colors.MUTED,
        "hint-dim": Colors.DIM,
        "hint": f"{Colors.DIM} italic",
    })

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_options),
                height=7,
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
        return False

    if result[0] == "cancel":
        return False

    if result[0] == "connect":
        from ..auth import auth_login
        console.print()
        try:
            auth_login(no_browser=False)
            console.print()
            show_step_complete("GitHub connected successfully")
        except Exception as e:
            console.print(f"  [{Colors.ERROR}]{STATUS_ERROR}[/{Colors.ERROR}] Connection failed: {e}")
            console.print(f"  [{Colors.DIM}]You can try again later with /auth login[/{Colors.DIM}]")
    else:
        console.print(f"  [{Colors.MUTED}]{DOT_BULLET} Skipped {ARROW_RIGHT} run /auth login anytime[/{Colors.MUTED}]")

    return True


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Create Rule
# ─────────────────────────────────────────────────────────────────────────────

def step_create_rule() -> bool:
    """Step 2: Create first rule (optional).

    Returns:
        True if completed or skipped, False if cancelled.
    """
    show_step_header(2, 3, "Create a Rule")

    console.print(f"  [{Colors.PRIMARY}]Rules guide the agent's behavior:[/{Colors.PRIMARY}]")
    console.print()
    console.print(f"    [{Colors.MUTED}]{DOT_BULLET} Coding style preferences[/{Colors.MUTED}]")
    console.print(f"    [{Colors.MUTED}]{DOT_BULLET} Project conventions[/{Colors.MUTED}]")
    console.print(f"    [{Colors.MUTED}]{DOT_BULLET} Testing requirements[/{Colors.MUTED}]")
    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    selected_index = [0]
    result = [None]

    options = [
        ("template", "Create from template", "Quick start with best practices"),
        ("custom", "Write custom rule", "Define your own guidelines"),
        ("skip", "Skip for now", "Can create later with /rules"),
    ]

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

    @kb.add("s")
    def skip(event):
        result[0] = "skip"
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    def cancel(event):
        result[0] = "cancel"
        event.app.exit()

    def get_formatted_options():
        lines = []
        for i, (key, desc, hint) in enumerate(options):
            indicator = STATUS_ACTIVE if i == selected_index[0] else STATUS_INACTIVE
            if i == selected_index[0]:
                lines.append(("class:selected", f"  {indicator} {desc}\n"))
                lines.append(("class:hint-selected", f"      {hint}\n"))
            else:
                lines.append(("class:option", f"  {indicator} {desc}\n"))
                lines.append(("class:hint-dim", f"      {hint}\n"))
        lines.append(("class:hint", f"\n{ARROW_PROMPT} Enter select  s skip  Esc cancel"))
        return lines

    style = Style.from_dict({
        "selected": f"{Colors.SUCCESS} bold",
        "hint-selected": Colors.SUCCESS,
        "option": Colors.MUTED,
        "hint-dim": Colors.DIM,
        "hint": f"{Colors.DIM} italic",
    })

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_options),
                height=9,
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
        return False

    if result[0] == "cancel":
        return False

    if result[0] == "template":
        console.print()
        create_rule_from_template()
    elif result[0] == "custom":
        console.print()
        create_custom_rule()
    else:
        console.print(f"  [{Colors.MUTED}]{DOT_BULLET} Skipped {ARROW_RIGHT} run /rules anytime[/{Colors.MUTED}]")

    return True


def create_rule_from_template() -> None:
    """Create a rule from a template."""
    templates = [
        ("python", "Python best practices", "Type hints, docstrings, PEP 8"),
        ("typescript", "TypeScript standards", "Strict types, ESLint, modern syntax"),
        ("testing", "Testing requirements", "Tests for features, 80% coverage"),
        ("minimal", "Minimal rule", "Concise, focused responses"),
    ]

    selected_index = [0]
    result = [None]

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_index[0] = (selected_index[0] - 1) % len(templates)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_index[0] = (selected_index[0] + 1) % len(templates)

    @kb.add("enter")
    def select(event):
        result[0] = templates[selected_index[0]]
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    def cancel(event):
        result[0] = None
        event.app.exit()

    def get_formatted_templates():
        lines = [("class:title", "  Select a template:\n\n")]
        for i, (key, title, desc) in enumerate(templates):
            indicator = STATUS_ACTIVE if i == selected_index[0] else STATUS_INACTIVE
            if i == selected_index[0]:
                lines.append(("class:selected", f"  {indicator} {title}\n"))
                lines.append(("class:selected-desc", f"      {desc}\n"))
            else:
                lines.append(("class:option", f"  {indicator} {title}\n"))
                lines.append(("class:desc", f"      {desc}\n"))
        lines.append(("class:hint", f"\n{ARROW_PROMPT} ↑↓ select  Enter confirm  Esc cancel"))
        return lines

    style = Style.from_dict({
        "title": f"{Colors.PRIMARY} bold",
        "selected": f"{Colors.SUCCESS} bold",
        "selected-desc": Colors.SUCCESS,
        "option": Colors.MUTED,
        "desc": Colors.DIM,
        "hint": f"{Colors.DIM} italic",
    })

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_templates),
                height=len(templates) * 2 + 4,
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

    if result[0]:
        key, title, desc = result[0]

        rules_dir = Path.cwd() / ".emdash" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        rule_file = rules_dir / f"{key}.md"

        rule_content = f"""# {title}

{desc}

## Guidelines

- Follow project conventions
- Write clean, maintainable code
- Add appropriate documentation
"""
        rule_file.write_text(rule_content)
        show_step_complete(f"Created rule: {rule_file.relative_to(Path.cwd())}")


def create_custom_rule() -> None:
    """Create a custom rule with user input."""
    console.print(f"  [{Colors.DIM}]Enter a name for your rule:[/{Colors.DIM}]")

    try:
        session = PromptSession()
        name = session.prompt(f"  {ARROW_PROMPT} ").strip()
        if not name:
            return

        name = name.lower().replace(" ", "-")

        console.print()
        console.print(f"  [{Colors.DIM}]Describe the rule (one line):[/{Colors.DIM}]")
        desc = session.prompt(f"  {ARROW_PROMPT} ").strip()

        rules_dir = Path.cwd() / ".emdash" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        rule_file = rules_dir / f"{name}.md"

        rule_content = f"""# {name.replace("-", " ").title()}

{desc or "Custom rule"}

## Guidelines

- Add your specific guidelines here
"""
        rule_file.write_text(rule_content)
        show_step_complete(f"Created rule: {rule_file.relative_to(Path.cwd())}")
        console.print(f"  [{Colors.DIM}]Edit the file to add more details[/{Colors.DIM}]")
    except (KeyboardInterrupt, EOFError):
        return


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Completion
# ─────────────────────────────────────────────────────────────────────────────

def step_quick_command() -> bool:
    """Step 3: Show quick commands.

    Returns:
        True to complete onboarding.
    """
    show_step_header(3, 3, "You're Ready")

    console.print(f"  [{Colors.SUCCESS}]Setup complete![/{Colors.SUCCESS}]")
    console.print()

    console.print(f"  [{Colors.DIM}]Quick commands:[/{Colors.DIM}]")
    console.print()
    console.print(f"    [{Colors.PRIMARY}]/help     [/{Colors.PRIMARY}] [{Colors.DIM}]Show all commands[/{Colors.DIM}]")
    console.print(f"    [{Colors.PRIMARY}]/plan     [/{Colors.PRIMARY}] [{Colors.DIM}]Switch to plan mode[/{Colors.DIM}]")
    console.print(f"    [{Colors.PRIMARY}]/agents   [/{Colors.PRIMARY}] [{Colors.DIM}]Manage custom agents[/{Colors.DIM}]")
    console.print(f"    [{Colors.PRIMARY}]/rules    [/{Colors.PRIMARY}] [{Colors.DIM}]Configure rules[/{Colors.DIM}]")
    console.print()

    console.print(f"  [{Colors.MUTED}]Or just type your question to get started.[/{Colors.MUTED}]")
    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    return True


# ─────────────────────────────────────────────────────────────────────────────
# Main Onboarding Flow
# ─────────────────────────────────────────────────────────────────────────────

def run_onboarding() -> bool:
    """Run the complete animated onboarding flow.

    Returns:
        True if onboarding completed, False if cancelled.
    """
    if not show_welcome_screen():
        console.print(f"  [{Colors.DIM}]Skipped onboarding. Run /setup anytime.[/{Colors.DIM}]")
        console.print()
        return False

    # Step 1: GitHub auth
    if not step_github_auth():
        return False

    # Step 2: Create rule
    if not step_create_rule():
        return False

    # Step 3: Quick commands
    step_quick_command()

    # Mark onboarding complete
    emdash_dir = Path.home() / ".emdash"
    emdash_dir.mkdir(parents=True, exist_ok=True)
    (emdash_dir / ".onboarding_complete").touch()

    return True

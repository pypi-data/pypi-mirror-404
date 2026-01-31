"""Emdash CLI Design System.

A zen, geometric design language combining clean lines with dot-matrix textures.
The em dash (─) is the signature element, appearing in all separators and frames.
"""

from rich.console import Console
from rich.markup import escape as _rich_escape

_console = Console()

# ─────────────────────────────────────────────────────────────────────────────
# Logo & Branding
# ─────────────────────────────────────────────────────────────────────────────

# Large stylized logo using block characters - minimal, geometric, impactful
LOGO_LARGE = r"""
  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
  █                                               █
  █   ▓█▀▀▀ █▀▄▀█ █▀▀▄ ▄▀▀▄ ▓█▀▀▀█ █  █          █
  █   ▓█▀▀  █ ▀ █ █  █ █▀▀█ ▓▀▀▀▀█ █▀▀█ ─────    █
  █   ▓█▄▄▄ █   █ █▄▄▀ █  █ ▓█▄▄▄█ █  █          █
  █                                               █
  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
"""

# Medium logo - cleaner, more readable
LOGO_MEDIUM = r"""
   ╭─────────────────────────────────────────╮
   │                                         │
   │   ███ █▄ ▄█ █▀▄ ▄▀▄ ▄▀▀ █ █ ───         │
   │   █▄▄ █ ▀ █ █ █ █▀█ ▀▀█ █▀█             │
   │   ███ █   █ █▄▀ █ █ ▄▄▀ █ █             │
   │                                         │
   ╰─────────────────────────────────────────╯
"""

# Compact logo - single line, stylized
LOGO_COMPACT = "─── ◈ emdash ◈ ───"

# Ultra-minimal logo with em dash signature
LOGO_MINIMAL = "── emdash ──"

# Braille-style logo - dot matrix aesthetic
LOGO_DOTS = r"""
   ⠀⣠⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣄⠀
   ⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇
   ⢸⣿⠀⠀⣴⣦⠀⣾⡄⣴⣦⠀⣶⣤⡀⠀⣴⣦⠀⣶⣶⣶⠀⣾⠀⣾⠀⠀⠀⠀⠀⠀⠀⣿⡇
   ⢸⣿⠀⠀⣿⣿⠀⣿⣿⣿⣿⠀⣿⠙⣿⠀⣿⣿⠀⠀⣿⠀⠀⣿⣀⣿⠀⠤⠤⠤⠀⠀⠀⣿⡇
   ⢸⣿⠀⠀⠛⠛⠀⠛⠀⠀⠛⠀⠛⠛⠃⠀⠛⠙⠛⠀⠛⠛⠀⠛⠀⠛⠀⠀⠀⠀⠀⠀⠀⣿⡇
   ⠀⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠀
"""

# Block-style large text - bold and impactful
LOGO_BLOCK = r"""
    ╔═══════════════════════════════════════════════╗
    ║                                               ║
    ║   ▓▓▓▓  ▓   ▓  ▓▓▓   ▓▓▓  ▓▓▓▓  ▓  ▓         ║
    ║   ▓     ▓▓ ▓▓  ▓  ▓ ▓   ▓ ▓     ▓▓▓▓  ────   ║
    ║   ▓▓▓   ▓ ▓ ▓  ▓  ▓ ▓▓▓▓▓ ▓▓▓▓  ▓  ▓         ║
    ║   ▓     ▓   ▓  ▓  ▓ ▓   ▓    ▓  ▓  ▓         ║
    ║   ▓▓▓▓  ▓   ▓  ▓▓▓  ▓   ▓ ▓▓▓▓  ▓  ▓         ║
    ║                                               ║
    ╚═══════════════════════════════════════════════╝
"""

# Clean geometric logo - the recommended default
LOGO = r"""
    ┌─────────────────────────────────────────────┐
    │                                             │
    │   ╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸   │
    │                                             │
    │            ◈  e m d a s h  ◈               │
    │                                             │
    │   ╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸   │
    │                                             │
    └─────────────────────────────────────────────┘
"""


# ─────────────────────────────────────────────────────────────────────────────
# Typography & Signature Elements
# ─────────────────────────────────────────────────────────────────────────────

EM_DASH = "─"
SEPARATOR_WIDTH = 45
SEPARATOR = EM_DASH * SEPARATOR_WIDTH
SEPARATOR_SHORT = EM_DASH * 20


def header(title: str, width: int = SEPARATOR_WIDTH) -> str:
    """Create a header with em dash separators.

    Example: ─── Title ─────────────────────────────
    """
    prefix = f"{EM_DASH * 3} {title} "
    remaining = width - len(prefix)
    return f"{prefix}{EM_DASH * max(0, remaining)}"


def footer(width: int = SEPARATOR_WIDTH) -> str:
    """Create a footer separator."""
    return EM_DASH * width


# ─────────────────────────────────────────────────────────────────────────────
# Dot Matrix / Stippled Elements
# ─────────────────────────────────────────────────────────────────────────────

# Spinner frames - dot matrix style, feels computational
SPINNER_FRAMES = ["⠿", "⠷", "⠯", "⠟", "⠻", "⠽", "⠾", "⠿"]

# Stippled elements
DOT_ACTIVE = "⠿"      # Dense braille - active/processing
DOT_WAITING = "∷"     # Stippled - waiting/idle
DOT_BULLET = "∷"      # List bullets


# ─────────────────────────────────────────────────────────────────────────────
# Status Indicators
# ─────────────────────────────────────────────────────────────────────────────

STATUS_ACTIVE = "▸"    # Active/selected/success
STATUS_INACTIVE = "▹"  # Inactive/pending
STATUS_ERROR = "■"     # Solid - errors
STATUS_INFO = "□"      # Outline - info


# ─────────────────────────────────────────────────────────────────────────────
# Flow & Navigation
# ─────────────────────────────────────────────────────────────────────────────

ARROW_PROMPT = "›"     # Prompt/hint indicator
ARROW_RIGHT = "»"      # Direction/flow
NEST_LINE = "│"        # Vertical nesting


# ─────────────────────────────────────────────────────────────────────────────
# Progress Elements
# ─────────────────────────────────────────────────────────────────────────────

PROGRESS_FULL = "█"
PROGRESS_PARTIAL = "▓"
PROGRESS_EMPTY = "░"


def progress_bar(percent: float, width: int = 20) -> str:
    """Create a progress bar.

    Example: ████████▓░░░░░░░░░░░  42%
    """
    filled = int(width * percent / 100)
    partial = 1 if (percent % (100 / width)) > (50 / width) and filled < width else 0
    empty = width - filled - partial

    bar = PROGRESS_FULL * filled + PROGRESS_PARTIAL * partial + PROGRESS_EMPTY * empty
    return f"{bar}  {percent:.0f}%"


def step_progress(current: int, total: int, width: int = 20) -> str:
    """Create a step progress indicator.

    Example: ∷∷∷∷∷∷∷∷∷∷∷∷∷∷∷∷∷∷∷  step 2 of 4
    """
    dots = DOT_WAITING * width
    return f"{dots}  step {current} of {total}"


# ─────────────────────────────────────────────────────────────────────────────
# Zen Color Palette - Red/Warm Tones
# ─────────────────────────────────────────────────────────────────────────────

class Colors:
    """Zen color palette - warm, vibrant, red-accented."""

    # Core semantic colors - warmer, more vibrant
    PRIMARY = "#f0a0a0"      # warm rose - main accent
    SECONDARY = "#e8d0a0"    # warm sand - secondary
    SUCCESS = "#b8d8a8"      # fresh sage - success
    WARNING = "#f0c878"      # warm amber - warnings
    ERROR = "#e87878"        # vibrant coral - errors

    # Text hierarchy
    TEXT = "#f0f0f0"         # bright white
    MUTED = "#c0a8a8"        # dusty rose - secondary text
    DIM = "#a09090"          # warm gray - hints

    # Accents
    ACCENT = "#d0b0c0"       # mauve - highlights
    SUBTLE = "#b8a8a8"       # warm fog - disabled


# Rich markup shortcuts
class Markup:
    """Rich markup helpers for consistent styling."""

    @staticmethod
    def primary(text: str) -> str:
        return f"[{Colors.PRIMARY}]{text}[/{Colors.PRIMARY}]"

    @staticmethod
    def success(text: str) -> str:
        return f"[{Colors.SUCCESS}]{text}[/{Colors.SUCCESS}]"

    @staticmethod
    def warning(text: str) -> str:
        return f"[{Colors.WARNING}]{text}[/{Colors.WARNING}]"

    @staticmethod
    def error(text: str) -> str:
        return f"[{Colors.ERROR}]{text}[/{Colors.ERROR}]"

    @staticmethod
    def muted(text: str) -> str:
        return f"[{Colors.MUTED}]{text}[/{Colors.MUTED}]"

    @staticmethod
    def dim(text: str) -> str:
        return f"[{Colors.DIM}]{text}[/{Colors.DIM}]"

    @staticmethod
    def accent(text: str) -> str:
        return f"[{Colors.ACCENT}]{text}[/{Colors.ACCENT}]"

    @staticmethod
    def bold(text: str) -> str:
        return f"[bold]{text}[/bold]"

    @staticmethod
    def italic(text: str) -> str:
        return f"[italic]{text}[/italic]"


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Toolkit Styles
# ─────────────────────────────────────────────────────────────────────────────

# Style dict for prompt_toolkit
PROMPT_TOOLKIT_STYLE = {
    # Menu items
    "selected": f"{Colors.SUCCESS} bold",
    "option": Colors.MUTED,
    "option-desc": Colors.DIM,
    "hint": f"{Colors.DIM} italic",

    # Headers and frames
    "header": f"{Colors.PRIMARY} bold",
    "separator": Colors.DIM,

    # Status
    "success": Colors.SUCCESS,
    "warning": Colors.WARNING,
    "error": Colors.ERROR,

    # Input
    "prompt": f"{Colors.SUCCESS} bold",
    "prompt-plan": f"{Colors.WARNING} bold",
}


# ─────────────────────────────────────────────────────────────────────────────
# ANSI Escape Codes (for raw terminal output)
# ─────────────────────────────────────────────────────────────────────────────

class ANSI:
    """ANSI escape codes for direct terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"

    # Warm zen palette as ANSI (256-color approximations)
    PRIMARY = "\033[38;5;217m"    # warm rose
    SECONDARY = "\033[38;5;223m"  # warm sand
    SUCCESS = "\033[38;5;150m"    # fresh sage
    WARNING = "\033[38;5;221m"    # warm amber
    ERROR = "\033[38;5;203m"      # vibrant coral
    MUTED = "\033[38;5;181m"      # dusty rose
    SHADOW = "\033[38;5;138m"     # warm gray


# ─────────────────────────────────────────────────────────────────────────────
# Component Templates
# ─────────────────────────────────────────────────────────────────────────────

def frame(title: str, content: str, width: int = SEPARATOR_WIDTH) -> str:
    """Create a framed content block.

    Example:
    ─── Title ─────────────────────────────

      Content goes here

    ─────────────────────────────────────────
    """
    lines = [
        header(title, width),
        "",
        content,
        "",
        footer(width),
    ]
    return "\n".join(lines)


def menu_hint(*hints: tuple[str, str]) -> str:
    """Create a hint bar for menus.

    Example: › y approve  n feedback  Esc cancel
    """
    parts = [f"{key} {action}" for key, action in hints]
    return f"{ARROW_PROMPT} {'  '.join(parts)}"


def bullet_list(items: list[str], indent: int = 2) -> str:
    """Create a bulleted list with stippled bullets.

    Example:
      ∷ First item
      ∷ Second item
    """
    prefix = " " * indent + DOT_BULLET + " "
    return "\n".join(f"{prefix}{item}" for item in items)


def nested_line(text: str, indent: int = 2) -> str:
    """Create a nested/indented line with vertical bar.

    Example:
      │ Nested content
    """
    return f"{' ' * indent}{NEST_LINE} {text}"


# ─────────────────────────────────────────────────────────────────────────────
# Safe Printing Utilities
# ─────────────────────────────────────────────────────────────────────────────


def print_error(message: str | Exception, prefix: str = "Error") -> None:
    """Print an error message safely, escaping any Rich markup in the message.

    Args:
        message: The error message or exception to print
        prefix: The prefix before the message (default: "Error")
    """
    safe_msg = _rich_escape(str(message))
    _console.print(f"[red]{prefix}: {safe_msg}[/red]")


def print_warning(message: str | Exception) -> None:
    """Print a warning message safely, escaping any Rich markup in the message."""
    safe_msg = _rich_escape(str(message))
    _console.print(f"[yellow]{safe_msg}[/yellow]")


def print_success(message: str) -> None:
    """Print a success message safely, escaping any Rich markup in the message."""
    safe_msg = _rich_escape(str(message))
    _console.print(f"[green]{safe_msg}[/green]")

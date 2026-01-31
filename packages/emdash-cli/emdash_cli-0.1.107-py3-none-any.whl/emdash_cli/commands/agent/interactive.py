"""Interactive REPL mode for the agent CLI."""

import queue
import subprocess
import sys
import time
import threading
from pathlib import Path

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .constants import AgentMode
from .profiles import get_agent_profile, AgentProfile
from .onboarding import is_first_run, run_onboarding
from .help import show_command_help
from .session_restore import get_recent_session, show_session_restore_prompt
from ...design import (
    header, footer, Colors, STATUS_ACTIVE, DOT_BULLET,
    ARROW_PROMPT, SEPARATOR_WIDTH, print_error,
)


def _get_machine_user_id() -> str:
    """Generate a unique user ID for this CLI instance.

    Used for multiuser sessions to identify participants.
    Includes process ID to ensure uniqueness when testing with multiple
    terminals on the same machine.
    """
    import hashlib
    import socket
    import os
    hostname = socket.gethostname()
    username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    pid = os.getpid()
    # Include PID to make unique per process - allows multiple terminals on same machine
    return hashlib.sha256(f"{username}@{hostname}:{pid}".encode()).hexdigest()[:16]


def show_welcome_banner(
    version: str,
    git_repo: str | None,
    git_branch: str | None,
    mode: str,
    model: str,
    console: Console,
    profile: AgentProfile = None,
) -> None:
    """Display clean welcome banner with zen styling."""
    console.print()

    # Simple header - use profile name if available
    agent_name = profile.name.lower() if profile else "emdash"
    console.print(f"[{Colors.MUTED}]{header(agent_name, SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print(f"  [{Colors.DIM}]v{version}[/{Colors.DIM}]")
    console.print()

    # Info section
    if git_repo:
        branch_display = f" [{Colors.WARNING}]{git_branch}[/{Colors.WARNING}]" if git_branch else ""
        console.print(f"  [{Colors.DIM}]repo[/{Colors.DIM}]     [{Colors.SUCCESS}]{git_repo}[/{Colors.SUCCESS}]{branch_display}")

    # Display mode based on agent profile
    if profile and profile.agent_type == "coworker":
        display_mode = "coworker"
        mode_color = Colors.ACCENT
    else:
        display_mode = mode
        mode_color = Colors.WARNING if mode == "plan" else Colors.SUCCESS
    console.print(f"  [{Colors.DIM}]mode[/{Colors.DIM}]     [{mode_color}]{display_mode}[/{mode_color}]")
    console.print(f"  [{Colors.DIM}]model[/{Colors.DIM}]    [{Colors.MUTED}]{model}[/{Colors.MUTED}]")
    console.print()

    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    # Quick tips
    console.print(f"  [{Colors.DIM}]› /help commands   › @file include files   › Ctrl+C cancel[/{Colors.DIM}]")
    console.print()
from .file_utils import expand_file_references, fuzzy_find_files
from .menus import (
    get_clarification_response,
    get_choice_questions_response,
    show_plan_approval_menu,
    show_plan_mode_approval_menu,
)
from .handlers import (
    handle_agents,
    handle_session,
    handle_todos,
    handle_todo_add,
    handle_hooks,
    handle_rules,
    handle_skills,
    handle_index,
    handle_mcp,
    handle_registry,
    handle_auth,
    handle_doctor,
    handle_verify,
    handle_verify_loop,
    handle_setup,
    handle_status,
    handle_pr,
    handle_projectmd,
    handle_research,
    handle_context,
    handle_messages,
    handle_compact,
    handle_diff,
    handle_telegram,
    handle_stats,
    # Multiuser
    handle_share,
    handle_join,
    handle_leave,
    handle_who,
    handle_invite,
    handle_team,
    handle_multiuser_config,
    send_shared_message,
    broadcast_agent_response,
    broadcast_event,
    broadcast_typing,
)
from .sse_listener import SharedSessionListener

console = Console()


def render_with_interrupt(renderer, stream, broadcast_callback=None, client=None) -> dict:
    """Render stream with ESC key interrupt support.

    Args:
        renderer: SSE renderer instance
        stream: SSE stream iterator
        broadcast_callback: Optional callback(event_type, data) to broadcast events
        client: Optional API client for abort support

    Returns:
        Result dict from renderer, with 'interrupted' flag
    """
    import json
    from ...keyboard import KeyListener

    interrupt_event = threading.Event()

    def on_escape():
        interrupt_event.set()

    listener = KeyListener(on_escape)

    # Events to broadcast to multiuser participants - all agent events
    BROADCAST_EVENTS = {
        # Tool lifecycle
        "tool_start", "tool_result",
        # Sub-agent lifecycle
        "subagent_start", "subagent_end",
        # Agent thinking/progress
        "thinking", "progress",
        # Output
        "response", "partial_response", "assistant_text",
        # Interaction events
        "clarification", "clarification_response", "choice_questions",
        "plan_mode_requested", "plan_submitted",
        # Errors
        "error", "warning",
        # Context
        "context_frame",
    }

    # Wrap stream to broadcast events if callback provided
    def wrapped_stream():
        current_event_type = None
        for line in stream:
            if broadcast_callback:
                if line.startswith("event:"):
                    # Parse event type from "event: <type>" line
                    current_event_type = line[6:].strip()
                elif line.startswith("data:") and current_event_type in BROADCAST_EVENTS:
                    # Extract and broadcast the data (non-blocking)
                    try:
                        data_str = line[5:].strip()
                        if data_str and data_str != "[DONE]":
                            data = json.loads(data_str)
                            # Call broadcast in background to not slow down rendering
                            broadcast_callback(current_event_type, data)
                    except (json.JSONDecodeError, Exception):
                        pass  # Skip malformed data silently
                    current_event_type = None
                elif not line.strip():
                    # Empty line resets event tracking
                    current_event_type = None
            yield line

    try:
        listener.start()
        # Use wrapped stream if we have a broadcast callback
        actual_stream = wrapped_stream() if broadcast_callback else stream
        result = renderer.render_stream(actual_stream, interrupt_event=interrupt_event)

        # If interrupted and we have a client, call abort to stop the server-side agent
        if result.get("interrupted") and client and result.get("session_id"):
            try:
                client.abort_chat(result["session_id"])
            except Exception:
                pass  # Ignore abort errors - agent may have already stopped

        return result
    finally:
        listener.stop()


def run_single_task(
    client,
    renderer,
    task: str,
    model: str | None,
    max_iterations: int,
    options: dict,
):
    """Run a single agent task."""
    import click

    try:
        stream = client.agent_chat_stream(
            message=task,
            model=model,
            max_iterations=max_iterations,
            options=options,
        )
        result = render_with_interrupt(renderer, stream, client=client)
        if result.get("interrupted"):
            console.print("[dim]Task interrupted. You can continue or start a new task.[/dim]")
    except Exception as e:
        print_error(e)
        raise click.Abort()


def run_slash_command_task(
    client,
    renderer,
    model: str | None,
    max_iterations: int,
    task: str,
    options: dict,
):
    """Run a task from a slash command."""
    try:
        stream = client.agent_chat_stream(
            message=task,
            model=model,
            max_iterations=max_iterations,
            options=options,
        )
        result = render_with_interrupt(renderer, stream, client=client)
        if result.get("interrupted"):
            console.print("[dim]Task interrupted.[/dim]")
        console.print()
    except Exception as e:
        print_error(e)


def run_interactive(
    client,
    renderer,
    model: str | None,
    max_iterations: int,
    options: dict,
):
    """Run interactive REPL mode with slash commands."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.styles import Style
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.formatted_text import FormattedText
    from prompt_toolkit.lexers import Lexer
    import re

    # Get agent profile based on type (must be early for completer/help access)
    agent_type = options.get("agent_type", "coding")
    profile = get_agent_profile(agent_type)

    # Current mode
    current_mode = AgentMode(options.get("mode", "code"))
    session_id = None
    current_spec = None
    # Attached images for next message
    attached_images: list[dict] = []
    # Loaded messages from saved session (for restoration)
    loaded_messages: list[dict] = []
    # Pending todos to add when session starts
    pending_todos: list[str] = []

    # Multiuser shared session state
    shared_session_id: str | None = None  # The multiuser session ID (different from agent session_id)
    shared_user_id: str | None = None     # Our user ID in the shared session
    shared_invite_code: str | None = None # For display purposes
    shared_server_url: str | None = None  # Server URL for the shared session (may differ from client.base_url)
    is_shared_session: bool = False       # Quick check flag
    is_shared_owner: bool = False         # Whether we created/own the shared session
    sse_listener: SharedSessionListener | None = None  # Background listener for shared session events
    pending_multiuser_messages: queue.Queue = queue.Queue()  # Messages from other users to process

    # Style for prompt (emdash signature style)
    # Toolbar info (will be set later, but need closure access)
    toolbar_branch: str | None = None
    toolbar_model: str = "unknown"

    PROMPT_STYLE = Style.from_dict({
        "prompt.mode.plan": f"{Colors.WARNING} bold",
        "prompt.mode.code": f"{Colors.PRIMARY} bold",
        "prompt.prefix": Colors.MUTED,
        "prompt.cursor": f"{Colors.PRIMARY}",
        "prompt.image": Colors.ACCENT,
        "completion-menu": "bg:#1a1a2e #e8ecf0",
        "completion-menu.completion": "bg:#1a1a2e #e8ecf0",
        "completion-menu.completion.current": f"bg:#2a2a3e {Colors.SUCCESS} bold",
        "completion-menu.meta.completion": f"bg:#1a1a2e {Colors.MUTED}",
        "completion-menu.meta.completion.current": f"bg:#2a2a3e {Colors.SUBTLE}",
        "command": f"{Colors.PRIMARY} bold",
        # Styled completion text
        "slash-cmd": "#a8a2d2 bold",  # Light blue/purple for commands
        "sub-cmd": "#a8a2d2",  # Same blue for subcommands
        "file-ref": f"{Colors.WARNING}",
        # Zen bottom toolbar styles
        "bottom-toolbar": f"bg:#1a1a1a {Colors.DIM}",
        "bottom-toolbar.brand": f"bg:#1a1a1a {Colors.PRIMARY}",
        "bottom-toolbar.branch": f"bg:#1a1a1a {Colors.WARNING}",
        "bottom-toolbar.model": f"bg:#1a1a1a {Colors.ACCENT}",
        "bottom-toolbar.mode-code": f"bg:#1a1a1a {Colors.SUCCESS}",
        "bottom-toolbar.mode-plan": f"bg:#1a1a1a {Colors.WARNING}",
        "bottom-toolbar.session": f"bg:#1a1a1a {Colors.SUCCESS}",
        "bottom-toolbar.no-session": f"bg:#1a1a1a {Colors.MUTED}",
    })

    class SlashCommandCompleter(Completer):
        """Completer for slash commands and @file references."""

        def get_completions(self, document, complete_event):
            text = document.text_before_cursor

            # Handle @file completions
            # Find the last @ in the text
            at_idx = text.rfind('@')
            if at_idx != -1:
                # Get the query after @
                query = text[at_idx + 1:]
                # Only complete if query has at least 1 char and no space after @
                if query and ' ' not in query:
                    matches = fuzzy_find_files(query, limit=10)
                    cwd = Path.cwd()
                    for match in matches:
                        try:
                            rel_path = match.relative_to(cwd)
                        except ValueError:
                            rel_path = match
                        # Replace from @ onwards - styled display
                        styled_display = FormattedText([
                            ("class:file-ref", f"@{rel_path}")
                        ])
                        yield Completion(
                            f"@{rel_path}",
                            start_position=-(len(query) + 1),  # +1 for @
                            display=styled_display,
                            display_meta="file",
                        )
                    return

            # Handle slash commands
            if not text.startswith("/"):
                return

            # Check if we're completing a subcommand (e.g., "/telegram " or "/telegram c")
            parts = text.split(maxsplit=1)
            base_cmd = parts[0]

            # If we have a space after base command, show subcommands
            if len(parts) > 1 or text.endswith(" "):
                subcommand_prefix = parts[1] if len(parts) > 1 else ""
                if base_cmd in profile.slash_subcommands:
                    subcommands = profile.slash_subcommands[base_cmd]
                    for subcmd, description in subcommands.items():
                        if subcmd.startswith(subcommand_prefix):
                            # Styled display for subcommand
                            styled_display = FormattedText([
                                ("class:sub-cmd", subcmd)
                            ])
                            yield Completion(
                                subcmd,
                                start_position=-len(subcommand_prefix),
                                display=styled_display,
                                display_meta=description,
                            )
                return

            # Otherwise show main slash commands (use profile-specific commands)
            for cmd, description in profile.slash_commands.items():
                # Extract base command (e.g., "/pr" from "/pr [url]")
                cmd_base = cmd.split()[0]
                if cmd_base.startswith(text):
                    # Add space suffix for commands with subcommands to trigger subcommand completion
                    completion_text = cmd_base + " " if cmd_base in profile.slash_subcommands else cmd_base
                    # Styled display for slash command
                    styled_display = FormattedText([
                        ("class:slash-cmd", cmd)
                    ])
                    yield Completion(
                        completion_text,
                        start_position=-len(text),
                        display=styled_display,
                        display_meta=description,
                    )

    class CommandLexer(Lexer):
        """Lexer for syntax highlighting slash commands in input."""

        # Pattern for slash commands and subcommands
        COMMAND_PATTERN = re.compile(r'^(/\w+)(\s+\w+)?')
        # Pattern for @file references
        FILE_REF_PATTERN = re.compile(r'@[\w./\-_]+')

        def lex_document(self, document):
            """Return a callable that returns style for each line."""
            def get_line_tokens(line_number):
                line = document.lines[line_number]
                tokens = []
                pos = 0

                # Check for slash command at start of line
                cmd_match = self.COMMAND_PATTERN.match(line)
                if cmd_match:
                    # Main command
                    cmd = cmd_match.group(1)
                    tokens.append(("class:slash-cmd", cmd))
                    pos = len(cmd)

                    # Subcommand if present
                    if cmd_match.group(2):
                        subcmd = cmd_match.group(2)
                        tokens.append(("class:sub-cmd", subcmd))
                        pos += len(subcmd)

                # Process rest of line for @file references
                rest = line[pos:]
                last_end = 0
                for match in self.FILE_REF_PATTERN.finditer(rest):
                    # Text before match
                    if match.start() > last_end:
                        tokens.append(("", rest[last_end:match.start()]))
                    # The @file reference
                    tokens.append(("class:file-ref", match.group()))
                    last_end = match.end()

                # Remaining text
                if last_end < len(rest):
                    tokens.append(("", rest[last_end:]))

                return tokens

            return get_line_tokens

    # Setup history file
    history_file = Path.home() / ".emdash" / "cli_history"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history = FileHistory(str(history_file))

    # Key bindings: Enter submits, Alt+Enter inserts newline
    kb = KeyBindings()

    @kb.add("enter")
    def submit_on_enter(event):
        """Submit on Enter, or select completion if menu is open."""
        buffer = event.current_buffer
        # If completion menu is open, accept the selected completion
        if buffer.complete_state and buffer.complete_state.current_completion:
            completion = buffer.complete_state.current_completion
            buffer.apply_completion(completion)
            return
        # Otherwise submit the input
        buffer.validate_and_handle()

    @kb.add("tab")
    def select_completion_on_tab(event):
        """Select completion with Tab, or trigger completion menu."""
        buffer = event.current_buffer
        # If completion menu is open, accept the selected completion
        if buffer.complete_state and buffer.complete_state.current_completion:
            completion = buffer.complete_state.current_completion
            buffer.apply_completion(completion)
        else:
            # Trigger completion menu
            buffer.start_completion()

    @kb.add("escape", "enter")  # Alt+Enter (Escape then Enter)
    @kb.add("c-j")  # Ctrl+J as alternative for newline
    def insert_newline_alt(event):
        """Insert a newline character with Alt+Enter or Ctrl+J."""
        event.current_buffer.insert_text("\n")

    @kb.add("c-v")  # Ctrl+V to paste (check for images)
    def paste_with_image_check(event):
        """Paste text or attach image from clipboard."""
        nonlocal attached_images
        from ...clipboard import get_clipboard_image, get_image_from_path
        from emdash_core.utils.image import is_clipboard_image_available

        # Debug: Check if pyobjc is available
        try:
            import AppKit  # noqa: F401
            pyobjc_available = True
        except ImportError:
            pyobjc_available = False

        # Check if system clipboard has an image
        has_image = is_clipboard_image_available()

        # Try to get image from clipboard
        image_data = get_clipboard_image()
        if image_data:
            base64_data, img_format = image_data
            attached_images.append({"data": base64_data, "format": img_format})
            # Show feedback that image was attached
            console.print(f"  [{Colors.SUCCESS}]✓ Image {len(attached_images)} attached[/{Colors.SUCCESS}]")
            # Refresh prompt to show updated image list
            event.app.invalidate()
            return

        # Check if clipboard contains an image file path
        clipboard_data = event.app.clipboard.get_data()
        if clipboard_data and clipboard_data.text:
            text = clipboard_data.text.strip()
            # Remove escape characters from dragged paths (e.g., "path\ with\ spaces")
            clean_path = text.replace("\\ ", " ")
            # Check if it looks like an image file path
            if clean_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')):
                image_data = get_image_from_path(clean_path)
                if image_data:
                    base64_data, img_format = image_data
                    attached_images.append({"data": base64_data, "format": img_format})
                    console.print(f"  [{Colors.SUCCESS}]✓ Image {len(attached_images)} attached from file[/{Colors.SUCCESS}]")
                    event.app.invalidate()
                    return

        # Check if clipboard is empty or has no image
        if not clipboard_data or not clipboard_data.text:
            # Show diagnostic info
            if not pyobjc_available:
                console.print(f"  [{Colors.ERROR}]pyobjc not installed - run: pip install pyobjc[/{Colors.ERROR}]")
            elif has_image:
                console.print(f"  [{Colors.WARNING}]Image detected but failed to read[/{Colors.WARNING}]")
            else:
                console.print(f"  [{Colors.WARNING}]No image in clipboard[/{Colors.WARNING}]")
            console.print(f"  [{Colors.DIM}]Tip: Copy image first (Cmd+Shift+Ctrl+4 for screenshot to clipboard)[/{Colors.DIM}]")
            event.app.invalidate()
            return

        # Normal text paste
        event.current_buffer.paste_clipboard_data(clipboard_data)

    def check_for_image_path(buff):
        """Check if buffer contains an image path and attach it."""
        nonlocal attached_images
        text = buff.text.strip()
        if not text:
            return
        # Clean escaped spaces from dragged paths
        clean_text = text.replace("\\ ", " ")
        if clean_text.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')):
            from ...clipboard import get_image_from_path
            from prompt_toolkit.application import get_app
            image_data = get_image_from_path(clean_text)
            if image_data:
                base64_data, img_format = image_data
                attached_images.append({"data": base64_data, "format": img_format})
                # Clear the buffer
                buff.text = ""
                buff.cursor_position = 0
                # Refresh prompt to show image indicator
                try:
                    get_app().invalidate()
                except Exception:
                    pass

    def get_bottom_toolbar():
        """Bottom status bar with zen aesthetic - em-dashes and warm colors."""
        nonlocal current_mode, session_id, toolbar_branch, toolbar_model

        # Zen symbols
        em = "─"
        dot = "∷"

        # Build toolbar with zen aesthetic
        parts = [
            ("class:bottom-toolbar", f" {em}{em} "),
            ("class:bottom-toolbar.brand", "◈ emdash"),
        ]

        # Branch with stippled bullet
        if toolbar_branch:
            parts.append(("class:bottom-toolbar", f" {dot} "))
            parts.append(("class:bottom-toolbar.branch", toolbar_branch))

        # Model with stippled bullet
        if toolbar_model and toolbar_model != "unknown":
            parts.append(("class:bottom-toolbar", f" {dot} "))
            parts.append(("class:bottom-toolbar.model", toolbar_model))

        # Mode indicator
        parts.append(("class:bottom-toolbar", f" {em}{em} "))
        if current_mode == AgentMode.PLAN:
            parts.append(("class:bottom-toolbar.mode-plan", "▹ plan"))
        else:
            parts.append(("class:bottom-toolbar.mode-code", "▸ code"))

        # Session indicator
        if session_id:
            parts.append(("class:bottom-toolbar.session", " ●"))
        else:
            parts.append(("class:bottom-toolbar.no-session", " ○"))

        parts.append(("class:bottom-toolbar", " "))

        return parts

    session = PromptSession(
        history=history,
        completer=SlashCommandCompleter(),
        lexer=CommandLexer(),
        style=PROMPT_STYLE,
        complete_while_typing=True,
        multiline=True,
        prompt_continuation="     ",
        key_bindings=kb,
        bottom_toolbar=get_bottom_toolbar,
    )

    # Watch for image paths being pasted/dropped
    session.default_buffer.on_text_changed += check_for_image_path

    # Typing indicator state
    is_typing_sent = False

    def check_typing_indicator(buff):
        """Send typing indicator when user starts typing in a shared session."""
        nonlocal is_typing_sent, is_shared_session, shared_session_id, shared_user_id
        if not is_shared_session or not shared_session_id or not shared_user_id:
            return
        text = buff.text
        if text and not is_typing_sent:
            # User started typing - send indicator
            broadcast_typing(client, shared_session_id, shared_user_id, is_typing=True)
            is_typing_sent = True
        elif not text and is_typing_sent:
            # User cleared input - stop typing indicator
            broadcast_typing(client, shared_session_id, shared_user_id, is_typing=False)
            is_typing_sent = False

    session.default_buffer.on_text_changed += check_typing_indicator

    def get_prompt():
        """Get formatted prompt with distinctive emdash styling."""
        nonlocal attached_images, current_mode
        parts = []
        # Show attached images above prompt
        if attached_images:
            image_tags = " ".join(f"[Image {i+1}]" for i in range(len(attached_images)))
            parts.append(("class:prompt.image", f"  {image_tags}\n"))
        # Distinctive em-dash prompt with mode indicator
        mode_class = "class:prompt.mode.plan" if current_mode == AgentMode.PLAN else "class:prompt.mode.code"
        # Use em-dash as the signature prompt element
        parts.append(("class:prompt.prefix", "  "))
        parts.append((mode_class, f"─── "))
        parts.append(("class:prompt.cursor", "█ "))
        return parts

    def show_help():
        """Show available commands with zen styling (profile-specific)."""
        console.print()
        console.print(f"[{Colors.MUTED}]{header('Commands', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
        console.print()
        for cmd, desc in profile.slash_commands.items():
            console.print(f"  [{Colors.PRIMARY}]{cmd:18}[/{Colors.PRIMARY}] [{Colors.DIM}]{desc}[/{Colors.DIM}]")
        console.print()
        console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
        console.print()
        console.print(f"  [{Colors.DIM}]Type your task or question to interact with the agent.[/{Colors.DIM}]")
        console.print()

    def handle_slash_command(cmd: str) -> bool:
        """Handle a slash command. Returns True if should continue, False to exit."""
        nonlocal current_mode, session_id, current_spec, pending_todos, model, toolbar_model
        nonlocal shared_session_id, shared_user_id, shared_invite_code, shared_server_url, is_shared_session, is_shared_owner, sse_listener

        cmd_parts = cmd.strip().split(maxsplit=1)
        command = cmd_parts[0].lower()
        args = cmd_parts[1] if len(cmd_parts) > 1 else ""

        if command == "/quit" or command == "/exit" or command == "/q":
            return False

        elif command == "/help":
            if args:
                # Show contextual help for specific command
                show_command_help(args)
            else:
                show_help()

        elif command == "/plan":
            current_mode = AgentMode.PLAN
            # Reset session so next chat creates a new session with plan mode
            if session_id:
                session_id = None
                console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] [{Colors.WARNING}]plan mode[/{Colors.WARNING}] [{Colors.DIM}](session reset)[/{Colors.DIM}]")
            else:
                console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] [{Colors.WARNING}]plan mode[/{Colors.WARNING}]")

        elif command == "/code":
            current_mode = AgentMode.CODE
            # Reset session so next chat creates a new session with code mode
            if session_id:
                session_id = None
                console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] [{Colors.SUCCESS}]code mode[/{Colors.SUCCESS}] [{Colors.DIM}](session reset)[/{Colors.DIM}]")
            else:
                console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] [{Colors.SUCCESS}]code mode[/{Colors.SUCCESS}]")

        elif command == "/mode":
            mode_color = Colors.WARNING if current_mode == AgentMode.PLAN else Colors.SUCCESS
            console.print(f"  [{Colors.MUTED}]current mode:[/{Colors.MUTED}] [{mode_color}]{current_mode.value}[/{mode_color}]")

        elif command == "/model":
            from .handlers.models import handle_model
            new_model = handle_model(args, model or "")
            if new_model:
                model = new_model
                # Update toolbar display
                toolbar_model = new_model.split("/")[-1] if "/" in new_model else new_model

        elif command == "/reset":
            session_id = None
            current_spec = None
            console.print(f"  [{Colors.DIM}]session reset[/{Colors.DIM}]")

        elif command == "/spec":
            if current_spec:
                console.print(Panel(Markdown(current_spec), title="Current Spec"))
            else:
                console.print("[dim]No spec available. Use plan mode to create one.[/dim]")

        elif command == "/pr":
            handle_pr(args, run_slash_command_task, client, renderer, model, max_iterations)

        elif command == "/projectmd":
            handle_projectmd(run_slash_command_task, client, renderer, model, max_iterations)

        elif command == "/research":
            handle_research(args, run_slash_command_task, client, renderer, model)

        elif command == "/status":
            handle_status(client)

        elif command == "/stats":
            handle_stats(args, client, session_id)

        elif command == "/diff":
            handle_diff(args)

        elif command == "/agents":
            handle_agents(args, client, renderer, model, max_iterations, render_with_interrupt)

        elif command == "/todos":
            handle_todos(args, client, session_id, pending_todos)

        elif command == "/todo-add":
            handle_todo_add(args, client, session_id, pending_todos)

        elif command == "/session":
            # Use list wrappers to allow mutation
            session_id_ref = [session_id]
            current_spec_ref = [current_spec]
            current_mode_ref = [current_mode]
            loaded_messages_ref = [loaded_messages]

            handle_session(
                args, client, model,
                session_id_ref, current_spec_ref, current_mode_ref, loaded_messages_ref
            )

            # Update local variables from refs
            session_id = session_id_ref[0]
            current_spec = current_spec_ref[0]
            current_mode = current_mode_ref[0]
            loaded_messages[:] = loaded_messages_ref[0]

        elif command == "/hooks":
            handle_hooks(args)

        elif command == "/rules":
            handle_rules(args, client, renderer, model, max_iterations, render_with_interrupt)

        elif command == "/skills":
            handle_skills(args, client, renderer, model, max_iterations, render_with_interrupt)

        elif command == "/index":
            handle_index(args, client)

        elif command == "/context":
            handle_context(renderer)

        elif command == "/messages":
            handle_messages(client, session_id)

        elif command == "/paste" or command == "/image":
            # Attach image from clipboard
            from ...clipboard import get_clipboard_image
            import platform

            image_data = get_clipboard_image()
            if image_data:
                base64_data, img_format = image_data
                attached_images.append({"data": base64_data, "format": img_format})
                console.print(f"  [{Colors.SUCCESS}]✓ Image {len(attached_images)} attached[/{Colors.SUCCESS}]")
            else:
                console.print(f"  [{Colors.WARNING}]No image in clipboard[/{Colors.WARNING}]")
                if platform.system() == "Darwin":
                    console.print(f"  [{Colors.DIM}]1. Take screenshot: Cmd+Shift+4 (copies to clipboard)[/{Colors.DIM}]")
                    console.print(f"  [{Colors.DIM}]2. Or copy any image: Cmd+C[/{Colors.DIM}]")
                    console.print(f"  [{Colors.DIM}]3. Then type /paste or press Ctrl+V[/{Colors.DIM}]")
                    # Check if pyobjc is available
                    try:
                        import AppKit  # noqa: F401
                    except ImportError:
                        console.print(f"  [{Colors.ERROR}]Note: pyobjc not installed - run: pip install pyobjc[/{Colors.ERROR}]")
                else:
                    console.print(f"  [{Colors.DIM}]Copy an image first, then type /paste[/{Colors.DIM}]")

        elif command == "/compact":
            handle_compact(client, session_id)

        elif command == "/mcp":
            handle_mcp(args)

        elif command == "/registry":
            handle_registry(args)

        elif command == "/auth":
            handle_auth(args)

        elif command == "/doctor":
            handle_doctor(args)

        elif command == "/verify":
            handle_verify(args, client, renderer, model, max_iterations, render_with_interrupt)

        elif command == "/verify-loop":
            if not args:
                console.print("[yellow]Usage: /verify-loop <task description>[/yellow]")
                console.print("[dim]Example: /verify-loop fix the failing tests[/dim]")
                return True

            # Create a task runner function that uses current client/renderer
            def run_task(task_message: str):
                nonlocal session_id  # session_id is declared nonlocal in handle_slash_command
                if session_id:
                    stream = client.agent_continue_stream(session_id, task_message)
                else:
                    stream = client.agent_chat_stream(
                        message=task_message,
                        model=model,
                        max_iterations=max_iterations,
                        options={**options, "mode": current_mode.value},
                    )
                result = render_with_interrupt(renderer, stream, client=client)
                if result and result.get("session_id"):
                    session_id = result["session_id"]

            handle_verify_loop(args, run_task)
            return True

        elif command == "/setup":
            handle_setup(args, client, renderer, model)
            return True

        elif command == "/telegram":
            handle_telegram(args)
            return True

        # Multiuser commands
        elif command == "/share":
            plan_mode = current_mode == AgentMode.PLAN
            result = handle_share(args, client, session_id or "", model, plan_mode)
            if result.get("session_id"):
                # Enable shared session mode
                shared_session_id = result["session_id"]
                shared_invite_code = result.get("invite_code")
                shared_user_id = result.get("user_id") or _get_machine_user_id()
                shared_server_url = client.base_url  # Owner uses their local server
                is_shared_session = True
                is_shared_owner = True  # We created this session

                # Callback for processing messages from other users - runs in background thread
                def on_process_message(data: dict):
                    """Process a message from another user immediately in background."""
                    nonlocal session_id
                    msg_content = data.get("content", "")
                    msg_user_id = data.get("user_id", "")
                    msg_images = data.get("images")

                    if not msg_content:
                        return

                    console.print(f"\n[bold cyan]>>> Message from {msg_user_id}: {msg_content}[/bold cyan]")

                    # Create broadcast callback for this processing
                    def bc_callback(event_type: str, evt_data: dict):
                        # Run broadcast in a thread to not block
                        threading.Thread(
                            target=broadcast_event,
                            args=(client, shared_session_id, shared_user_id, event_type, evt_data),
                            daemon=True,
                        ).start()

                    try:
                        # Process with local agent
                        request_opts = {**options, "mode": current_mode.value}
                        if session_id:
                            stream = client.agent_continue_stream(
                                session_id, msg_content, images=msg_images
                            )
                        else:
                            stream = client.agent_chat_stream(
                                message=msg_content,
                                model=model,
                                max_iterations=max_iterations,
                                options=request_opts,
                                images=msg_images,
                            )

                        # Render with broadcast callback
                        result = render_with_interrupt(renderer, stream, broadcast_callback=bc_callback, client=client)

                        if result and result.get("session_id"):
                            session_id = result["session_id"]

                        # Broadcast final response
                        response_text = result.get("content", "") if result else ""
                        if response_text:
                            broadcast_agent_response(
                                client, shared_session_id, shared_user_id,
                                msg_user_id, msg_content, response_text,
                            )
                        console.print()

                    except Exception as e:
                        console.print(f"[red]Error processing message: {e}[/red]")

                # Start SSE listener for real-time events
                sse_listener = SharedSessionListener(
                    base_url=client.base_url,
                    session_id=shared_session_id,
                    user_id=shared_user_id,
                    on_process_message=on_process_message,
                    is_owner=True,
                )
                sse_listener.start()
                console.print(f"[dim]Listening for shared session events...[/dim]")
            return True

        elif command == "/join":
            result = handle_join(args, client)
            if result.get("session_id"):
                # Enable shared session mode
                shared_session_id = result["session_id"]
                shared_user_id = result.get("user_id") or _get_machine_user_id()
                is_shared_session = True
                is_shared_owner = False  # Joiner is not the owner

                # Get server URL from result (may be different from client.base_url)
                # This ensures we connect to the SAME server where the session was created
                shared_server_url = result.get("server_url", client.base_url)
                console.print(f"[dim]Using session server: {shared_server_url}[/dim]")

                # Start SSE listener for real-time events (use session's server)
                sse_listener = SharedSessionListener(
                    base_url=shared_server_url,
                    session_id=shared_session_id,
                    user_id=shared_user_id,
                )
                sse_listener.start()
                console.print(f"[dim]Listening for shared session events...[/dim]")
            return True

        elif command == "/leave":
            if is_shared_session and shared_session_id:
                # Stop SSE listener first
                if sse_listener:
                    sse_listener.stop()
                    sse_listener = None

                handle_leave(args, client, shared_session_id, shared_user_id or _get_machine_user_id())

                # Clear shared session state
                shared_session_id = None
                shared_user_id = None
                shared_invite_code = None
                shared_server_url = None
                is_shared_session = False
                is_shared_owner = False
                # Clear any pending messages
                while not pending_multiuser_messages.empty():
                    try:
                        pending_multiuser_messages.get_nowait()
                    except queue.Empty:
                        break
            else:
                console.print("[yellow]Not in a shared session.[/yellow]")
            return True

        elif command == "/who":
            if is_shared_session and shared_session_id:
                handle_who(args, client, shared_session_id)
            else:
                console.print("[yellow]Not in a shared session. Use /share or /join first.[/yellow]")
            return True

        elif command == "/invite":
            if is_shared_session and shared_session_id:
                handle_invite(args, client, shared_session_id)
            else:
                console.print("[yellow]Not in a shared session. Use /share first.[/yellow]")
            return True

        elif command == "/team":
            team_user_id = shared_user_id or _get_machine_user_id()
            handle_team(args, client, shared_session_id or "", team_user_id)
            return True

        elif command == "/multiuser":
            handle_multiuser_config(args)
            return True

        else:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")
            console.print("[dim]Type /help for available commands[/dim]")

        return True

    # Check for first run and show onboarding
    if is_first_run():
        run_onboarding()

    # Check for recent session to restore
    recent_session = get_recent_session(client)
    if recent_session:
        choice, session_data = show_session_restore_prompt(recent_session)
        if choice == "restore" and session_data:
            session_id = session_data.get("name")
            if session_data.get("mode"):
                current_mode = AgentMode(session_data["mode"])
            console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] Session restored: {session_id}")
            console.print()

    # Show welcome message
    from ... import __version__

    # Get current working directory
    cwd = Path.cwd()

    # Get git repo name (if in a git repo)
    git_repo = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=cwd
        )
        if result.returncode == 0:
            git_repo = Path(result.stdout.strip()).name
    except Exception:
        pass

    # Get current git branch
    git_branch = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            git_branch = result.stdout.strip()
    except Exception:
        pass

    # Get display model name
    if model:
        display_model = model
    else:
        from emdash_core.agent.providers.factory import DEFAULT_MODEL
        display_model = DEFAULT_MODEL

    # Shorten model name for display
    if "/" in display_model:
        display_model = display_model.split("/")[-1]

    # Update toolbar variables for the bottom bar
    toolbar_branch = git_branch
    toolbar_model = display_model

    # Welcome banner
    show_welcome_banner(
        version=__version__,
        git_repo=git_repo,
        git_branch=git_branch,
        mode=current_mode.value,
        model=display_model,
        console=console,
        profile=profile,
    )

    def process_pending_multiuser_message():
        """Process a pending message from another user in the shared session.

        Called by the owner to process messages queued via SSE events.
        Returns True if a message was processed, False otherwise.
        """
        nonlocal session_id, shared_session_id, shared_user_id

        try:
            # Non-blocking check for pending messages
            msg_data = pending_multiuser_messages.get_nowait()
        except queue.Empty:
            return False

        # Extract message details
        msg_content = msg_data.get("content", "")
        msg_user_id = msg_data.get("user_id", "")
        msg_images = msg_data.get("images")

        if not msg_content:
            return False

        console.print()
        console.print(f"[bold cyan]Processing message from other user...[/bold cyan]")

        # Build options for the request
        request_options = {
            **options,
            "mode": current_mode.value,
        }

        # Create callback to broadcast events in real-time
        def make_broadcast_callback():
            sid = shared_session_id
            uid = shared_user_id
            def callback(event_type: str, data: dict):
                broadcast_event(client, sid, uid, event_type, data)
            return callback

        bc_callback = make_broadcast_callback() if shared_session_id and shared_user_id else None

        try:
            # Process with local agent
            if session_id:
                stream = client.agent_continue_stream(
                    session_id, msg_content, images=msg_images
                )
            else:
                stream = client.agent_chat_stream(
                    message=msg_content,
                    model=model,
                    max_iterations=max_iterations,
                    options=request_options,
                    images=msg_images,
                )

            # Pass broadcast callback for real-time event parity
            result = render_with_interrupt(renderer, stream, broadcast_callback=bc_callback, client=client)

            if result and result.get("session_id"):
                session_id = result["session_id"]

            # Final response broadcast (for clients that joined late or missed events)
            response_text = result.get("content", "") if result else ""
            if response_text and shared_session_id and shared_user_id:
                broadcast_agent_response(
                    client,
                    shared_session_id,
                    shared_user_id,
                    msg_user_id,  # Original sender
                    msg_content,
                    response_text,
                )

            console.print()
            return True

        except Exception as e:
            console.print(f"[red]Error processing shared message: {e}[/red]")
            return False

    while True:
        try:
            # Check for pending multiuser messages (owner only)
            if is_shared_owner and is_shared_session:
                while process_pending_multiuser_message():
                    pass  # Process all pending messages

            # Get user input
            user_input = session.prompt(get_prompt()).strip()

            # Reset typing indicator after submitting
            if is_typing_sent and is_shared_session and shared_session_id and shared_user_id:
                broadcast_typing(client, shared_session_id, shared_user_id, is_typing=False)
                is_typing_sent = False

            if not user_input:
                continue

            # Check if input is an image file path (dragged file)
            clean_input = user_input.replace("\\ ", " ")
            if clean_input.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')):
                from ...clipboard import get_image_from_path
                image_data = get_image_from_path(clean_input)
                if image_data:
                    base64_data, img_format = image_data
                    attached_images.append({"data": base64_data, "format": img_format})
                    continue  # Prompt again for actual message

            # Handle slash commands
            if user_input.startswith("/"):
                if not handle_slash_command(user_input):
                    break
                continue

            # Handle quit shortcuts
            if user_input.lower() in ("quit", "exit", "q"):
                break

            # Expand @file references in the message
            expanded_input, included_files = expand_file_references(user_input)
            if included_files:
                console.print(f"[dim]Including {len(included_files)} file(s): {', '.join(Path(f).name for f in included_files)}[/dim]")

            # Build options with current mode
            request_options = {
                **options,
                "mode": current_mode.value,
            }

            # Run agent with current mode
            try:
                # Prepare images for API call
                images_to_send = attached_images if attached_images else None

                # Check if we're in a shared session
                if is_shared_session and shared_session_id and shared_user_id:
                    if is_shared_owner:
                        # Owner processes locally and broadcasts to others in real-time
                        # Create callback to broadcast events as they stream (threaded for speed)
                        def make_broadcast_callback():
                            sid = shared_session_id
                            uid = shared_user_id
                            def callback(event_type: str, data: dict):
                                # Run broadcast in background thread to not slow rendering
                                threading.Thread(
                                    target=broadcast_event,
                                    args=(client, sid, uid, event_type, data),
                                    daemon=True,
                                ).start()
                            return callback

                        bc_callback = make_broadcast_callback()

                        # Use normal agent flow with broadcast callback
                        if session_id:
                            stream = client.agent_continue_stream(
                                session_id, expanded_input, images=images_to_send
                            )
                        else:
                            stream = client.agent_chat_stream(
                                message=expanded_input,
                                model=model,
                                max_iterations=max_iterations,
                                options=request_options,
                                images=images_to_send,
                                history=loaded_messages if loaded_messages else None,
                            )
                            loaded_messages.clear()

                        attached_images = []
                        # Pass broadcast callback for real-time event parity
                        result = render_with_interrupt(renderer, stream, broadcast_callback=bc_callback, client=client)

                        if result and result.get("session_id"):
                            session_id = result["session_id"]

                        # Final response text broadcast (for clients that joined late or missed events)
                        response_text = result.get("content", "") if result else ""
                        if response_text and shared_session_id and shared_user_id:
                            broadcast_agent_response(
                                client,
                                shared_session_id,
                                shared_user_id,
                                None,  # Owner's own message
                                expanded_input,
                                response_text,
                            )
                        console.print()
                        continue
                    else:
                        # Non-owner: send via multiuser API (queued)
                        # Use shared_server_url to ensure message goes to correct server
                        msg_result = send_shared_message(
                            client,
                            shared_session_id,
                            shared_user_id,
                            expanded_input,
                            images=images_to_send,
                            server_url=shared_server_url,
                        )

                        if msg_result:
                            if msg_result.get("agent_busy"):
                                queue_pos = msg_result.get("queue_position", 0)
                                console.print(f"[dim]Message queued (position {queue_pos + 1}). Response will appear below.[/dim]")
                            else:
                                console.print(f"[dim]Message sent. Response will appear below.[/dim]")
                            # Response will come via SSE listener running in background

                        # Clear attached images after sending
                        attached_images = []
                        continue  # Skip normal flow, response comes via SSE

                elif session_id:
                    stream = client.agent_continue_stream(
                        session_id, expanded_input, images=images_to_send
                    )
                else:
                    # Pass loaded_messages from saved session if available
                    stream = client.agent_chat_stream(
                        message=expanded_input,
                        model=model,
                        max_iterations=max_iterations,
                        options=request_options,
                        images=images_to_send,
                        history=loaded_messages if loaded_messages else None,
                    )
                    # Clear loaded_messages after first use
                    loaded_messages.clear()

                # Clear attached images after sending
                attached_images = []

                # Render the stream and capture any spec output
                result = render_with_interrupt(renderer, stream, client=client)

                # Check if we got a session ID back
                if result and result.get("session_id"):
                    session_id = result["session_id"]

                    # Add any pending todos now that we have a session
                    if pending_todos:
                        for todo_title in pending_todos:
                            try:
                                client.add_todo(session_id, todo_title)
                            except Exception:
                                pass  # Silently ignore errors adding todos
                        pending_todos.clear()

                # Check for spec output
                if result and result.get("spec"):
                    current_spec = result["spec"]

                # Handle clarifications (may be chained - loop until no more)
                while True:
                    clarification = result.get("clarification")
                    if not (clarification and session_id):
                        break

                    response = get_clarification_response(clarification)
                    if not response:
                        break

                    # Show the user's selection in the chat
                    console.print()
                    console.print(f"[dim]Selected:[/dim] [bold]{response}[/bold]")
                    console.print()

                    # Use dedicated clarification answer endpoint
                    try:
                        stream = client.clarification_answer_stream(session_id, response)
                        result = render_with_interrupt(renderer, stream, client=client)

                        # Update mode if user chose code
                        if "code" in response.lower():
                            current_mode = AgentMode.CODE
                    except (
                        httpx.RemoteProtocolError,
                        httpx.ReadError,
                        httpx.ConnectError,
                        httpx.ReadTimeout,
                        ConnectionRefusedError,
                    ) as e:
                        # Connection error - break clarification loop but stay in REPL
                        console.print(f"[{Colors.WARNING}]Connection lost[/{Colors.WARNING}]: {type(e).__name__}")
                        break
                    except Exception as e:
                        error_str = str(e).lower()
                        if "connection refused" in error_str:
                            console.print(f"[{Colors.WARNING}]Connection lost[/{Colors.WARNING}]")
                        else:
                            print_error(e, "Error continuing session")
                        break

                # Handle choice questions (may be chained - loop until no more)
                while True:
                    choice_questions = result.get("choice_questions")
                    if not (choice_questions and session_id):
                        break

                    responses = get_choice_questions_response(choice_questions)
                    if not responses:
                        break

                    # Show the user's selections in the chat
                    console.print()
                    for resp in responses:
                        q = resp.get("question", "")[:40]
                        a = resp.get("answer", "")
                        console.print(f"[dim]{q}:[/dim] [bold]{a}[/bold]")
                    console.print()

                    # Use dedicated choices answer endpoint
                    try:
                        stream = client.choice_questions_answer_stream(session_id, responses)
                        result = render_with_interrupt(renderer, stream, client=client)
                    except (
                        httpx.RemoteProtocolError,
                        httpx.ReadError,
                        httpx.ConnectError,
                        httpx.ReadTimeout,
                        ConnectionRefusedError,
                    ) as e:
                        # Connection error - break loop but stay in REPL
                        console.print(f"[{Colors.WARNING}]Connection lost[/{Colors.WARNING}]: {type(e).__name__}")
                        break
                    except Exception as e:
                        error_str = str(e).lower()
                        if "connection refused" in error_str:
                            console.print(f"[{Colors.WARNING}]Connection lost[/{Colors.WARNING}]")
                        else:
                            print_error(e, "Error continuing session")
                        break

                # Handle plan mode entry request (show approval menu)
                plan_mode_requested = result.get("plan_mode_requested")
                if plan_mode_requested is not None and session_id:
                    choice, feedback = show_plan_mode_approval_menu()

                    if choice == "approve":
                        current_mode = AgentMode.PLAN
                        console.print()
                        console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] [{Colors.WARNING}]plan mode activated[/{Colors.WARNING}]")
                        console.print()
                        # Use the planmode approve endpoint
                        stream = client.planmode_approve_stream(session_id)
                        result = render_with_interrupt(renderer, stream, client=client)
                        # After approval, check if there's now a plan submitted
                        if result.get("plan_submitted"):
                            pass  # plan_submitted will be handled below
                    elif choice == "feedback":
                        # Use the planmode reject endpoint - stay in code mode
                        stream = client.planmode_reject_stream(session_id, feedback)
                        render_with_interrupt(renderer, stream, client=client)

                # Handle plan mode completion (show approval menu)
                # Only show menu when agent explicitly submits a plan via exit_plan tool
                plan_submitted = result.get("plan_submitted")
                should_show_plan_menu = (
                    current_mode == AgentMode.PLAN and
                    session_id and
                    plan_submitted is not None  # Agent called exit_plan tool
                )
                if should_show_plan_menu:
                    choice, feedback = show_plan_approval_menu()

                    if choice == "approve":
                        current_mode = AgentMode.CODE
                        # Use the plan approve endpoint which properly resets mode on server
                        stream = client.plan_approve_stream(session_id)
                        render_with_interrupt(renderer, stream, client=client)
                    elif choice == "feedback":
                        if feedback:
                            # Use the plan reject endpoint which keeps mode as PLAN on server
                            stream = client.plan_reject_stream(session_id, feedback)
                            render_with_interrupt(renderer, stream, client=client)
                        else:
                            console.print("[dim]No feedback provided[/dim]")
                            session_id = None
                            current_spec = None

                console.print()

            except (httpx.ConnectError, ConnectionRefusedError, OSError) as e:
                # Connection refused - server is likely down
                error_str = str(e).lower()
                console.print()
                if "connection refused" in error_str or "errno 61" in error_str or "errno 111" in error_str:
                    console.print(f"[{Colors.ERROR}]Server not running[/{Colors.ERROR}]")
                    console.print(f"[{Colors.DIM}]Start the server with: em serve[/{Colors.DIM}]")
                else:
                    console.print(f"[{Colors.WARNING}]Connection failed[/{Colors.WARNING}]: {type(e).__name__}")
                    console.print(f"[{Colors.DIM}]Check if the server is running: em serve[/{Colors.DIM}]")
                console.print()
                # Don't break - let user retry after starting server

            except (
                httpx.RemoteProtocolError,
                httpx.ReadError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.ConnectTimeout,
            ) as e:
                # Connection errors during streaming - show friendly message and keep REPL running
                console.print()
                console.print(f"[{Colors.WARNING}]Connection interrupted[/{Colors.WARNING}]: {type(e).__name__}")
                console.print(f"[{Colors.DIM}]The server connection was lost. Your session is preserved - try your request again.[/{Colors.DIM}]")
                console.print()
                # Don't break - let user retry

            except httpx.HTTPStatusError as e:
                # HTTP errors (4xx, 5xx) - show error but keep REPL running
                console.print()
                console.print(f"[{Colors.ERROR}]Server error[/{Colors.ERROR}]: {e.response.status_code}")
                if e.response.status_code >= 500:
                    console.print(f"[{Colors.DIM}]The server encountered an error. Try again or check server logs.[/{Colors.DIM}]")
                console.print()

            except Exception as e:
                # Check if it's a connection error wrapped in another exception
                error_str = str(e).lower()
                if "connection refused" in error_str or "errno 61" in error_str:
                    console.print()
                    console.print(f"[{Colors.ERROR}]Server not running[/{Colors.ERROR}]")
                    console.print(f"[{Colors.DIM}]Start the server with: em serve[/{Colors.DIM}]")
                    console.print()
                else:
                    print_error(e)

        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted[/dim]")
            break
        except EOFError:
            break

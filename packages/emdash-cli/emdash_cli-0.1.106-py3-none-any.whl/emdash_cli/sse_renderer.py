"""SSE event renderer for Rich terminal output."""

import json
import os
import sys
import textwrap
import time
import threading
from typing import Iterator, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from .design import (
    SPINNER_FRAMES,
    Colors,
    ANSI,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    STATUS_ERROR,
    STATUS_INFO,
    DOT_ACTIVE,
    DOT_BULLET,
    NEST_LINE,
    ARROW_RIGHT,
    header,
    footer,
    progress_bar,
    EM_DASH,
)
from .diff_renderer import render_file_change


class SSERenderer:
    """Renders SSE events to Rich terminal output with live updates.

    Features:
    - Animated spinner while tools execute
    - Special UI for spawning sub-agents
    - Clean, minimal output
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        verbose: bool = True,
    ):
        """Initialize the renderer.

        Args:
            console: Rich console to render to (creates one if not provided)
            verbose: Whether to show tool calls and progress
        """
        self.console = console or Console()
        self.verbose = verbose
        self._partial_response = ""
        self._session_id = None
        self._spec = None
        self._spec_submitted = False
        self._plan_submitted = None  # Plan data when submit_plan tool is called
        self._plan_mode_requested = None  # Plan mode request data
        self._pending_clarification = None
        self._pending_choice_questions = None  # Choice questions data

        # Live display state
        self._current_tool = None
        self._tool_count = 0
        self._completed_tools: list[dict] = []
        self._pending_tools: dict = {}  # For parallel tool execution support
        self._spinner_idx = 0
        self._waiting_for_next = False

        # Sub-agent state (for inline updates)
        self._subagent_tool_count = 0
        self._subagent_current_tool = None
        self._subagent_type = None
        self._in_subagent_mode = False  # Track when sub-agent is running

        # Spinner animation thread
        self._spinner_thread: Optional[threading.Thread] = None
        self._spinner_running = False
        self._spinner_message = "thinking"
        self._spinner_lock = threading.Lock()

        # Extended thinking storage
        self._last_thinking: Optional[str] = None

        # Context frame storage (rendered at end of stream)
        self._last_context_frame: Optional[dict] = None

        # In-place tool update tracking (Claude Code style)
        self._tool_line_active = False  # Whether we have an active tool line to update
        self._current_tool_name = ""    # Current tool name (for colored display)
        self._current_tool_args = ""    # Current tool args (for muted display)
        self._current_tool_line = ""    # Full line for subagent display
        self._action_count = 0          # Total actions executed
        self._error_count = 0           # Total errors
        self._start_time = None         # Session start time

        # Floating todo list state
        self._floating_todos: Optional[list] = None  # Current todo list (when active)
        self._todo_panel_height = 0  # Height of the todo panel (for cursor positioning)

        # Floating file changes state
        self._floating_file_changes: Optional[list] = None  # Current file changes (when active)
        self._file_changes_panel_height = 0  # Height of panel (for cursor positioning)

    def reset(self) -> None:
        """Reset renderer state between sessions to prevent resource accumulation."""
        # Stop any running spinner
        self._stop_spinner()

        # Reset state that could accumulate
        self._completed_tools = []
        self._pending_tools = {}
        self._floating_todos = None
        self._floating_file_changes = None
        self._tool_line_active = False
        self._current_tool_line = ""
        self._action_count = 0
        self._error_count = 0

    def render_stream(
        self,
        lines: Iterator[str],
        interrupt_event: Optional[threading.Event] = None,
    ) -> dict:
        """Render SSE stream to terminal.

        Args:
            lines: Iterator of SSE lines from HTTP response
            interrupt_event: Optional event to signal interruption (e.g., ESC pressed)

        Returns:
            Dict with session_id, content, spec, interrupted flag, and other metadata
        """
        # Clean up any lingering state from previous stream
        self._stop_spinner()
        self._completed_tools = []
        self._pending_tools = {}

        current_event = None
        final_response = ""
        interrupted = False
        self._last_thinking = None  # Reset thinking storage
        self._pending_clarification = None  # Reset clarification state
        self._pending_choice_questions = None  # Reset choice questions state
        self._plan_submitted = None  # Reset plan state
        self._plan_mode_requested = None  # Reset plan mode request state

        # Start spinner while waiting for first event
        if self.verbose:
            self._start_spinner("thinking")

        try:
            for line in lines:
                # Check for interrupt signal
                if interrupt_event and interrupt_event.is_set():
                    self._stop_spinner()
                    self.console.print("\n[yellow]Cancelled[/yellow]")
                    interrupted = True
                    # Close the generator to terminate the HTTP stream
                    if hasattr(lines, 'close'):
                        lines.close()
                    break

                line = line.strip()

                if line.startswith("event: "):
                    current_event = line[7:]
                elif line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        # Ensure data is a dict (could be null/None from JSON)
                        if data is None:
                            data = {}
                        if current_event:
                            result = self._handle_event(current_event, data)
                            if result:
                                final_response = result
                    except json.JSONDecodeError:
                        pass
                elif line == ": ping":
                    # SSE keep-alive - ensure spinner is running
                    if self.verbose and not self._spinner_running:
                        self._start_spinner("waiting")
        finally:
            # Always stop spinner when stream ends
            self._stop_spinner()
            # Finalize any active tool line
            self._finalize_tool_line()
            # Clear floating todos (they stay visible as part of output)
            self._clear_floating_todos()
            # Clear floating file changes (they stay visible as part of output)
            self._clear_floating_file_changes()

        # Render context frame at the end (only once)
        if self.verbose:
            self._render_final_context_frame()
        # Keep _last_context_frame for /context command access

        return {
            "content": final_response,
            "session_id": self._session_id,
            "spec": self._spec,
            "spec_submitted": self._spec_submitted,
            "plan_submitted": self._plan_submitted,
            "plan_mode_requested": self._plan_mode_requested,
            "clarification": self._pending_clarification,
            "choice_questions": self._pending_choice_questions,
            "interrupted": interrupted,
            "thinking": self._last_thinking,
        }

    def _start_spinner(self, message: str = "thinking") -> None:
        """Start the animated spinner in a background thread."""
        # Stop any existing spinner first to prevent thread accumulation
        if self._spinner_running or self._spinner_thread:
            self._stop_spinner()

        self._spinner_message = message
        self._spinner_running = True

        # Show first frame immediately (don't wait for thread tick)
        if not self._tool_line_active:
            wave_frames = ["●○○○○", "○●○○○", "○○●○○", "○○○●○", "○○○○●"]
            with self._spinner_lock:
                sys.stdout.write(f"\r  {ANSI.PRIMARY}─{ANSI.RESET} {ANSI.WARNING}{wave_frames[0]}{ANSI.RESET} {ANSI.MUTED}{message}{ANSI.RESET}      ")
                sys.stdout.flush()

        self._spinner_thread = threading.Thread(target=self._spinner_loop, daemon=True)
        self._spinner_thread.start()

    def _stop_spinner(self) -> None:
        """Stop the spinner and clear the line."""
        if not self._spinner_running and not self._spinner_thread:
            return

        self._spinner_running = False
        if self._spinner_thread:
            # Wait longer for thread to finish to prevent accumulation
            self._spinner_thread.join(timeout=0.5)
            # Force cleanup even if thread didn't stop
            self._spinner_thread = None

        # Clear the spinner line (only if no tool line is active)
        if not self._tool_line_active:
            with self._spinner_lock:
                sys.stdout.write("\r" + " " * 60 + "\r")
                sys.stdout.flush()

    def _spinner_loop(self) -> None:
        """Background thread that animates the spinner with bouncing dot."""
        # Alternative: wave dots
        wave_frames = [
            "●○○○○",
            "○●○○○",
            "○○●○○",
            "○○○●○",
            "○○○○●",
            "○○○●○",
            "○○●○○",
            "○●○○○",
        ]
        frame_idx = 0
        while self._spinner_running:
            # Don't animate spinner if a tool line is active
            if self._tool_line_active:
                time.sleep(0.1)
                continue

            with self._spinner_lock:
                frame_idx = (frame_idx + 1) % len(wave_frames)
                dots = wave_frames[frame_idx]
                # Animated dots with em-dash framing
                sys.stdout.write(f"\r  {ANSI.PRIMARY}─{ANSI.RESET} {ANSI.WARNING}{dots}{ANSI.RESET} {ANSI.MUTED}{self._spinner_message}{ANSI.RESET}      ")
                sys.stdout.flush()
            time.sleep(0.1)

    def _show_waiting(self) -> None:
        """Show waiting animation (starts spinner if not running)."""
        if not self._spinner_running:
            self._start_spinner("waiting")

    def _clear_waiting(self) -> None:
        """Clear waiting line (stops spinner)."""
        self._stop_spinner()
        self._waiting_for_next = False

    def _handle_event(self, event_type: str, data: dict) -> Optional[str]:
        """Handle individual SSE event."""
        # Ensure data is a dict
        if not isinstance(data, dict):
            data = {}

        # Clear waiting indicator when new event arrives (but not for sub-agent events)
        subagent_id = data.get("subagent_id") if isinstance(data, dict) else None
        if not subagent_id and not self._in_subagent_mode:
            self._clear_waiting()

        if event_type == "session_start":
            self._render_session_start(data)
        elif event_type == "tool_start":
            self._render_tool_start(data)
        elif event_type == "tool_result":
            self._render_tool_result(data)
            # Start spinner while waiting for next tool/response
            self._waiting_for_next = True
            if self.verbose:
                self._start_spinner("thinking")
        elif event_type == "subagent_start":
            self._render_subagent_start(data)
        elif event_type == "subagent_end":
            self._render_subagent_end(data)
        elif event_type == "thinking":
            self._render_thinking(data)
        elif event_type == "assistant_text":
            self._render_assistant_text(data)
        elif event_type == "progress":
            self._render_progress(data)
        elif event_type == "partial_response":
            self._render_partial(data)
        elif event_type == "response":
            return self._render_response(data)
        elif event_type == "clarification":
            self._render_clarification(data)
        elif event_type == "choice_questions":
            self._render_choice_questions(data)
        elif event_type == "plan_mode_requested":
            self._render_plan_mode_requested(data)
        elif event_type == "plan_submitted":
            self._render_plan_submitted(data)
        elif event_type == "error":
            self._render_error(data)
        elif event_type == "warning":
            self._render_warning(data)
        elif event_type == "session_end":
            self._render_session_end(data)
        elif event_type == "context_frame":
            self._render_context_frame(data)

        return None

    def _render_session_start(self, data: dict) -> None:
        """Render session start event."""
        if data.get("session_id"):
            self._session_id = data["session_id"]

        if not self.verbose:
            return

        agent = data.get("agent_name", "Agent")

        self.console.print()
        self.console.print(f"  [{Colors.PRIMARY} bold]{agent}[/{Colors.PRIMARY} bold]")

        # Reset counters for Claude Code style tracking
        self._tool_count = 0
        self._completed_tools = []
        self._action_count = 0
        self._error_count = 0
        self._start_time = time.time()

        # Start spinner while waiting for first tool
        self._start_spinner("thinking")

    def _render_tool_start(self, data: dict) -> None:
        """Render tool start event - show spinner line for current tool."""
        if not self.verbose:
            return

        name = data.get("name", "unknown")
        args = data.get("args", {})
        tool_id = data.get("tool_id")
        subagent_id = data.get("subagent_id")
        subagent_type = data.get("subagent_type")

        self._tool_count += 1
        self._action_count += 1

        # Store tool info for result rendering (keyed by tool_id for parallel support)
        key = tool_id or name
        self._pending_tools[key] = {"name": name, "args": args, "start_time": time.time(), "tool_id": tool_id, "committed": False}
        self._current_tool = self._pending_tools[key]

        # Stop spinner when tool starts
        self._stop_spinner()

        # Special handling for task tool (spawning sub-agents)
        if name == "task":
            self._render_agent_spawn_start(args)
            return

        # Sub-agent events: show on single updating line
        if subagent_id:
            self._subagent_tool_count += 1
            self._subagent_current_tool = name
            args_summary = self._format_tool_args_short(name, args)
            self._show_spinner_line(f"{name}({args_summary})")
            return

        # NOTE: Floating file changes panel disabled - cursor-based updates don't work
        # well with interleaved output (spinners, thinking, etc.)
        # TODO: Re-enable when we have a better approach (e.g., status bar)

        # For parallel tool calls: if there's already an active spinner, commit it first
        # This allows multiple tools to be shown stacked
        if self._tool_line_active and self._current_tool_name:
            self._commit_tool_line()

        # Show tool with spinner (will be finalized when result comes)
        args_summary = self._format_tool_args_short(name, args)
        self._show_tool_spinner(name, args_summary)

    def _render_subagent_progress(self, agent_type: str, tool_name: str, args: dict) -> None:
        """Render sub-agent tool call with indentation."""
        # Use stored type if not provided
        agent_type = agent_type or self._subagent_type or "Agent"

        # Get a short summary of what's being done
        summary = ""
        if "path" in args:
            path = str(args["path"])
            # Shorten long paths
            if len(path) > 60:
                summary = "..." + path[-57:]
            else:
                summary = path
        elif "pattern" in args:
            summary = str(args["pattern"])[:60]
        elif "query" in args:
            summary = str(args["query"])[:60]

        # Print tool call on its own line with indentation (zen style)
        if summary:
            self.console.print(f"    [{Colors.DIM}]{NEST_LINE}[/{Colors.DIM}] [{Colors.MUTED}]{DOT_ACTIVE}[/{Colors.MUTED}] {tool_name} [{Colors.DIM}]{summary}[/{Colors.DIM}]")
        else:
            self.console.print(f"    [{Colors.DIM}]{NEST_LINE}[/{Colors.DIM}] [{Colors.MUTED}]{DOT_ACTIVE}[/{Colors.MUTED}] {tool_name}")

    def _render_agent_spawn_start(self, args: dict) -> None:
        """Track sub-agent spawn state (rendering done by subagent_start event)."""
        agent_type = args.get("subagent_type", "Explore")

        # Enter sub-agent mode: stop spinner, track state
        self._stop_spinner()
        self._in_subagent_mode = True

        # Reset sub-agent tracking
        self._subagent_tool_count = 0
        self._subagent_current_tool = None
        self._subagent_type = agent_type

        # Don't render here - subagent_start event will render the UI

    def _render_tool_result(self, data: dict) -> None:
        """Render tool result - finalize the tool line with result."""
        name = data.get("name", "unknown")
        success = data.get("success", True)
        summary = data.get("summary")
        subagent_id = data.get("subagent_id")

        # Track errors
        if not success:
            self._error_count += 1

        # Detect spec submission
        if name == "submit_spec" and success:
            self._spec_submitted = True
            spec_data = data.get("data") or {}
            if spec_data:
                self._spec = spec_data.get("content")

        # Get tool info early (needed for committed check)
        pending_tools = getattr(self, '_pending_tools', {})
        tool_id = data.get("tool_id")
        key = tool_id or name
        tool_info = pending_tools.get(key) or {}
        is_committed = tool_info.get("committed", False)

        # Handle todo tools specially - show floating todo panel
        if name in ("write_todo", "update_todo_list") and success:
            tool_data = data.get("data") or {}
            # Backend returns 'all_tasks' not 'todos'
            tasks = tool_data.get("all_tasks", [])
            if tasks and self.verbose:
                # Convert backend format to renderer format
                todos = []
                for task in tasks:
                    todos.append({
                        "content": task.get("title", ""),
                        "status": task.get("status", "pending"),
                        "activeForm": task.get("title", ""),
                    })
                # Finalize current tool line first (only if not committed)
                if not is_committed:
                    self._finalize_tool_spinner(success)
                pending_tools.pop(key, None)
                self._update_floating_todos(todos)
                return  # Don't show tool line for todo tools

        # Handle file edit tools - show mini diff (this is important to keep)
        if name in ("write_file", "write_to_file", "apply_diff", "edit", "str_replace_editor") and success:
            tool_data = data.get("data") or {}  # Handle None explicitly
            args = data.get("args") or {}
            # Finalize tool line before showing diff (only if not committed)
            if not is_committed:
                self._finalize_tool_spinner(success)
            self._render_file_change_inline(name, tool_data, args)
            # Mark as handled
            pending_tools.pop(key, None)
            self._current_tool = None
            return

        if not self.verbose:
            return

        # Special handling for task tool result
        if name == "task":
            self._render_agent_spawn_result(data)
            return

        # Sub-agent events: don't print result lines
        if subagent_id:
            return

        # Remove from pending tools (tool_info already fetched earlier)
        pending_tools.pop(key, None)

        # Track completed tools
        self._completed_tools.append({
            "name": name,
            "success": success,
            "summary": summary,
        })
        self._current_tool = None

        # Check if this tool was committed (parallel execution - line already printed)
        # If committed, we can't update the line so skip finalization
        if is_committed:
            return

        # Finalize the tool line with success/error indicator
        self._finalize_tool_spinner(success)

    def _render_agent_spawn_result(self, data: dict) -> None:
        """Render sub-agent spawn result with zen styling."""
        success = data.get("success", True)
        result_data = data.get("data") or {}

        # Exit sub-agent mode
        self._in_subagent_mode = False

        # Calculate duration
        duration = ""
        if self._current_tool and self._current_tool.get("start_time"):
            elapsed = time.time() - self._current_tool["start_time"]
            duration = f" [{Colors.DIM}]({elapsed:.1f}s)[/{Colors.DIM}]"

        if success:
            agent_type = result_data.get("agent_type", "Agent")
            iterations = result_data.get("iterations", 0)
            files_count = len(result_data.get("files_explored", []))

            self.console.print(
                f"    [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] {agent_type} completed{duration}"
            )
            # Show stats using our tracked tool count
            stats = []
            if iterations > 0:
                stats.append(f"{iterations} turns")
            if files_count > 0:
                stats.append(f"{files_count} files")
            if self._subagent_tool_count > 0:
                stats.append(f"{self._subagent_tool_count} tools")
            if stats:
                self.console.print(f"    [{Colors.DIM}]{DOT_BULLET} {' · '.join(stats)}[/{Colors.DIM}]")
        else:
            error = result_data.get("error", data.get("summary", "failed"))
            self.console.print(f"    [{Colors.ERROR}]{STATUS_ERROR}[/{Colors.ERROR}] Agent failed: {error}")

        self.console.print()
        self._current_tool = None
        self._subagent_tool_count = 0
        self._subagent_type = None

    def _render_subagent_start(self, data: dict) -> None:
        """Render subagent start event with animated zen styling."""
        agent_type = data.get("agent_type", "Agent")
        prompt = data.get("prompt", "")
        description = data.get("description", "")

        # Stop any existing spinner
        self._stop_spinner()

        # Truncate prompt for display
        prompt_display = prompt[:120] + "..." if len(prompt) > 120 else prompt

        self.console.print()

        # Animated header line
        header_text = header(f'{agent_type} Agent', 42)
        for i in range(0, len(header_text) + 1, 3):
            sys.stdout.write(f"\r  {ANSI.MUTED}{header_text[:i]}{ANSI.RESET}")
            sys.stdout.flush()
            time.sleep(0.004)
        sys.stdout.write("\n")
        sys.stdout.flush()

        # Agent icon based on type
        if agent_type == "Plan":
            icon = "◇"
            icon_color = Colors.WARNING
        elif agent_type == "Explore":
            icon = "◈"
            icon_color = Colors.ACCENT
        else:
            icon = "◆"
            icon_color = Colors.PRIMARY

        # Animated agent type with icon
        agent_label = f"    [{icon_color}]{icon}[/{icon_color}] [{icon_color}]{agent_type}[/{icon_color}]"
        self.console.print(agent_label)

        if description:
            self.console.print(f"    [{Colors.DIM}]{description}[/{Colors.DIM}]")

        # Animated prompt reveal
        self.console.print()
        sys.stdout.write(f"    {ANSI.PRIMARY}{ARROW_RIGHT}{ANSI.RESET} ")
        sys.stdout.flush()
        # Typewriter effect for prompt
        for char in prompt_display:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.008)
        sys.stdout.write("\n")
        sys.stdout.flush()

        self.console.print()

        # Enter subagent mode for tool tracking
        self._in_subagent_mode = True
        self._subagent_type = agent_type
        self._subagent_tool_count = 0
        self._subagent_start_time = time.time()

    def _render_subagent_end(self, data: dict) -> None:
        """Render subagent end event with animated zen styling."""
        agent_type = data.get("agent_type", "Agent")
        success = data.get("success", True)
        iterations = data.get("iterations", 0)
        files_explored = data.get("files_explored", 0)
        execution_time = data.get("execution_time", 0)

        # Exit subagent mode
        self._in_subagent_mode = False

        if success:
            # Animated completion spinner then checkmark
            completion_msg = f"{agent_type} completed"
            for i in range(6):
                spinner = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
                sys.stdout.write(f"\r    {ANSI.MUTED}{spinner}{ANSI.RESET} {completion_msg}")
                sys.stdout.flush()
                time.sleep(0.06)

            # Replace with success indicator
            sys.stdout.write(f"\r    {ANSI.SUCCESS}{STATUS_ACTIVE}{ANSI.RESET} [{Colors.SUCCESS}]{completion_msg}[/{Colors.SUCCESS}] [{Colors.DIM}]({execution_time:.1f}s)[/{Colors.DIM}]    \n")
            sys.stdout.flush()

            # Show stats with bullets
            stats = []
            if iterations > 0:
                stats.append(f"{iterations} turns")
            if files_explored > 0:
                stats.append(f"{files_explored} files")
            if self._subagent_tool_count > 0:
                stats.append(f"{self._subagent_tool_count} tools")
            if stats:
                self.console.print(f"    [{Colors.DIM}]{DOT_BULLET} {' · '.join(stats)}[/{Colors.DIM}]")
        else:
            self.console.print(f"    [{Colors.ERROR}]{STATUS_ERROR}[/{Colors.ERROR}] [{Colors.ERROR}]{agent_type} failed[/{Colors.ERROR}]")

        self.console.print()
        # Animated footer
        footer_text = footer(42)
        for i in range(0, len(footer_text) + 1, 4):
            sys.stdout.write(f"\r  {ANSI.MUTED}{footer_text[:i]}{ANSI.RESET}")
            sys.stdout.flush()
            time.sleep(0.003)
        sys.stdout.write("\n")
        sys.stdout.flush()
        self.console.print()
        self._subagent_type = None
        self._subagent_tool_count = 0

    def _format_args_summary(self, args: dict) -> str:
        """Format args into a compact summary string."""
        if not args:
            return ""

        parts = []
        for _, v in list(args.items())[:2]:
            v_str = str(v)
            if len(v_str) > 40:
                v_str = v_str[:37] + "..."
            parts.append(f"[dim]{v_str}[/dim]")

        return " ".join(parts)

    def _format_tool_args(self, tool_name: str, args: dict) -> str:
        """Format tool args in Claude Code style: ToolName(key_arg_value).

        Shows the most relevant arg for each tool type.
        """
        if not args:
            return ""

        # Tool-specific formatting for cleaner display
        if tool_name in ("glob", "grep", "semantic_search"):
            pattern = args.get("pattern", args.get("query", ""))
            if pattern:
                return f'[dim]pattern:[/dim] "{pattern}"' if len(pattern) < 50 else f'[dim]pattern:[/dim] "{pattern[:47]}..."'
        elif tool_name in ("read_file", "write_to_file", "list_files"):
            path = args.get("path", "")
            if path:
                return f"[dim]{path}[/dim]"
        elif tool_name == "bash":
            cmd = args.get("command", "")
            if cmd:
                return f"[dim]{cmd[:60]}{'...' if len(cmd) > 60 else ''}[/dim]"
        elif tool_name == "edit_file":
            path = args.get("path", "")
            if path:
                return f"[dim]{path}[/dim]"

        # Default: show first arg value
        if args:
            first_val = str(list(args.values())[0])
            if len(first_val) > 50:
                first_val = first_val[:47] + "..."
            return f"[dim]{first_val}[/dim]"

        return ""

    def _render_thinking(self, data: dict) -> None:
        """Render thinking event - show thinking content with muted styling.

        Extended thinking from models like Claude is displayed with a subtle
        style to distinguish it from regular output.
        """
        if not self.verbose:
            return

        message = data.get("message", data.get("content", ""))
        if not message:
            return

        # Store thinking for potential later display
        self._last_thinking = message

        # Stop any active spinner before printing
        self._stop_spinner()

        # Clear any active tool line
        if self._tool_line_active:
            self._finalize_tool_spinner(True)

        # Print thinking with muted style and indentation
        # Wrap to terminal width with indent
        indent = "    "  # 4 spaces for thinking
        max_width = self.console.size.width - len(indent) - 2
        lines = message.strip().split("\n")
        for line in lines:
            # Word wrap long lines
            while len(line) > max_width:
                # Find last space before max_width
                wrap_at = line.rfind(" ", 0, max_width)
                if wrap_at == -1:
                    wrap_at = max_width
                self.console.print(f"{indent}[{Colors.MUTED}]{line[:wrap_at]}[/{Colors.MUTED}]")
                line = line[wrap_at:].lstrip()
            if line:
                self.console.print(f"{indent}[{Colors.MUTED}]{line}[/{Colors.MUTED}]")

    def _render_assistant_text(self, data: dict) -> None:
        """Render intermediate assistant text - Claude Code style (update spinner)."""
        if not self.verbose:
            return

        content = data.get("content", "").strip()
        if not content:
            return

        # Claude Code style: show first line as ephemeral spinner message
        first_line = content.split("\n")[0]

        # Constrain to terminal width
        max_width = min(60, self.console.size.width - 10)
        if len(first_line) > max_width:
            first_line = first_line[:max_width - 3] + "..."

        self._show_thinking_spinner(first_line)

    def _render_progress(self, data: dict) -> None:
        """Render progress event with zen styling."""
        if not self.verbose:
            return

        message = data.get("message", "")
        percent = data.get("percent")

        if percent is not None:
            bar = progress_bar(percent, width=20)
            self.console.print(f"  [{Colors.DIM}]{NEST_LINE}[/{Colors.DIM}] [{Colors.MUTED}]{bar} {message}[/{Colors.MUTED}]")
        else:
            self.console.print(f"  [{Colors.DIM}]{NEST_LINE}[/{Colors.DIM}] [{Colors.MUTED}]{DOT_BULLET} {message}[/{Colors.MUTED}]")

    def _render_partial(self, data: dict) -> None:
        """Render partial response (streaming text)."""
        content = data.get("content", "")
        self._partial_response += content

    def _render_response(self, data: dict) -> str:
        """Render final response."""
        content = data.get("content", "")

        # Clear any ephemeral thinking line before printing response
        with self._spinner_lock:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()

        self.console.print()
        self.console.print(Markdown(content))

        return content

    def _render_clarification(self, data: dict) -> None:
        """Render clarification request with zen styling."""
        question = data.get("question", "")
        context = data.get("context", "")
        options = data.get("options", [])

        # Ensure options is a list (not a string)
        if isinstance(options, str):
            options = [options] if options else []

        # Build content
        content = Text()
        content.append(f"{question}\n", style=Colors.TEXT)

        if options and isinstance(options, list):
            content.append("\n")
            for i, opt in enumerate(options, 1):
                content.append(f"{STATUS_INACTIVE} ", style=Colors.WARNING)
                content.append(f"{i}. ", style=Colors.MUTED)
                content.append(f"{opt}\n", style=Colors.TEXT)

        # Display in a constrained panel
        self.console.print()
        panel = Panel(
            content,
            title=f"[{Colors.MUTED}]Question[/{Colors.MUTED}]",
            title_align="left",
            border_style=Colors.DIM,
            padding=(0, 2),
            width=min(70, self.console.size.width - 4),
        )
        self.console.print(panel)

        # Always store clarification (with or without options)
        # Use the corrected options list
        self._pending_clarification = {
            "question": question,
            "context": context,
            "options": options if isinstance(options, list) else [],
        }

    def _render_choice_questions(self, data: dict) -> None:
        """Render choice questions request with zen styling."""
        choices = data.get("choices", [])
        context = data.get("context", "approach")

        # Context labels
        context_labels = {
            "approach": "Implementation Approach",
            "scope": "Scope Decision",
            "requirement": "Requirement Clarification",
        }
        context_label = context_labels.get(context, "Choices")

        # Build content - show a summary of the questions
        content = Text()
        content.append(f"{len(choices)} choice(s) to make:\n\n", style=Colors.TEXT)

        for i, choice in enumerate(choices, 1):
            question = choice.get("question", "")
            options = choice.get("options", [])
            option_labels = [
                opt.get("label", opt) if isinstance(opt, dict) else opt
                for opt in options
            ]
            content.append(f"{i}. ", style=Colors.WARNING)
            content.append(f"{question}\n", style=Colors.TEXT)
            content.append(f"   Options: ", style=Colors.MUTED)
            content.append(f"{', '.join(option_labels)}\n", style=Colors.DIM)

        # Display in a constrained panel
        self.console.print()
        panel = Panel(
            content,
            title=f"[{Colors.MUTED}]{context_label}[/{Colors.MUTED}]",
            title_align="left",
            border_style=Colors.DIM,
            padding=(0, 2),
            width=min(70, self.console.size.width - 4),
        )
        self.console.print(panel)

        # Store the choice questions data
        self._pending_choice_questions = data

    def _render_plan_mode_requested(self, data: dict) -> None:
        """Render plan mode request event with zen styling."""
        reason = data.get("reason", "")

        # Store the request data for the CLI to show the menu
        self._plan_mode_requested = data

        # Build content
        content = Text()
        content.append(f"{STATUS_INFO} ", style=Colors.WARNING)
        content.append("Request to enter plan mode\n", style=Colors.TEXT)
        if reason:
            content.append(f"\n{reason}", style=Colors.DIM)

        # Display in a constrained panel
        self.console.print()
        panel = Panel(
            content,
            title=f"[{Colors.MUTED}]Plan Mode[/{Colors.MUTED}]",
            title_align="left",
            border_style=Colors.DIM,
            padding=(0, 2),
            width=min(60, self.console.size.width - 4),
        )
        self.console.print(panel)

    def _render_plan_submitted(self, data: dict) -> None:
        """Render plan submission event with zen styling."""
        plan = data.get("plan", "")

        # Store the plan data for the CLI to show the menu
        self._plan_submitted = data

        # Render plan in a constrained, professional panel
        self.console.print()
        panel = Panel(
            Markdown(plan, justify="left"),
            title=f"[{Colors.MUTED}]Plan[/{Colors.MUTED}]",
            title_align="left",
            border_style=Colors.DIM,
            padding=(0, 2),
            width=min(80, self.console.size.width - 4),
        )
        self.console.print(panel)

    def _render_error(self, data: dict) -> None:
        """Render error event with zen styling."""
        message = data.get("message", "Unknown error")
        details = data.get("details")

        self.console.print()
        self.console.print(f"  [{Colors.ERROR}]{STATUS_ERROR}[/{Colors.ERROR}] [{Colors.ERROR} bold]Error[/{Colors.ERROR} bold] {message}")

        if details:
            self.console.print(f"    [{Colors.DIM}]{details}[/{Colors.DIM}]")

    def _render_warning(self, data: dict) -> None:
        """Render warning event with zen styling."""
        message = data.get("message", "")
        self.console.print(f"  [{Colors.WARNING}]{STATUS_INFO}[/{Colors.WARNING}] {message}")

    def _render_session_end(self, data: dict) -> None:
        """Render session end event with zen styling."""
        if not self.verbose:
            return

        success = data.get("success", True)
        if not success:
            error = data.get("error", "Unknown error")
            self.console.print()
            self.console.print(f"  [{Colors.ERROR}]{STATUS_ERROR}[/{Colors.ERROR}] Session ended with error: {error}")

    def _render_context_frame(self, data: dict) -> None:
        """Store context frame data to render at end of stream."""
        # Just store the latest context frame, will render at end
        self._last_context_frame = data

    def _render_final_context_frame(self) -> None:
        """Render the final context frame at end of agent loop."""
        # Only show context frame when EMDASH_INJECT_CONTEXT_FRAME is enabled
        inject_enabled = os.getenv("EMDASH_INJECT_CONTEXT_FRAME", "").lower() in ("1", "true", "yes")
        if not inject_enabled or not self._last_context_frame:
            return

        data = self._last_context_frame
        adding = data.get("adding") or {}
        reading = data.get("reading") or {}

        # Get stats from the adding data
        step_count = adding.get("step_count", 0)
        entities_found = adding.get("entities_found", 0)
        context_tokens = adding.get("context_tokens", 0)
        context_breakdown = adding.get("context_breakdown", {})

        # Get reading stats
        item_count = reading.get("item_count", 0)

        # Only show if there's something to report
        if step_count == 0 and item_count == 0 and context_tokens == 0:
            return

        self.console.print()
        self.console.print(f"[{Colors.MUTED}]{header('Context Frame', 30)}[/{Colors.MUTED}]")

        # Show total context
        if context_tokens > 0:
            self.console.print(f"  [bold]Total: {context_tokens:,} tokens[/bold]")

        # Show breakdown
        if context_breakdown:
            breakdown_parts = []
            for key, tokens in context_breakdown.items():
                if tokens > 0:
                    breakdown_parts.append(f"{key}: {tokens:,}")
            if breakdown_parts:
                self.console.print(f"  [{Colors.DIM}]{DOT_BULLET} {' | '.join(breakdown_parts)}[/{Colors.DIM}]")

        # Show other stats
        stats = []
        if step_count > 0:
            stats.append(f"{step_count} steps")
        if entities_found > 0:
            stats.append(f"{entities_found} entities")
        if item_count > 0:
            stats.append(f"{item_count} context items")

        if stats:
            self.console.print(f"  [{Colors.DIM}]{DOT_BULLET} {' · '.join(stats)}[/{Colors.DIM}]")

        # Show reranked items (for testing)
        items = reading.get("items", [])
        if items:
            self.console.print()
            self.console.print(f"  [bold]Reranked Items ({len(items)}):[/bold]")
            for item in items[:10]:  # Show top 10
                name = item.get("name", "?")
                item_type = item.get("type", "?")
                score = item.get("score")
                file_path = item.get("file", "")
                score_str = f" [{Colors.PRIMARY}]({score:.3f})[/{Colors.PRIMARY}]" if score is not None else ""
                self.console.print(f"    [{Colors.DIM}]{item_type}[/{Colors.DIM}] [bold]{name}[/bold]{score_str}")
                if file_path:
                    self.console.print(f"      [{Colors.DIM}]{file_path}[/{Colors.DIM}]")

    # ─────────────────────────────────────────────────────────────────────────────
    # Claude Code style spinner methods
    # ─────────────────────────────────────────────────────────────────────────────

    def _format_tool_args_short(self, tool_name: str, args: dict) -> str:
        """Format tool args in short form for spinner display."""
        if not args:
            return ""

        # Tool-specific short formatting
        if tool_name == "web":
            mode = args.get("mode", "search")
            if mode == "search":
                query = args.get("query", "")
                if query:
                    return f'search: "{query[:35]}{"..." if len(query) > 35 else ""}"'
                return "search"
            elif mode == "fetch":
                url = args.get("url", "")
                if url:
                    # Show domain + path, truncated
                    return f"fetch: {url[:45]}{'...' if len(url) > 45 else ''}"
                return "fetch"
        elif tool_name in ("web_search", "WebSearch"):
            query = args.get("query", args.get("q", ""))
            if query:
                return f'"{query[:40]}{"..." if len(query) > 40 else ""}"'
        elif tool_name in ("web_fetch", "WebFetch", "fetch"):
            url = args.get("url", "")
            if url:
                return url[:50]
        elif tool_name in ("glob", "grep", "semantic_search"):
            pattern = args.get("pattern", args.get("query", ""))
            if pattern:
                return f'"{pattern[:40]}{"..." if len(pattern) > 40 else ""}"'
        elif tool_name in ("read_file", "write_to_file", "write_file", "list_files", "apply_diff", "edit"):
            path = args.get("path", args.get("file_path", ""))
            if path:
                # Show just filename or last part of path
                if "/" in path:
                    path = path.split("/")[-1]
                return path[:50]
        elif tool_name in ("bash", "execute_command"):
            cmd = args.get("command", "")
            if cmd:
                return f"{cmd[:40]}{'...' if len(cmd) > 40 else ''}"

        # Default: show first arg value (short)
        if args:
            first_val = str(list(args.values())[0])
            if len(first_val) > 40:
                first_val = first_val[:37] + "..."
            return first_val

        return ""

    def _show_thinking_spinner(self, text: str) -> None:
        """Show ephemeral thinking spinner that will be cleared (not finalized).

        Unlike _show_tool_spinner, this doesn't track the line for finalization.
        The thinking text is cleared when the next event arrives.

        Args:
            text: The thinking text to show
        """
        # Braille spinner frames
        spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        frame = spinner_frames[self._action_count % len(spinner_frames)]

        with self._spinner_lock:
            # Clear line and show spinner + text (muted style for thinking)
            sys.stdout.write(f"\r\033[K  {ANSI.MUTED}{frame} {text}{ANSI.RESET}")
            sys.stdout.flush()
            # Don't set _tool_line_active - this is ephemeral

    def _show_spinner_line(self, text: str) -> None:
        """Show a spinner line that replaces itself (for subagents).

        Args:
            text: The text to show after the spinner
        """
        # Braille spinner frames
        spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        frame = spinner_frames[self._action_count % len(spinner_frames)]

        with self._spinner_lock:
            # Clear line and show spinner + text
            sys.stdout.write(f"\r\033[K  {ANSI.MUTED}{frame}{ANSI.RESET} {text}")
            sys.stdout.flush()
            self._tool_line_active = True
            self._current_tool_line = text

    def _show_tool_spinner(self, name: str, args_summary: str) -> None:
        """Show a tool with spinner that will be finalized with result.

        Args:
            name: Tool name
            args_summary: Short args summary
        """
        # Braille spinner frames
        spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        frame = spinner_frames[self._action_count % len(spinner_frames)]

        with self._spinner_lock:
            # Two-tone: name in warm sand, args in warm gray
            if args_summary:
                line = f"  {ANSI.MUTED}{frame}{ANSI.RESET} {ANSI.SECONDARY}{name}{ANSI.RESET}{ANSI.SHADOW}({args_summary}){ANSI.RESET}"
            else:
                line = f"  {ANSI.MUTED}{frame}{ANSI.RESET} {ANSI.SECONDARY}{name}{ANSI.RESET}"
            sys.stdout.write(f"\r\033[K{line}")
            sys.stdout.flush()
            self._tool_line_active = True
            self._current_tool_name = name
            self._current_tool_args = args_summary

    def _commit_tool_line(self) -> None:
        """Commit the current tool line (print with spinner) without finalizing.

        This is used for parallel tools - when a new tool starts while another
        is still running, we commit the previous one to allow stacking.
        """
        if not self._tool_line_active:
            return

        with self._spinner_lock:
            # Braille spinner frame to show "in progress"
            spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            frame = spinner_frames[self._action_count % len(spinner_frames)]

            if self._current_tool_args:
                line = f"  {ANSI.MUTED}{frame}{ANSI.RESET} {ANSI.SECONDARY}{self._current_tool_name}{ANSI.RESET}{ANSI.SHADOW}({self._current_tool_args}){ANSI.RESET}"
            else:
                line = f"  {ANSI.MUTED}{frame}{ANSI.RESET} {ANSI.SECONDARY}{self._current_tool_name}{ANSI.RESET}"
            sys.stdout.write(f"\r\033[K{line}\n")
            sys.stdout.flush()

            # Mark this tool as committed in pending_tools
            for key, info in self._pending_tools.items():
                if info.get("name") == self._current_tool_name:
                    info["committed"] = True
                    break

            self._tool_line_active = False
            self._current_tool_name = ""
            self._current_tool_args = ""
            self._current_tool_line = ""

    def _finalize_tool_spinner(self, success: bool = True) -> None:
        """Finalize the current tool spinner line with success/error icon.

        Args:
            success: Whether the tool succeeded
        """
        if not self._tool_line_active:
            return

        with self._spinner_lock:
            # Replace spinner with result icon, keep two-tone style
            icon = f"{ANSI.SUCCESS}▸{ANSI.RESET}" if success else f"{ANSI.ERROR}▸{ANSI.RESET}"
            if self._current_tool_args:
                line = f"  {icon} {ANSI.SECONDARY}{self._current_tool_name}{ANSI.RESET}{ANSI.SHADOW}({self._current_tool_args}){ANSI.RESET}"
            else:
                line = f"  {icon} {ANSI.SECONDARY}{self._current_tool_name}{ANSI.RESET}"
            sys.stdout.write(f"\r\033[K{line}\n")
            sys.stdout.flush()
            self._tool_line_active = False
            self._current_tool_name = ""
            self._current_tool_args = ""
            self._current_tool_line = ""

    def _clear_spinner_line(self) -> None:
        """Clear the current spinner line without finalizing."""
        with self._spinner_lock:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()
            self._tool_line_active = False

    def _finalize_tool_line(self) -> None:
        """Finalize any remaining tool line at end of stream."""
        # Finalize any active tool spinner
        if self._tool_line_active:
            self._finalize_tool_spinner(success=True)

        # Don't show summary - tools are already shown individually

    # ─────────────────────────────────────────────────────────────────────────────
    # Floating todo panel methods
    # ─────────────────────────────────────────────────────────────────────────────

    def _show_floating_todos(self, todos: list) -> None:
        """Display a floating todo panel at the current position.

        The panel will be redrawn/updated when todos change.

        Args:
            todos: List of todo items with 'content', 'status', 'activeForm'
        """
        if not todos:
            return

        self._floating_todos = todos

        # Count statuses
        completed = sum(1 for t in todos if t.get("status") == "completed")
        in_progress = sum(1 for t in todos if t.get("status") == "in_progress")
        pending = sum(1 for t in todos if t.get("status") == "pending")
        total = len(todos)

        # Build the todo panel
        lines = []
        lines.append(f"{ANSI.MUTED}{EM_DASH * 3} Todo List {EM_DASH * 32}{ANSI.RESET}")

        for todo in todos:
            status = todo.get("status", "pending")
            content = todo.get("content", "")
            active_form = todo.get("activeForm", content)

            if status == "completed":
                lines.append(f"  {ANSI.SUCCESS}●{ANSI.RESET} {ANSI.MUTED}\033[9m{content}\033[0m{ANSI.RESET}")
            elif status == "in_progress":
                lines.append(f"  {ANSI.WARNING}◐{ANSI.RESET} \033[1m{active_form}...\033[0m")
            else:
                lines.append(f"  {ANSI.MUTED}○{ANSI.RESET} {content}")

        lines.append(f"{ANSI.MUTED}{EM_DASH * 45}{ANSI.RESET}")
        lines.append(f"  {ANSI.MUTED}○ {pending}{ANSI.RESET}  {ANSI.WARNING}◐ {in_progress}{ANSI.RESET}  {ANSI.SUCCESS}● {completed}{ANSI.RESET}  {ANSI.MUTED}total {total}{ANSI.RESET}")
        lines.append("")  # Empty line after

        self._todo_panel_height = len(lines)

        # Print the todo panel
        sys.stdout.write("\n")
        for line in lines:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()

    def _update_floating_todos(self, todos: list) -> None:
        """Update the floating todo panel in place.

        Args:
            todos: Updated list of todo items
        """
        if not todos:
            self._clear_floating_todos()
            return

        if self._floating_todos is None:
            # First time showing todos
            self._show_floating_todos(todos)
            return

        self._floating_todos = todos

        # Move cursor up to overwrite previous panel
        if self._todo_panel_height > 0:
            sys.stdout.write(f"\033[{self._todo_panel_height + 1}A")  # +1 for the newline before panel

        # Clear those lines
        for _ in range(self._todo_panel_height + 1):
            sys.stdout.write("\033[K\n")

        # Move back up
        sys.stdout.write(f"\033[{self._todo_panel_height + 1}A")

        # Redraw the panel
        self._show_floating_todos(todos)

    def _clear_floating_todos(self) -> None:
        """Clear the floating todo panel."""
        if self._floating_todos is None:
            return

        # Just reset the state - the panel stays as part of output
        self._floating_todos = None
        self._todo_panel_height = 0

    # ─────────────────────────────────────────────────────────────────────────────
    # Floating file changes panel methods
    # ─────────────────────────────────────────────────────────────────────────────

    def _show_floating_file_changes(self, file_changes: list) -> None:
        """Display a floating file changes panel at the current position.

        The panel will be redrawn/updated when file changes occur.

        Args:
            file_changes: List of file change items with 'path', 'status'
                         (pending/in_progress/completed)
        """
        if not file_changes:
            return

        self._floating_file_changes = file_changes

        # Count statuses
        completed = sum(1 for f in file_changes if f.get("status") == "completed")
        in_progress = sum(1 for f in file_changes if f.get("status") == "in_progress")
        pending = sum(1 for f in file_changes if f.get("status") == "pending")
        total = len(file_changes)

        # Build the file changes panel
        lines = []
        lines.append(f"{ANSI.MUTED}{EM_DASH * 3} File Changes {EM_DASH * 29}{ANSI.RESET}")

        for file_change in file_changes:
            status = file_change.get("status", "pending")
            path = file_change.get("path", "")
            # Show just the filename for display
            display_name = path.split("/")[-1] if "/" in path else path

            if status == "completed":
                lines.append(f"  {ANSI.SUCCESS}●{ANSI.RESET} {display_name}")
            elif status == "in_progress":
                lines.append(f"  {ANSI.WARNING}◐{ANSI.RESET} \033[1m{display_name}...\033[0m")
            else:
                lines.append(f"  {ANSI.MUTED}○{ANSI.RESET} {display_name}")

        lines.append(f"{ANSI.MUTED}{EM_DASH * 45}{ANSI.RESET}")
        lines.append(f"  {ANSI.SUCCESS}● {completed}{ANSI.RESET}  {ANSI.WARNING}◐ {in_progress}{ANSI.RESET}  {ANSI.MUTED}○ {pending}{ANSI.RESET}  {ANSI.MUTED}total {total}{ANSI.RESET}")
        lines.append("")  # Empty line after

        self._file_changes_panel_height = len(lines)

        # Print the file changes panel
        sys.stdout.write("\n")
        for line in lines:
            sys.stdout.write(line + "\n")
        sys.stdout.flush()

    def _update_floating_file_changes(self, file_changes: list) -> None:
        """Update the floating file changes panel in place.

        Args:
            file_changes: Updated list of file change items
        """
        if not file_changes:
            self._clear_floating_file_changes()
            return

        if self._floating_file_changes is None:
            # First time showing file changes
            self._show_floating_file_changes(file_changes)
            return

        self._floating_file_changes = file_changes

        # Move cursor up to overwrite previous panel
        if self._file_changes_panel_height > 0:
            sys.stdout.write(f"\033[{self._file_changes_panel_height + 1}A")  # +1 for the newline before panel

        # Clear those lines
        for _ in range(self._file_changes_panel_height + 1):
            sys.stdout.write("\033[K\n")

        # Move back up
        sys.stdout.write(f"\033[{self._file_changes_panel_height + 1}A")

        # Redraw the panel
        self._show_floating_file_changes(file_changes)

    def _clear_floating_file_changes(self) -> None:
        """Clear the floating file changes panel."""
        if self._floating_file_changes is None:
            return

        # Just reset the state - the panel stays as part of output
        self._floating_file_changes = None
        self._file_changes_panel_height = 0

    def _add_file_change(self, path: str, status: str = "in_progress") -> None:
        """Add or update a file in the file changes tracking.

        Args:
            path: File path being modified
            status: Status of the change (pending/in_progress/completed)
        """
        if self._floating_file_changes is None:
            self._floating_file_changes = []

        # Check if file already exists in the list
        for file_change in self._floating_file_changes:
            if file_change.get("path") == path:
                file_change["status"] = status
                self._update_floating_file_changes(self._floating_file_changes)
                return

        # Add new file
        self._floating_file_changes.append({"path": path, "status": status})
        self._update_floating_file_changes(self._floating_file_changes)

    def _render_file_change_inline(self, tool_name: str, tool_data: dict, args: dict) -> None:
        """Render file changes using the shared diff renderer.

        Args:
            tool_name: Name of the edit tool
            tool_data: Result data from the tool
            args: Arguments passed to the tool
        """
        # Extract file path and changes
        file_path = args.get("path") or args.get("file_path") or tool_data.get("path", "")
        if not file_path:
            return

        # Get diff info from tool data
        old_content = tool_data.get("old_content", "")
        new_content = tool_data.get("new_content", "")
        diff_lines = tool_data.get("diff", [])

        # Use shared renderer
        render_file_change(
            self.console,
            file_path,
            old_content=old_content,
            new_content=new_content,
            diff_lines=diff_lines,
            compact=True,
        )

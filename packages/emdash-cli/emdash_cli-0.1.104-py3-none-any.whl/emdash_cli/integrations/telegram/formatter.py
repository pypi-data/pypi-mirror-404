"""Format SSE events for Telegram messages.

Converts EmDash agent SSE events into Telegram-friendly formatted messages.
Handles markdown escaping, message length limits, and visual formatting.
"""

from dataclasses import dataclass, field
from typing import Any


# Telegram message length limit
MAX_MESSAGE_LENGTH = 4096

# Status icons for Telegram
ICON_SESSION = "🚀"
ICON_THINKING = "💭"
ICON_TOOL = "🔧"
ICON_TOOL_SUCCESS = "✅"
ICON_TOOL_ERROR = "❌"
ICON_RESPONSE = "💬"
ICON_ERROR = "⚠️"
ICON_COMPLETE = "✨"
ICON_PROGRESS = "⏳"
ICON_CLARIFICATION = "❓"


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram Markdown.

    Telegram uses a subset of Markdown. Characters that need escaping:
    _ * [ ] ( ) ~ ` > # + - = | { } . !

    Args:
        text: Raw text to escape

    Returns:
        Escaped text safe for Telegram Markdown
    """
    # Characters to escape for MarkdownV2
    # For regular Markdown mode, we only need to escape a few
    escape_chars = ["_", "*", "[", "`"]
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    return text


def truncate_text(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> str:
    """Truncate text to fit Telegram's message limit.

    Args:
        text: Text to truncate
        max_length: Maximum length (default: Telegram's 4096 limit)

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


@dataclass
class TelegramMessage:
    """A formatted message ready for Telegram."""

    text: str
    parse_mode: str | None = "Markdown"
    is_update: bool = False  # If True, update previous message instead of sending new

    def __post_init__(self):
        # Ensure text fits in Telegram's limit
        self.text = truncate_text(self.text)


@dataclass
class MessageAggregator:
    """Aggregates partial responses into complete messages.

    Handles rate limiting by batching updates and only sending
    when enough content has accumulated or time has passed.
    """

    # Current accumulated content
    content: str = ""

    # Whether we have unsent content
    dirty: bool = False

    # Message ID of the message being updated (for edit mode)
    message_id: int | None = None

    # Minimum characters before sending an update
    min_update_chars: int = 50

    # Current tool being executed (for status display)
    current_tool: str | None = None

    # Session info
    session_id: str | None = None

    # Completed tools for summary
    completed_tools: list = field(default_factory=list)

    def add_partial(self, content: str) -> bool:
        """Add partial content.

        Args:
            content: Partial response content to add

        Returns:
            True if enough content has accumulated to send an update
        """
        self.content += content
        self.dirty = True
        return len(self.content) >= self.min_update_chars

    def get_update_message(self) -> TelegramMessage | None:
        """Get the current content as an update message.

        Returns:
            TelegramMessage if there's content to send, None otherwise
        """
        if not self.content:
            return None

        self.dirty = False
        return TelegramMessage(
            text=self.content,
            is_update=self.message_id is not None,
        )

    def reset(self) -> None:
        """Reset the aggregator for a new response."""
        self.content = ""
        self.dirty = False
        self.message_id = None
        self.current_tool = None
        self.completed_tools = []


class SSEEventFormatter:
    """Formats SSE events into Telegram messages."""

    def __init__(self, show_thinking: bool = False, show_tools: bool = True, compact: bool = False):
        """Initialize the formatter.

        Args:
            show_thinking: Whether to show agent thinking/reasoning
            show_tools: Whether to show tool calls
            compact: Use compact formatting
        """
        self.show_thinking = show_thinking
        self.show_tools = show_tools
        self.compact = compact
        self.aggregator = MessageAggregator()

    def format_event(self, event_type: str, data: dict) -> TelegramMessage | None:
        """Format an SSE event into a Telegram message.

        Args:
            event_type: Type of SSE event
            data: Event data dict

        Returns:
            TelegramMessage if the event should be sent, None to skip
        """
        if event_type == "session_start":
            return self._format_session_start(data)
        elif event_type == "thinking":
            return self._format_thinking(data)
        elif event_type == "tool_start":
            return self._format_tool_start(data)
        elif event_type == "tool_result":
            return self._format_tool_result(data)
        elif event_type == "partial_response":
            return self._format_partial(data)
        elif event_type == "response":
            return self._format_response(data)
        elif event_type == "error":
            return self._format_error(data)
        elif event_type == "clarification":
            return self._format_clarification(data)
        elif event_type == "session_end":
            return self._format_session_end(data)
        elif event_type == "progress":
            return self._format_progress(data)

        return None

    def _format_session_start(self, data: dict) -> TelegramMessage:
        """Format session start event."""
        self.aggregator.reset()
        self.aggregator.session_id = data.get("session_id")

        agent = data.get("agent_name", "Agent")
        if self.compact:
            return TelegramMessage(text=f"{ICON_SESSION} *{agent}* started")
        return TelegramMessage(
            text=f"{ICON_SESSION} *{agent}* session started\n_{self.aggregator.session_id}_"
        )

    def _format_thinking(self, data: dict) -> TelegramMessage | None:
        """Format thinking event."""
        if not self.show_thinking:
            return None

        content = data.get("message", data.get("content", ""))
        if not content:
            return None

        # Truncate long thinking
        if len(content) > 200:
            content = content[:197] + "..."

        return TelegramMessage(text=f"{ICON_THINKING} _{escape_markdown(content)}_")

    def _format_tool_start(self, data: dict) -> TelegramMessage | None:
        """Format tool start event."""
        if not self.show_tools:
            return None

        name = data.get("name", "unknown")
        self.aggregator.current_tool = name

        # Skip sub-agent tool events
        if data.get("subagent_id"):
            return None

        # Format tool args summary
        args = data.get("args", {})
        summary = self._format_tool_args(name, args)

        if self.compact:
            return TelegramMessage(text=f"{ICON_TOOL} `{name}`")

        if summary:
            return TelegramMessage(text=f"{ICON_TOOL} `{name}` {summary}")
        return TelegramMessage(text=f"{ICON_TOOL} `{name}`")

    def _format_tool_result(self, data: dict) -> TelegramMessage | None:
        """Format tool result event."""
        if not self.show_tools:
            return None

        name = data.get("name", "unknown")
        success = data.get("success", True)

        # Skip sub-agent tool events
        if data.get("subagent_id"):
            return None

        # Track completed tools
        self.aggregator.completed_tools.append({"name": name, "success": success})
        self.aggregator.current_tool = None

        # In compact mode, don't show individual tool results
        if self.compact:
            return None

        icon = ICON_TOOL_SUCCESS if success else ICON_TOOL_ERROR
        return TelegramMessage(text=f"{icon} `{name}` completed")

    def _format_partial(self, data: dict) -> TelegramMessage | None:
        """Format partial response event.

        Accumulates content and returns update when threshold is reached.
        """
        content = data.get("content", "")
        if not content:
            return None

        should_update = self.aggregator.add_partial(content)
        if should_update:
            return self.aggregator.get_update_message()

        return None

    def _format_response(self, data: dict) -> TelegramMessage:
        """Format final response event."""
        content = data.get("content", "")

        # Check if we were streaming partial content (should update existing message)
        was_streaming = bool(self.aggregator.content)

        # Reset aggregator
        self.aggregator.reset()

        # Format response with icon
        if self.compact:
            return TelegramMessage(text=content, parse_mode="Markdown", is_update=was_streaming)

        return TelegramMessage(
            text=f"{ICON_RESPONSE}\n\n{content}",
            parse_mode="Markdown",
            is_update=was_streaming,
        )

    def _format_error(self, data: dict) -> TelegramMessage:
        """Format error event."""
        message = data.get("message", "Unknown error")
        details = data.get("details", "")

        text = f"{ICON_ERROR} *Error:* {escape_markdown(message)}"
        if details and not self.compact:
            text += f"\n_{escape_markdown(details)}_"

        return TelegramMessage(text=text)

    def _format_clarification(self, data: dict) -> TelegramMessage:
        """Format clarification request."""
        question = data.get("question", "")
        options = data.get("options", [])

        text = f"{ICON_CLARIFICATION} *Question:*\n{question}"

        if options and isinstance(options, list):
            text += "\n\n*Options:*"
            for i, opt in enumerate(options, 1):
                text += f"\n{i}. {opt}"

        return TelegramMessage(text=text)

    def _format_session_end(self, data: dict) -> TelegramMessage | None:
        """Format session end event."""
        success = data.get("success", True)

        if not success:
            error = data.get("error", "Unknown error")
            return TelegramMessage(text=f"{ICON_ERROR} Session ended with error: {error}")

        if self.compact:
            tools_count = len(self.aggregator.completed_tools)
            if tools_count > 0:
                return TelegramMessage(text=f"{ICON_COMPLETE} Done ({tools_count} tools)")
            return TelegramMessage(text=f"{ICON_COMPLETE} Done")

        return None

    def _format_progress(self, data: dict) -> TelegramMessage | None:
        """Format progress event."""
        if self.compact:
            return None

        message = data.get("message", "")
        percent = data.get("percent")

        if percent is not None:
            return TelegramMessage(text=f"{ICON_PROGRESS} {message} ({percent}%)")

        return TelegramMessage(text=f"{ICON_PROGRESS} {message}")

    def _format_tool_args(self, tool_name: str, args: dict) -> str:
        """Format tool args into a short summary."""
        if not args:
            return ""

        # Tool-specific formatting
        if tool_name in ("glob", "grep", "semantic_search"):
            pattern = args.get("pattern", args.get("query", ""))
            if pattern:
                if len(pattern) > 40:
                    pattern = pattern[:37] + "..."
                return f'`"{pattern}"`'

        elif tool_name in ("read_file", "write_to_file", "write_file", "edit"):
            path = args.get("path", args.get("file_path", ""))
            if path:
                # Show just filename
                if "/" in path:
                    path = path.split("/")[-1]
                return f"`{path}`"

        elif tool_name == "bash":
            cmd = args.get("command", "")
            if cmd:
                if len(cmd) > 40:
                    cmd = cmd[:37] + "..."
                return f"`{cmd}`"

        return ""

    def get_pending_content(self) -> TelegramMessage | None:
        """Get any pending accumulated content.

        Call this when the stream ends to flush remaining content.

        Returns:
            TelegramMessage with remaining content, or None
        """
        if self.aggregator.dirty and self.aggregator.content:
            return self.aggregator.get_update_message()
        return None

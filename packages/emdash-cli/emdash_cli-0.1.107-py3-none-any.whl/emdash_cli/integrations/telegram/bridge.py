"""Telegram-EmDash bridge for SSE streaming.

Connects Telegram messages to the EmDash agent and streams
SSE responses back to Telegram as message updates.
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

import httpx

from .bot import TelegramBot, TelegramMessage, TelegramUpdate
from .config import TelegramConfig, TelegramSettings, save_config
from .formatter import SSEEventFormatter, TelegramMessage as FormattedMessage


# Default EmDash server URL
DEFAULT_SERVER_URL = "http://localhost:8765"

# Telegram-only commands (not forwarded to agent)
# All other /commands are forwarded to the EmDash agent
TELEGRAM_COMMANDS = {
    "/start",      # Telegram welcome message
    "/stop",       # Cancel current operation
    "/cancel",     # Cancel pending interaction
    "/tgstatus",   # Telegram bot status
    "/tgsettings", # Telegram display settings
    "/tghelp",     # Telegram help
    "/thinking",   # Toggle thinking display
    "/tools",      # Toggle tool calls display
    "/plan",       # Switch to plan mode
    "/code",       # Switch to code mode
    "/mode",       # Show current mode
    "/reset",      # Reset session
}

# Map BotFather command format (underscores) to EmDash format (hyphens)
# BotFather doesn't allow hyphens in command names
COMMAND_ALIASES = {
    "/todo_add": "/todo-add",
    "/verify_loop": "/verify-loop",
}


@dataclass
class PendingInteraction:
    """Tracks a pending interaction requiring user response."""

    type: str  # "clarification", "plan_approval", "planmode_request"
    data: dict = field(default_factory=dict)
    options: list = field(default_factory=list)


@dataclass
class BridgeState:
    """Tracks the state of the bridge."""

    # Current session ID (one per chat)
    sessions: dict[int, str] = field(default_factory=dict)

    # Last message ID sent to each chat (for editing)
    last_message_ids: dict[int, int] = field(default_factory=dict)

    # Timestamp of last message sent to each chat (for rate limiting)
    last_message_times: dict[int, float] = field(default_factory=dict)

    # Whether we're currently processing a request for each chat
    processing: dict[int, bool] = field(default_factory=dict)

    # Pending interactions requiring user response (per chat)
    pending: dict[int, PendingInteraction] = field(default_factory=dict)

    # Current mode per chat (code or plan)
    modes: dict[int, str] = field(default_factory=dict)


class TelegramBridge:
    """Bridge between Telegram and EmDash agent.

    Receives messages from Telegram, sends them to the EmDash agent,
    and streams SSE responses back as Telegram messages.
    """

    def __init__(
        self,
        config: TelegramConfig,
        server_url: str | None = None,
        on_message: Any = None,
    ):
        """Initialize the bridge.

        Args:
            config: Telegram configuration
            server_url: EmDash server URL (default: localhost:8765)
            on_message: Optional callback for logging/debugging
        """
        self.config = config
        self.server_url = server_url or os.getenv("EMDASH_SERVER_URL", DEFAULT_SERVER_URL)
        self.on_message = on_message

        self.state = BridgeState()
        self._running = False
        self._bot: TelegramBot | None = None
        self._http_client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Start the bridge.

        Begins listening for Telegram messages and processing them.
        """
        if not self.config.bot_token:
            raise ValueError("Bot token not configured")

        self._running = True
        self._bot = TelegramBot(self.config.bot_token)
        # Timeout for SSE streaming - 5 minutes max per request
        self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=30.0))

        await self._bot.__aenter__()

        # Get bot info
        bot_info = await self._bot.get_me()
        if self.on_message:
            self.on_message("bridge_started", {"bot": bot_info.username})

        # Start polling loop
        try:
            async for update in self._bot.poll_updates(
                offset=self.config.state.last_update_id
            ):
                if not self._running:
                    break

                # Update offset and persist to disk
                self.config.state.last_update_id = update.update_id
                save_config(self.config)

                # Process the update
                await self._handle_update(update)

        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the bridge."""
        self._running = False

        if self._bot:
            await self._bot.__aexit__(None, None, None)
            self._bot = None

        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def _handle_update(self, update: TelegramUpdate) -> None:
        """Handle an incoming Telegram update.

        Args:
            update: The Telegram update to process
        """
        if not update.message or not update.message.text:
            return

        chat_id = update.message.chat.id
        text = update.message.text.strip()
        user = update.message.from_user

        # Log the incoming message
        if self.on_message:
            user_name = user.display_name if user else "Unknown"
            self.on_message("message_received", {
                "chat_id": chat_id,
                "user": user_name,
                "text": text[:100],
            })

        # Check authorization
        if not self.config.is_chat_authorized(chat_id):
            await self._send_message(chat_id, "Sorry, this chat is not authorized.")
            return

        # Check if already processing
        if self.state.processing.get(chat_id):
            await self._send_message(chat_id, "Please wait, still processing previous request...")
            return

        # Check if there's a pending interaction waiting for response
        pending = self.state.pending.get(chat_id)
        if pending:
            await self._handle_pending_response(chat_id, text, pending)
            return

        # Handle special commands
        if text.startswith("/"):
            await self._handle_command(chat_id, text)
            return

        # Process as agent message
        await self._process_agent_message(chat_id, text)

    async def _handle_command(self, chat_id: int, text: str) -> None:
        """Handle slash commands.

        Telegram-specific commands (in TELEGRAM_COMMANDS) are handled locally.
        All other slash commands are forwarded to the EmDash agent.

        Args:
            chat_id: Chat ID
            text: Command text (e.g., "/plan" or "/todo_add Fix tests")
        """
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Handle Telegram-specific commands locally
        if command in TELEGRAM_COMMANDS:
            await self._handle_telegram_command(chat_id, command, args)
            return

        # Apply command aliases (BotFather format -> EmDash format)
        if command in COMMAND_ALIASES:
            command = COMMAND_ALIASES[command]

        # Forward to agent as a slash command
        message = f"{command} {args}".strip() if args else command
        await self._process_agent_message(chat_id, message)

    async def _handle_telegram_command(self, chat_id: int, command: str, args: str) -> None:
        """Handle Telegram-specific commands.

        Args:
            chat_id: Chat ID
            command: Command name (e.g., "/start")
            args: Command arguments
        """
        if command == "/start":
            await self._send_message(
                chat_id,
                "*EmDash Bot*\n\n"
                "Send me a message and I'll process it with the EmDash agent.\n\n"
                "*Mode commands:*\n"
                "/plan - Switch to plan mode\n"
                "/code - Switch to code mode\n"
                "/mode - Show current mode\n"
                "/reset - Reset session\n\n"
                "*Telegram-only commands:*\n"
                "/stop - Cancel current operation\n"
                "/cancel - Cancel pending interaction\n"
                "/tgstatus - Show bot connection status\n"
                "/tgsettings - Show display settings\n"
                "/thinking - Toggle showing agent thinking\n"
                "/tools - Toggle showing tool calls\n"
                "/tghelp - Show this help",
            )

        elif command == "/tgstatus":
            session_id = self.state.sessions.get(chat_id)
            pending = self.state.pending.get(chat_id)
            current_mode = self.state.modes.get(chat_id, "code")
            status = "Connected" if session_id else "No active session"
            pending_status = f"\n*Pending:* {pending.type}" if pending else ""
            mode_emoji = "📋" if current_mode == "plan" else "💻"
            await self._send_message(
                chat_id,
                f"*Status:* {status}\n"
                f"*Mode:* {mode_emoji} {current_mode}\n"
                f"*Server:* `{self.server_url}`"
                f"{pending_status}",
            )

        elif command == "/stop":
            if self.state.processing.get(chat_id):
                self.state.processing[chat_id] = False
                await self._send_message(chat_id, "Operation cancelled.")
            else:
                await self._send_message(chat_id, "No operation in progress.")

        elif command == "/cancel":
            if chat_id in self.state.pending:
                del self.state.pending[chat_id]
                await self._send_message(chat_id, "Pending interaction cancelled.")
            else:
                await self._send_message(chat_id, "No pending interaction.")

        elif command == "/thinking":
            self.config.settings.show_thinking = not self.config.settings.show_thinking
            status = "enabled" if self.config.settings.show_thinking else "disabled"
            await self._send_message(chat_id, f"Show thinking {status}.")

        elif command == "/tools":
            self.config.settings.show_tool_calls = not self.config.settings.show_tool_calls
            status = "enabled" if self.config.settings.show_tool_calls else "disabled"
            await self._send_message(chat_id, f"Show tool calls {status}.")

        elif command == "/tgsettings":
            await self._send_message(
                chat_id,
                "*Telegram Display Settings:*\n\n"
                f"Show thinking: `{self.config.settings.show_thinking}`\n"
                f"Show tools: `{self.config.settings.show_tool_calls}`\n"
                f"Compact mode: `{self.config.settings.compact_mode}`\n"
                f"Update interval: `{self.config.settings.update_interval_ms}ms`",
            )

        elif command == "/tghelp":
            await self._send_message(
                chat_id,
                "*EmDash Telegram Bot*\n\n"
                "Send any message or slash command to interact with the EmDash agent.\n\n"
                "*Mode commands:*\n"
                "/plan - Switch to plan mode (read-only exploration)\n"
                "/code - Switch to code mode (execute changes)\n"
                "/mode - Show current mode\n"
                "/reset - Reset session\n\n"
                "*Agent commands (forwarded):*\n"
                "/todos - Show todo list\n"
                "/status - Show project status\n"
                "/help - Show all agent commands\n\n"
                "*Telegram-only commands:*\n"
                "/stop - Cancel current operation\n"
                "/cancel - Cancel pending interaction\n"
                "/tgstatus - Bot connection status\n"
                "/tgsettings - Display settings\n"
                "/thinking - Toggle thinking display\n"
                "/tools - Toggle tool calls display\n"
                "/tghelp - This help message\n\n"
                "*Responding to questions:*\n"
                "Reply with option number (1, 2, 3...) or type your answer.\n\n"
                "*Plan approval:*\n"
                'Reply "yes" to approve, "no" to reject, or type feedback.',
            )

        elif command == "/plan":
            # Switch to plan mode and reset session
            self.state.modes[chat_id] = "plan"
            if chat_id in self.state.sessions:
                del self.state.sessions[chat_id]
                await self._send_message(
                    chat_id,
                    "✅ Switched to *plan mode* (session reset)\n\n"
                    "_Plan mode explores the codebase and creates plans without making changes._",
                )
            else:
                await self._send_message(
                    chat_id,
                    "✅ Switched to *plan mode*\n\n"
                    "_Plan mode explores the codebase and creates plans without making changes._",
                )

        elif command == "/code":
            # Switch to code mode and reset session
            self.state.modes[chat_id] = "code"
            if chat_id in self.state.sessions:
                del self.state.sessions[chat_id]
                await self._send_message(
                    chat_id,
                    "✅ Switched to *code mode* (session reset)\n\n"
                    "_Code mode can execute changes and modify files._",
                )
            else:
                await self._send_message(
                    chat_id,
                    "✅ Switched to *code mode*\n\n"
                    "_Code mode can execute changes and modify files._",
                )

        elif command == "/mode":
            current_mode = self.state.modes.get(chat_id, "code")
            if current_mode == "plan":
                await self._send_message(
                    chat_id,
                    "📋 Current mode: *plan*\n\n"
                    "_Use /code to switch to code mode._",
                )
            else:
                await self._send_message(
                    chat_id,
                    "💻 Current mode: *code*\n\n"
                    "_Use /plan to switch to plan mode._",
                )

        elif command == "/reset":
            # Reset session for this chat
            if chat_id in self.state.sessions:
                del self.state.sessions[chat_id]
            await self._send_message(chat_id, "🔄 Session reset.")

    async def _process_agent_message(self, chat_id: int, message: str) -> None:
        """Process a message through the EmDash agent.

        Args:
            chat_id: Telegram chat ID
            message: User message to process
        """
        self.state.processing[chat_id] = True

        # Get or create session
        session_id = self.state.sessions.get(chat_id)

        # Create formatter with settings
        formatter = SSEEventFormatter(
            show_thinking=self.config.settings.show_thinking,
            show_tools=self.config.settings.show_tool_calls,
            compact=self.config.settings.compact_mode,
        )

        # Send typing indicator
        if self._bot:
            try:
                await self._bot.send_chat_action(chat_id, "typing")
            except Exception:
                pass

        try:
            # Stream from agent
            last_update_time = 0.0
            update_interval = self.config.settings.update_interval_ms / 1000.0
            has_sent_response = False

            # Get current mode for this chat (default to code)
            current_mode = self.state.modes.get(chat_id, "code")

            async for event_type, data in self._stream_agent_chat(message, session_id, current_mode):
                # Check if cancelled
                if not self.state.processing.get(chat_id):
                    break

                # Update session ID if provided (don't send session_start as separate message)
                if event_type == "session_start" and data.get("session_id"):
                    self.state.sessions[chat_id] = data["session_id"]
                    continue  # Skip sending session_start notification

                # Skip session_end notifications (clutters the chat)
                if event_type == "session_end":
                    continue

                # Handle interactive events - store pending state
                if event_type == "clarification":
                    await self._handle_clarification_event(chat_id, data)
                    continue

                if event_type == "plan_submitted":
                    await self._handle_plan_submitted_event(chat_id, data)
                    continue

                if event_type == "plan_mode_requested":
                    await self._handle_plan_mode_event(chat_id, data)
                    continue

                # Format the event
                formatted = formatter.format_event(event_type, data)

                # Track if we've sent a response (to avoid duplicates)
                if event_type == "response":
                    has_sent_response = True

                # Send formatted message
                if formatted:
                    now = time.time()

                    # Rate limit updates
                    if formatted.is_update and (now - last_update_time) < update_interval:
                        continue

                    last_update_time = now

                    # Edit or send new message
                    if formatted.is_update and chat_id in self.state.last_message_ids:
                        await self._edit_message(
                            chat_id,
                            self.state.last_message_ids[chat_id],
                            formatted.text,
                            formatted.parse_mode,
                        )
                    else:
                        msg = await self._send_message(
                            chat_id, formatted.text, formatted.parse_mode
                        )
                        if msg:
                            self.state.last_message_ids[chat_id] = msg.message_id

            # Flush any pending partial content (only if we haven't sent a full response)
            if not has_sent_response:
                pending_content = formatter.get_pending_content()
                if pending_content:
                    await self._send_message(chat_id, pending_content.text, pending_content.parse_mode)

        except Exception as e:
            if self.on_message:
                self.on_message("error", {"error": str(e)})
            await self._send_message(chat_id, f"Error: {str(e)}")

        finally:
            self.state.processing[chat_id] = False

    async def _stream_agent_chat(
        self,
        message: str,
        session_id: str | None = None,
        mode: str = "code",
    ) -> AsyncIterator[tuple[str, dict]]:
        """Stream agent chat response via SSE.

        Args:
            message: User message
            session_id: Optional session ID for continuity
            mode: Agent mode (code or plan)

        Yields:
            Tuples of (event_type, data)
        """
        if not self._http_client:
            return

        payload = {
            "message": message,
            "options": {
                "max_iterations": 50,
                "verbose": True,
                "mode": mode,
            },
        }

        if session_id:
            payload["session_id"] = session_id

        url = f"{self.server_url}/api/agent/chat"

        try:
            async with self._http_client.stream("POST", url, json=payload) as response:
                response.raise_for_status()

                current_event = None

                async for line in response.aiter_lines():
                    line = line.strip()

                    if line.startswith("event: "):
                        current_event = line[7:]
                    elif line.startswith("data: "):
                        if current_event:
                            try:
                                data = json.loads(line[6:])
                                if data is None:
                                    data = {}
                                yield current_event, data
                            except json.JSONDecodeError:
                                pass
                    elif line == ": ping":
                        # Keep-alive ping
                        pass

        except httpx.HTTPError as e:
            yield "error", {"message": f"HTTP error: {str(e)}"}
        except Exception as e:
            yield "error", {"message": str(e)}

    async def _send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str | None = "Markdown",
    ) -> TelegramMessage | None:
        """Send a message to a chat.

        Args:
            chat_id: Target chat ID
            text: Message text
            parse_mode: Parse mode for formatting

        Returns:
            Sent message, or None on error
        """
        if not self._bot:
            return None

        try:
            return await self._bot.send_message(
                chat_id, text, parse_mode=parse_mode
            )
        except Exception as e:
            # Try sending without parse mode if Markdown fails
            if parse_mode:
                try:
                    return await self._bot.send_message(
                        chat_id, text, parse_mode=None
                    )
                except Exception:
                    pass

            if self.on_message:
                self.on_message("send_error", {"error": str(e)})
            return None

    async def _edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str | None = "Markdown",
    ) -> None:
        """Edit an existing message.

        Args:
            chat_id: Chat containing the message
            message_id: Message ID to edit
            text: New text
            parse_mode: Parse mode for formatting
        """
        if not self._bot:
            return

        try:
            await self._bot.edit_message_text(
                chat_id, message_id, text, parse_mode=parse_mode
            )
        except Exception:
            # Editing can fail if message is identical - ignore
            pass

    async def _send_long_message(self, chat_id: int, text: str) -> None:
        """Send a long message, splitting if necessary.

        Args:
            chat_id: Target chat ID
            text: Message text (can be longer than 4096 chars)
        """
        max_len = self.config.settings.max_message_length

        # If short enough, send as-is
        if len(text) <= max_len:
            await self._send_message(chat_id, text)
            return

        # Split into chunks at paragraph boundaries
        chunks = []
        current_chunk = ""

        paragraphs = text.split("\n\n")
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_len:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # If paragraph itself is too long, split it
                if len(para) > max_len:
                    words = para.split()
                    current_chunk = ""
                    for word in words:
                        if len(current_chunk) + len(word) + 1 <= max_len:
                            if current_chunk:
                                current_chunk += " "
                            current_chunk += word
                        else:
                            chunks.append(current_chunk)
                            current_chunk = word
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        # Send each chunk
        for i, chunk in enumerate(chunks):
            if len(chunks) > 1:
                chunk = f"*({i + 1}/{len(chunks)})*\n\n{chunk}"
            await self._send_message(chat_id, chunk)
            # Small delay between chunks to avoid rate limits
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)

    # ─────────────────────────────────────────────────────────────────────────────
    # Interactive event handlers
    # ─────────────────────────────────────────────────────────────────────────────

    async def _handle_clarification_event(self, chat_id: int, data: dict) -> None:
        """Handle clarification event - prompt user for response.

        Args:
            chat_id: Telegram chat ID
            data: Clarification event data
        """
        question = data.get("question", "")
        options = data.get("options", [])
        context = data.get("context", "")

        # Ensure options is a list
        if isinstance(options, str):
            options = [options] if options else []

        # Store pending interaction
        self.state.pending[chat_id] = PendingInteraction(
            type="clarification",
            data=data,
            options=options,
        )

        # Build message
        text = f"❓ *Question:*\n{question}"

        if options:
            text += "\n\n*Options:*"
            for i, opt in enumerate(options, 1):
                text += f"\n{i}. {opt}"
            text += "\n\n_Reply with option number (1-{}) or type your answer_".format(len(options))
        else:
            text += "\n\n_Type your answer_"

        await self._send_message(chat_id, text)

    async def _handle_plan_submitted_event(self, chat_id: int, data: dict) -> None:
        """Handle plan submitted event - prompt user for approval.

        Args:
            chat_id: Telegram chat ID
            data: Plan submitted event data
        """
        plan = data.get("plan", "")

        # Store pending interaction
        self.state.pending[chat_id] = PendingInteraction(
            type="plan_approval",
            data=data,
        )

        # Build message
        text = f"📋 *Plan Submitted:*\n\n{plan}"
        text += "\n\n_Reply:_"
        text += '\n• "approve" or "yes" to proceed'
        text += '\n• "reject" or "no" to cancel'
        text += "\n• Or type feedback to request changes"

        await self._send_long_message(chat_id, text)

    async def _handle_plan_mode_event(self, chat_id: int, data: dict) -> None:
        """Handle plan mode request event - prompt user for approval.

        Args:
            chat_id: Telegram chat ID
            data: Plan mode request event data
        """
        reason = data.get("reason", "")

        # Store pending interaction
        self.state.pending[chat_id] = PendingInteraction(
            type="planmode_request",
            data=data,
        )

        # Build message
        text = "🗺️ *Plan Mode Requested*"
        if reason:
            text += f"\n\n{reason}"
        text += "\n\n_Reply:_"
        text += '\n• "approve" or "yes" to enter plan mode'
        text += '\n• "reject" or "no" to continue without plan'

        await self._send_message(chat_id, text)

    async def _handle_pending_response(
        self, chat_id: int, text: str, pending: PendingInteraction
    ) -> None:
        """Handle user response to a pending interaction.

        Args:
            chat_id: Telegram chat ID
            text: User's response text
            pending: The pending interaction
        """
        # Clear pending state
        del self.state.pending[chat_id]

        if pending.type == "clarification":
            await self._process_clarification_answer(chat_id, text, pending)
        elif pending.type == "plan_approval":
            await self._process_plan_approval(chat_id, text, pending)
        elif pending.type == "planmode_request":
            await self._process_planmode_approval(chat_id, text, pending)

    async def _process_clarification_answer(
        self, chat_id: int, text: str, pending: PendingInteraction
    ) -> None:
        """Process clarification answer and continue agent.

        Args:
            chat_id: Telegram chat ID
            text: User's answer
            pending: The pending clarification
        """
        session_id = self.state.sessions.get(chat_id)
        if not session_id:
            await self._send_message(chat_id, "Error: No active session")
            return

        # Check if user replied with option number
        answer = text.strip()
        if pending.options and answer.isdigit():
            idx = int(answer) - 1
            if 0 <= idx < len(pending.options):
                answer = pending.options[idx]

        await self._send_message(chat_id, f"✅ Selected: {answer}\nContinuing...")

        # Call continuation endpoint and stream response
        await self._stream_continuation(
            chat_id,
            f"{self.server_url}/api/agent/chat/{session_id}/clarification/answer",
            params={"answer": answer},
        )

    async def _process_plan_approval(
        self, chat_id: int, text: str, pending: PendingInteraction
    ) -> None:
        """Process plan approval/rejection and continue agent.

        Args:
            chat_id: Telegram chat ID
            text: User's response
            pending: The pending plan approval
        """
        session_id = self.state.sessions.get(chat_id)
        if not session_id:
            await self._send_message(chat_id, "Error: No active session")
            return

        response = text.strip().lower()

        if response in ("approve", "yes", "y", "ok", "proceed"):
            await self._send_message(chat_id, "✅ Plan approved. Executing...")
            await self._stream_continuation(
                chat_id,
                f"{self.server_url}/api/agent/chat/{session_id}/plan/approve",
            )
        elif response in ("reject", "no", "n", "cancel"):
            await self._send_message(chat_id, "❌ Plan rejected.")
            await self._stream_continuation(
                chat_id,
                f"{self.server_url}/api/agent/chat/{session_id}/plan/reject",
                params={"feedback": ""},
            )
        else:
            # Treat as feedback
            await self._send_message(chat_id, f"📝 Feedback sent: {text[:50]}...")
            await self._stream_continuation(
                chat_id,
                f"{self.server_url}/api/agent/chat/{session_id}/plan/reject",
                params={"feedback": text},
            )

    async def _process_planmode_approval(
        self, chat_id: int, text: str, pending: PendingInteraction
    ) -> None:
        """Process plan mode approval/rejection and continue agent.

        Args:
            chat_id: Telegram chat ID
            text: User's response
            pending: The pending plan mode request
        """
        session_id = self.state.sessions.get(chat_id)
        if not session_id:
            await self._send_message(chat_id, "Error: No active session")
            return

        response = text.strip().lower()

        if response in ("approve", "yes", "y", "ok"):
            await self._send_message(chat_id, "✅ Entering plan mode...")
            await self._stream_continuation(
                chat_id,
                f"{self.server_url}/api/agent/chat/{session_id}/planmode/approve",
            )
        else:
            await self._send_message(chat_id, "Continuing without plan mode...")
            await self._stream_continuation(
                chat_id,
                f"{self.server_url}/api/agent/chat/{session_id}/planmode/reject",
                params={"feedback": text if response not in ("reject", "no", "n") else ""},
            )

    async def _stream_continuation(
        self,
        chat_id: int,
        url: str,
        params: dict | None = None,
    ) -> None:
        """Stream a continuation endpoint response.

        Args:
            chat_id: Telegram chat ID
            url: API endpoint URL
            params: Optional query parameters
        """
        if not self._http_client:
            return

        self.state.processing[chat_id] = True

        # Create formatter with settings
        formatter = SSEEventFormatter(
            show_thinking=self.config.settings.show_thinking,
            show_tools=self.config.settings.show_tool_calls,
            compact=self.config.settings.compact_mode,
        )

        try:
            response_content = ""
            last_update_time = 0.0
            update_interval = self.config.settings.update_interval_ms / 1000.0

            async with self._http_client.stream("POST", url, params=params) as response:
                response.raise_for_status()

                current_event = None

                async for line in response.aiter_lines():
                    # Check if cancelled
                    if not self.state.processing.get(chat_id):
                        break

                    line = line.strip()

                    if line.startswith("event: "):
                        current_event = line[7:]
                    elif line.startswith("data: "):
                        if current_event:
                            try:
                                data = json.loads(line[6:])
                                if data is None:
                                    data = {}

                                # Handle interactive events recursively
                                if current_event == "clarification":
                                    await self._handle_clarification_event(chat_id, data)
                                    continue
                                if current_event == "plan_submitted":
                                    await self._handle_plan_submitted_event(chat_id, data)
                                    continue
                                if current_event == "plan_mode_requested":
                                    await self._handle_plan_mode_event(chat_id, data)
                                    continue

                                # Format the event
                                formatted = formatter.format_event(current_event, data)

                                if current_event == "response":
                                    response_content = data.get("content", "")

                                if formatted:
                                    now = time.time()
                                    if formatted.is_update and (now - last_update_time) < update_interval:
                                        continue
                                    last_update_time = now

                                    msg = await self._send_message(
                                        chat_id, formatted.text, formatted.parse_mode
                                    )
                                    if msg:
                                        self.state.last_message_ids[chat_id] = msg.message_id

                            except json.JSONDecodeError:
                                pass

            # Send final response if we have one
            if response_content and chat_id not in self.state.pending:
                await self._send_long_message(chat_id, response_content)

        except Exception as e:
            if self.on_message:
                self.on_message("error", {"error": str(e)})
            await self._send_message(chat_id, f"Error: {str(e)}")

        finally:
            self.state.processing[chat_id] = False

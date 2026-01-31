"""Event decorators for message processing in solo and shared modes.

This module implements the decorator pattern for handling messages:
- StandardDecorator: Solo mode - direct passthrough to TUI
- SharedDecorator: Multiuser mode - all events flow through server via SSE
"""

from typing import AsyncIterator, Callable, Optional, Protocol, runtime_checkable

import httpx


def _build_agent_prompt(content: str, chat_context: list[dict]) -> str:
    """Build an agent prompt that includes recent chat history.

    When chat_context is empty the raw content is returned unchanged,
    so solo / non-chat invocations are unaffected.
    """
    if not chat_context:
        return content

    lines = []
    for msg in chat_context:
        name = msg.get("display_name", msg.get("user_id", "User"))
        lines.append(f"  {name}: {msg['content']}")
    context_block = "\n".join(lines)

    return (
        f"[Team chat context — recent messages from the conversation]\n"
        f"{context_block}\n\n"
        f"[Request]\n{content}"
    )


@runtime_checkable
class EventDecorator(Protocol):
    """Protocol for message processing decorators."""

    def process_message(
        self, content: str, images: Optional[list[dict]] = None
    ) -> AsyncIterator[dict]:
        """Process a message and yield events.

        Args:
            content: The message content to process
            images: Optional list of images [{"data": base64_str, "format": "png"}]

        Yields:
            Event dicts with type and data keys
        """
        ...

    async def broadcast_event(self, event_type: str, event_data: dict) -> None:
        """Broadcast an event to participants (no-op in standard mode).

        Args:
            event_type: Type of event (e.g., tool_start, response)
            event_data: Event data payload
        """
        ...


class StandardDecorator(EventDecorator):
    """Solo mode decorator - direct passthrough to TUI.

    In solo mode, events are processed locally and yielded directly
    to the TUI for display. No network calls to multiuser endpoints.
    """

    def __init__(
        self,
        handler: Callable[[str, Optional[list[dict]]], AsyncIterator[dict]],
    ):
        """Initialize with the agent handler.

        Args:
            handler: Async callable that processes messages and yields events.
                     Signature: (content: str, images: list | None) -> AsyncIterator[dict]
        """
        self.handler = handler

    async def process_message(
        self, content: str, images: Optional[list[dict]] = None
    ) -> AsyncIterator[dict]:
        """Process message and yield events directly.

        Args:
            content: The message content to process
            images: Optional list of images [{"data": base64_str, "format": "png"}]

        Yields:
            Event dicts from the underlying handler
        """
        async for event in self.handler(content, images):
            yield event

    async def broadcast_event(self, event_type: str, event_data: dict) -> None:
        """No-op in standard mode - events are local only."""
        pass


class SharedDecorator(EventDecorator):
    """Multiuser mode decorator - all events via server SSE.

    In shared mode, messages are sent to the server which broadcasts
    them to all participants. Events come back via SSE, providing a
    single source of truth for all users (including the sender).
    """

    def __init__(
        self,
        session_id: str,
        user_id: str,
        server_url: str,
        handler: Callable[[str, Optional[list[dict]]], AsyncIterator[dict]],
        is_owner: bool = False,
    ):
        """Initialize the shared decorator.

        Args:
            session_id: The shared session ID
            user_id: This user's ID
            server_url: API base URL
            handler: The underlying agent handler (for owner to process agent requests).
                     Signature: (content: str, images: list | None) -> AsyncIterator[dict]
            is_owner: Whether this user is the session owner
        """
        self.session_id = session_id
        self.user_id = user_id
        self.server_url = server_url
        self.handler = handler
        self.is_owner = is_owner
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def process_message(
        self, content: str, images: Optional[list[dict]] = None
    ) -> AsyncIterator[dict]:
        """Send message to server - events come via SSE.

        For joiners: POST to conversation endpoint, no local yield.
        For owners: POST to conversation endpoint, then process through agent
                    and broadcast each event.

        Slash commands (like /leave, /who) are processed locally through the
        handler, not sent to the server as chat messages.

        Args:
            content: The message content to process
            images: Optional list of images [{"data": base64_str, "format": "png"}]

        Yields:
            Nothing for joiners (events come via SSE).
            For owners processing agent requests: yields events locally
            while also broadcasting them.
            For slash commands: yields events from handler directly.
        """
        import re

        # Slash commands are processed locally through the handler
        # These include /leave, /who, /invite, /share, /join, etc.
        if content.strip().startswith('/'):
            async for event in self.handler(content, images):
                yield event
            return

        # Check if this triggers the agent
        message_lower = content.lower()
        triggers_agent = "@agent" in message_lower or "@emdash" in message_lower

        # Strip @agent/@emdash from the message for agent processing
        agent_message = content
        if triggers_agent:
            agent_message = re.sub(r'@agent|@emdash', '', content, flags=re.IGNORECASE).strip()
            if not agent_message:
                agent_message = content

        client = await self._get_client()

        # POST to unified conversation endpoint
        chat_context: list[dict] = []
        try:
            resp = await client.post(
                f"{self.server_url}/api/multiuser/conversation/{self.session_id}/message",
                json={
                    "user_id": self.user_id,
                    "content": content,
                    "trigger_agent": triggers_agent,
                },
            )
            if resp.status_code == 200:
                body = resp.json()
                chat_context = body.get("chat_context", [])
        except Exception as e:
            # If the POST fails, yield an error event locally
            yield {"type": "error", "data": {"message": f"Failed to send message: {e}"}}
            return

        # If this user is the owner and the message triggers the agent,
        # process through the handler and broadcast each event
        if self.is_owner and triggers_agent:
            # Process and broadcast - no local yield, events come via SSE
            await self._process_and_broadcast(agent_message, chat_context, images)

        # For everyone (including owner), events come via SSE
        # Clear processing state since we're not handling locally
        yield {"type": "set_processing", "data": {"processing": False}}

    async def _process_and_broadcast(
        self,
        content: str,
        chat_context: list[dict] | None = None,
        images: list[dict] | None = None,
    ) -> None:
        """Process a message through the agent and broadcast all events.

        This is used by the owner to handle agent requests. Each event
        from the agent is broadcast to all participants via SSE.

        IMPORTANT: In shared mode, we do NOT yield locally. All events
        come back via SSE as the single source of truth. This prevents
        duplicate events on the owner's TUI.

        Args:
            content: The message content (with @agent stripped)
            chat_context: Recent human chat messages for agent context
            images: Optional list of images [{"data": base64_str, "format": "png"}]
        """
        import logging
        log = logging.getLogger(__name__)

        # Events to broadcast to all participants
        broadcast_event_types = {
            "tool_start", "tool_result", "thinking", "chat_chunk",
            "chat_complete", "progress", "subagent_start", "subagent_end",
            "response", "partial_response", "error", "set_processing",
            # Interactive events — broadcast so all participants see the
            # question/approval prompt.  Non-owners render them read-only;
            # the owner answers and broadcasts prompt_resolved to clear them.
            "ask_choice_questions", "clarification_request",
            "plan_mode_requested", "plan_submitted",
        }

        # Build prompt with chat context so the agent sees the
        # human discussion that led to this @agent invocation.
        prompt = _build_agent_prompt(content, chat_context or [])

        log.info(f"[SHARED-DECORATOR] _process_and_broadcast starting for: {content[:50]}...")

        # Signal all participants that the agent is processing
        await self.broadcast_event("set_processing", {"processing": True})
        await self.broadcast_event("agent_typing", {"is_typing": True})

        try:
            async for event in self.handler(prompt, images):
                event_type = event.get("type", "")
                event_data = event.get("data", {})

                log.info(f"[SHARED-DECORATOR] Handler yielded event: {event_type}")

                # Broadcast relevant events to all participants via SSE
                # Owner will receive them via SSE like everyone else
                if event_type in broadcast_event_types:
                    log.info(f"[SHARED-DECORATOR] Broadcasting: {event_type}")
                    await self.broadcast_event(event_type, event_data)
                else:
                    log.info(f"[SHARED-DECORATOR] Skipping (not in broadcast types): {event_type}")

                # Do NOT yield locally - events come via SSE for everyone
                # (This is the "single source of truth" principle)

        except Exception as e:
            log.error(f"[SHARED-DECORATOR] Error in _process_and_broadcast: {e}")
            await self.broadcast_event("error", {"message": str(e)})

        # Signal all participants that the agent finished
        await self.broadcast_event("agent_typing", {"is_typing": False})
        await self.broadcast_event("set_processing", {"processing": False})

        log.info(f"[SHARED-DECORATOR] _process_and_broadcast finished")

    async def broadcast_event(self, event_type: str, event_data: dict) -> None:
        """Broadcast an event to all session participants.

        Args:
            event_type: Type of event
            event_data: Event data payload
        """
        try:
            client = await self._get_client()
            await client.post(
                f"{self.server_url}/api/multiuser/session/{self.session_id}/broadcast_event",
                json={
                    "user_id": self.user_id,
                    "event_type": event_type,
                    "data": event_data,
                },
            )
        except Exception:
            # Don't block on broadcast failures
            pass

    async def process_agent_request(
        self,
        content: str,
        display_name: str,
        chat_context: list[dict] | None = None,
    ) -> AsyncIterator[dict]:
        """Process an agent request from another user (owner only).

        This is called when the owner receives a process_message_request
        via SSE from another participant.

        In shared mode, we do NOT yield events locally. All events are
        broadcast via SSE and everyone (including owner) receives them
        from SSE as the single source of truth.

        Args:
            content: The message content (already stripped of @agent)
            display_name: Display name of the user who sent the request
            chat_context: Recent human chat messages for agent context

        Yields:
            Only a processing indicator - actual events come via SSE
        """
        # Unused but kept for interface compatibility
        _ = display_name

        # Process and broadcast - no local yield, events come via SSE
        await self._process_and_broadcast(content, chat_context)

        # Signal processing complete - the actual events will come via SSE
        yield {"type": "set_processing", "data": {"processing": False}}

"""SSE listener for multiuser shared session events.

This module provides a background listener that receives real-time
events from a shared session via Server-Sent Events (SSE).
"""

import asyncio
import json
import threading
from typing import Callable, Optional

import httpx
from rich.console import Console
from rich.panel import Panel

console = Console()


class SharedSessionListener:
    """Listens to SSE events from a shared session.

    This listener runs in a background thread and processes events
    such as participant joins/leaves, agent responses, and tool calls.
    """

    def __init__(
        self,
        base_url: str,
        session_id: str,
        user_id: str,
        on_event: Optional[Callable[[dict], None]] = None,
        on_process_message: Optional[Callable[[dict], None]] = None,
        is_owner: bool = False,
    ):
        """Initialize the SSE listener.

        Args:
            base_url: API base URL (e.g., http://localhost:8000)
            session_id: The shared session ID to listen to
            user_id: This user's ID (to filter out own events)
            on_event: Optional callback for custom event handling
            on_process_message: Callback for owner to process messages from other users
            is_owner: Whether this user is the session owner
        """
        self.base_url = base_url
        self.session_id = session_id
        self.user_id = user_id
        self.on_event = on_event or self._default_handler
        self.on_process_message = on_process_message
        self.is_owner = is_owner
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start listening for events in a background thread."""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._listen_sync, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop listening for events."""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _listen_sync(self) -> None:
        """Synchronous listen loop that runs in background thread."""
        url = f"{self.base_url}/api/multiuser/session/{self.session_id}/stream"
        params = {"user_id": self.user_id}

        console.print(f"[dim]SSE connecting to {url} as user {self.user_id[:8]}...[/dim]")

        while self._running and not self._stop_event.is_set():
            try:
                with httpx.Client(timeout=None) as client:
                    with client.stream("GET", url, params=params) as response:
                        if response.status_code != 200:
                            console.print(f"[red]SSE connection failed: {response.status_code}[/red]")
                            # Try to read error body
                            try:
                                error_text = response.text[:200]
                                console.print(f"[dim]  Error: {error_text}[/dim]")
                            except Exception:
                                pass
                            self._stop_event.wait(5.0)  # Backoff
                            continue

                        console.print(f"[green]SSE connected! is_owner={self.is_owner}[/green]")
                        current_event_type = None
                        for line in response.iter_lines():
                            if self._stop_event.is_set():
                                break

                            # Parse SSE format: event: {type}\ndata: {json}\n\n
                            if line.startswith("event:"):
                                current_event_type = line[6:].strip()
                            elif line.startswith("data:"):
                                data = line[5:].strip()
                                if data and data != "[DONE]":
                                    self._handle_event(data, current_event_type)
                                current_event_type = None  # Reset for next event

            except httpx.ReadTimeout:
                # Normal timeout, reconnect
                continue
            except httpx.ConnectError as e:
                console.print(f"[dim]SSE connection error, retrying...[/dim]")
                self._stop_event.wait(2.0)  # Backoff before reconnect
            except Exception as e:
                if self._running:
                    console.print(f"[dim]SSE error: {e}[/dim]")
                    self._stop_event.wait(2.0)

    def _handle_event(self, data: str, event_type: str | None = None) -> None:
        """Parse and handle an SSE event."""
        try:
            payload = json.loads(data)
            # Restructure to expected format: {type, data, source_user_id}
            event = {
                "type": event_type or payload.get("type", "unknown"),
                "data": payload,
                "source_user_id": payload.get("_source_user_id", ""),
            }

            # Skip user_message events from ourselves - we already see our own input locally
            if event["type"] == "user_message" and event["source_user_id"] == self.user_id:
                return

            # Debug: show received events (excluding our own user_message)
            console.print(f"[dim]SSE event: {event['type']} (source={event['source_user_id'][:8] if event['source_user_id'] else 'none'})[/dim]")
            self.on_event(event)
        except json.JSONDecodeError as e:
            console.print(f"[dim]SSE JSON error: {e}[/dim]")
            pass  # Ignore malformed events

    def _default_handler(self, event: dict) -> None:
        """Default event handler - renders events to console."""
        event_type = event.get("type", "unknown")
        data = event.get("data", {})
        source_user = event.get("source_user_id", "")

        # Debug: show received events
        # console.print(f"[dim]SSE event: {event_type} from {source_user}[/dim]")

        # Skip events from ourselves (we see them locally)
        if source_user == self.user_id:
            return

        if event_type == "participant_joined":
            name = data.get("display_name", "Someone")
            console.print(f"\n[green]+ {name} joined the session[/green]")

        elif event_type == "participant_left":
            name = data.get("display_name", "Someone")
            console.print(f"\n[yellow]- {name} left the session[/yellow]")

        elif event_type == "user_message":
            # Another user sent a message
            name = data.get("display_name", "User")
            content = data.get("content", "")
            console.print(f"\n[bold]{name}:[/bold] {content}")

        elif event_type in ("response", "assistant_text"):
            # Agent response text
            text = data.get("text", "")
            if text:
                console.print(text, end="", highlight=False)

        elif event_type == "partial_response":
            # Streaming response chunk
            text = data.get("text", "")
            if text:
                console.print(text, end="", highlight=False)

        elif event_type == "tool_start":
            tool = data.get("tool", "unknown")
            console.print(f"\n[dim]Using tool: {tool}[/dim]")

        elif event_type == "tool_result":
            # Tool results can be verbose, show summary
            tool = data.get("tool", "unknown")
            success = data.get("success", True)
            if not success:
                console.print(f"[red]Tool {tool} failed[/red]")

        elif event_type == "thinking":
            # Agent thinking indicator
            text = data.get("text", "")
            if text:
                console.print(f"[dim italic]{text}[/dim italic]")

        elif event_type == "progress":
            # Progress update
            message = data.get("message", "")
            if message:
                console.print(f"[dim]{message}[/dim]")

        elif event_type == "error":
            message = data.get("message", "Unknown error")
            console.print(f"\n[red]Error: {message}[/red]")

        elif event_type == "warning":
            message = data.get("message", "")
            if message:
                console.print(f"\n[yellow]Warning: {message}[/yellow]")

        elif event_type == "subagent_start":
            # Sub-agent started
            agent_name = data.get("agent_name", "sub-agent")
            task = data.get("task", "")
            console.print(f"\n[dim]Starting {agent_name}...[/dim]")
            if task:
                console.print(f"[dim]  Task: {task[:50]}{'...' if len(task) > 50 else ''}[/dim]")

        elif event_type == "subagent_end":
            # Sub-agent completed
            agent_name = data.get("agent_name", "sub-agent")
            console.print(f"[dim]{agent_name} completed[/dim]")

        elif event_type == "clarification":
            # Agent is asking for clarification
            question = data.get("question", "")
            options = data.get("options", [])
            if question:
                console.print(f"\n[bold cyan]Clarification needed:[/bold cyan] {question}")
                for i, opt in enumerate(options, 1):
                    label = opt.get("label", opt) if isinstance(opt, dict) else opt
                    console.print(f"  {i}. {label}")

        elif event_type == "clarification_response":
            # User responded to clarification
            response = data.get("response", "")
            console.print(f"[dim]Selected: {response}[/dim]")

        elif event_type == "choice_questions":
            # Agent is presenting choice questions
            questions = data.get("questions", [])
            for q in questions:
                question_text = q.get("question", "")
                console.print(f"\n[bold cyan]{question_text}[/bold cyan]")

        elif event_type == "plan_mode_requested":
            # Agent wants to enter plan mode
            console.print(f"\n[yellow]Agent requested plan mode[/yellow]")

        elif event_type == "plan_submitted":
            # Agent submitted a plan
            console.print(f"\n[green]Plan submitted for review[/green]")

        elif event_type == "context_frame":
            # Context frame update
            frame_type = data.get("type", "")
            if frame_type:
                console.print(f"[dim]Context: {frame_type}[/dim]")

        elif event_type == "queue_updated":
            length = data.get("length", 0)
            if length > 0:
                console.print(f"[dim]Queue: {length} message(s) waiting[/dim]")

        elif event_type == "state_changed":
            state = data.get("state", "")
            if state == "agent_busy":
                console.print(f"[dim]Agent is processing...[/dim]")
            elif state == "active":
                console.print(f"[dim]Agent ready[/dim]")

        elif event_type == "session_start":
            # Initial state when connecting
            participants = data.get("participants", [])
            message_count = data.get("message_count", 0)
            console.print(f"[dim]Connected to session ({len(participants)} participants, {message_count} messages)[/dim]")

        elif event_type == "session_end":
            console.print(f"\n[yellow]Session ended[/yellow]")

        elif event_type == "user_typing":
            # Another user is typing
            name = data.get("display_name", "Someone")
            console.print(f"[dim italic]{name} is typing...[/dim italic]", end="\r")

        elif event_type == "user_stopped_typing":
            # Another user stopped typing - clear the line
            console.print(" " * 40, end="\r")  # Clear typing indicator

        elif event_type == "process_message_request":
            # Server is asking the owner to process a message from another user
            console.print(f"\n[cyan]>>> Received process_message_request[/cyan]")
            console.print(f"[dim]  is_owner={self.is_owner}, has_callback={self.on_process_message is not None}[/dim]")
            owner_id = data.get("owner_id", "")
            if self.is_owner and self.on_process_message:
                # We're the owner - process this message with our local agent
                message_user = data.get("user_id", "")
                content = data.get("content", "")
                console.print(f"[dim]  Processing message from {message_user}: {content}[/dim]")
                # Call the callback to process the message
                self.on_process_message(data)
            elif owner_id == self.user_id:
                # We're the owner but no callback - shouldn't happen
                console.print(f"\n[yellow]Received process request but no handler configured[/yellow]")

        # Ignore other event types silently


def create_listener(
    base_url: str,
    session_id: str,
    user_id: str,
    on_event: Optional[Callable[[dict], None]] = None,
    on_process_message: Optional[Callable[[dict], None]] = None,
    is_owner: bool = False,
) -> SharedSessionListener:
    """Factory function to create an SSE listener.

    Args:
        base_url: API base URL
        session_id: Shared session ID
        user_id: This user's ID
        on_event: Optional custom event handler
        on_process_message: Callback for owner to process messages from other users
        is_owner: Whether this user is the session owner

    Returns:
        Configured SharedSessionListener instance
    """
    return SharedSessionListener(
        base_url=base_url,
        session_id=session_id,
        user_id=user_id,
        on_event=on_event,
        on_process_message=on_process_message,
        is_owner=is_owner,
    )

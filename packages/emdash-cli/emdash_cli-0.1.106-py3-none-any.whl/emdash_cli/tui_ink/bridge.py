"""Bridge between Python backend and Ink TUI frontend.

Communication protocol:
- Python sends JSON events to Ink via stdin
- Ink sends JSON responses to Python via stdout
- Each message is a single line of JSON followed by newline
"""

import asyncio
import base64
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import AsyncIterator, Callable, Optional

from ..handlers.decorators import EventDecorator, StandardDecorator, SharedDecorator


def _convert_attachments_to_images(attachments: list[dict]) -> list[dict]:
    """Convert TUI image attachments to the format expected by the API.

    Args:
        attachments: List of {"id": str, "path": str, "name": str} from TUI

    Returns:
        List of {"data": base64_str, "format": "png"|"jpg"|...} for API
    """
    images = []
    for attachment in attachments:
        path = attachment.get("path", "")
        if not path or not os.path.exists(path):
            continue

        # Determine format from extension
        ext = Path(path).suffix.lower()
        format_map = {
            ".png": "png",
            ".jpg": "jpeg",
            ".jpeg": "jpeg",
            ".gif": "gif",
            ".webp": "webp",
        }
        img_format = format_map.get(ext, "png")

        try:
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            images.append({"data": data, "format": img_format})
        except Exception:
            # Skip images that can't be read
            pass

    return images
from ..handlers.multiuser_listener import TUISessionListener
from ..handlers.project_sync import SyncManager, create_sync


def find_ink_tui_path() -> Path:
    """Find the compiled Ink TUI entry point."""
    # Check for bundled version first (installed via pip/uv)
    # Path: packages/cli/emdash_cli/tui_ink/bridge.py -> tui_ink/bundle/
    bundle_path = Path(__file__).parent / "bundle" / "emdash-tui.mjs"
    if bundle_path.exists():
        return bundle_path

    # Check relative to this file (development)
    # Path: packages/cli/emdash_cli/tui_ink/bridge.py -> packages/tui-ink
    pkg_dir = Path(__file__).parent.parent.parent.parent / "tui-ink"

    # Try compiled dist first
    dist_path = pkg_dir / "dist" / "index.js"
    if dist_path.exists():
        return dist_path

    # Try source with tsx (development)
    src_path = pkg_dir / "src" / "index.tsx"
    if src_path.exists():
        return src_path

    # Check if installed globally via npm
    try:
        result = subprocess.run(
            ["which", "emdash-tui"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass

    raise FileNotFoundError(
        "Ink TUI not found. Please ensure Node.js >= 18 is installed."
    )


class InkTUIBridge:
    """Bridge for communicating with the Ink TUI process."""

    def __init__(self, model: str | None = None, mode: str = "code"):
        # Use EMDASH_MODEL env var if model not specified
        if model is None:
            model = os.environ.get("EMDASH_MODEL", "claude-sonnet-4")
        self.model = model
        self.mode = mode
        self.process: subprocess.Popen | None = None
        self._reader_task: asyncio.Task | None = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._cancelled = False  # Flag to signal cancellation during processing
        # Multiuser state
        self._multiuser_listener: Optional[TUISessionListener] = None
        self._multiuser_session_id: Optional[str] = None
        self._multiuser_user_id: Optional[str] = None
        self._multiuser_server_url: Optional[str] = None
        self._multiuser_is_owner: bool = False
        # Bidirectional sync (Firebase/local ↔ core)
        self._sync_manager: Optional[SyncManager] = None
        # Handler for processing messages (set by run_ink_tui)
        self._on_submit: Optional[Callable] = None
        # Decorator for message processing (StandardDecorator by default, SharedDecorator in multiuser)
        self._decorator: Optional[EventDecorator] = None
        self._standard_decorator: Optional[StandardDecorator] = None

    async def start(self) -> None:
        """Start the Ink TUI process."""
        tui_path = find_ink_tui_path()

        # Determine command based on file extension
        if tui_path.suffix == ".tsx":
            # Development mode - use tsx
            cmd = ["npx", "tsx", str(tui_path)]
        else:
            # Production mode - use node
            cmd = ["node", str(tui_path)]

        # Start process with pipes
        # - stdin: PIPE for sending JSON events from Python to Ink
        # - stdout: inherited (None) so Ink can render directly to terminal
        # - stderr: PIPE for receiving JSON responses from Ink
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=None,  # Ink renders directly to terminal
            stderr=subprocess.PIPE,  # Ink sends JSON responses here
            cwd=os.getcwd(),
            env={**os.environ, "FORCE_COLOR": "1"},  # Enable colors
        )

        self._running = True

        # Start reader task
        self._reader_task = asyncio.create_task(self._read_loop())

        # Wait for ready signal
        await self._wait_for_ready()

        # Send init event
        await self.send_event("init", {
            "model": self.model,
            "mode": self.mode,
            "cwd": os.getcwd(),
        })

    async def _wait_for_ready(self, timeout: float = 10.0) -> None:
        """Wait for the TUI to signal it's ready."""
        try:
            msg = await asyncio.wait_for(self._message_queue.get(), timeout=timeout)
            if msg.get("type") == "user_input" and msg.get("data", {}).get("content") == "__ink_ready__":
                return
            # Put it back if it's not the ready signal
            await self._message_queue.put(msg)
        except asyncio.TimeoutError:
            raise TimeoutError("Ink TUI failed to start within timeout")

    async def _read_loop(self) -> None:
        """Read messages from the Ink TUI process (via stderr)."""
        if not self.process or not self.process.stderr:
            return

        loop = asyncio.get_event_loop()

        while self._running:
            try:
                # Read line asynchronously from stderr
                line = await loop.run_in_executor(
                    None, self.process.stderr.readline
                )

                if not line:
                    # Process ended
                    break

                # Parse JSON
                try:
                    msg = json.loads(line.decode("utf-8").strip())
                    await self._message_queue.put(msg)
                except json.JSONDecodeError:
                    # Invalid JSON - skip
                    pass

            except Exception:
                if self._running:
                    # Unexpected error
                    break

    async def send_event(self, event_type: str, data: dict) -> None:
        """Send an event to the Ink TUI."""
        if not self.process or not self.process.stdin:
            return

        msg = json.dumps({"type": event_type, "data": data})
        try:
            self.process.stdin.write(f"{msg}\n".encode("utf-8"))
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            # Process ended
            self._running = False

    async def read_message(self, timeout: float | None = None) -> dict | None:
        """Read a message from the Ink TUI."""
        try:
            if timeout:
                return await asyncio.wait_for(self._message_queue.get(), timeout=timeout)
            return await self._message_queue.get()
        except asyncio.TimeoutError:
            return None

    async def stop(self) -> None:
        """Stop the Ink TUI process."""
        self._running = False

        # Stop multiuser listener and project sync if running
        await self.stop_multiuser_listener()
        await self.stop_sync()

        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self.process:
            try:
                # Send exit event
                await self.send_event("exit", {})
                # Wait briefly for graceful shutdown
                self.process.wait(timeout=2)
            except Exception:
                pass

            # Force kill if still running
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()

    def is_running(self) -> bool:
        """Check if the TUI process is still running."""
        return self._running and self.process is not None and self.process.poll() is None

    async def start_multiuser_listener(
        self,
        server_url: str,
        session_id: str,
        user_id: str,
        is_owner: bool = False,
    ) -> None:
        """Start the multiuser SSE listener.

        Args:
            server_url: API base URL
            session_id: Shared session ID
            user_id: This user's ID
            is_owner: Whether this user owns the session
        """
        # Stop existing listener if any
        await self.stop_multiuser_listener()

        self._multiuser_session_id = session_id
        self._multiuser_user_id = user_id
        self._multiuser_is_owner = is_owner

        def on_multiuser_event(event: dict) -> None:
            """Handle events from the SSE listener."""
            event_type = event.get("type", "unknown")
            event_data = event.get("data", {})

            # Owner handles process_message_request by processing through agent
            if is_owner and event_type == "process_message_request" and self._on_submit:
                # Process the message through the agent
                asyncio.create_task(self._process_message_request(event_data))
                return

            # Forward other events to the Ink TUI
            asyncio.create_task(self.send_event(event_type, event_data))

        self._multiuser_listener = TUISessionListener(
            base_url=server_url,
            session_id=session_id,
            user_id=user_id,
            on_event=on_multiuser_event,
            is_owner=is_owner,
        )
        await self._multiuser_listener.start()

    async def _process_message_request(self, event_data: dict) -> None:
        """Process a message request from another user through the agent.

        In the decorator architecture, the SharedDecorator handles agent
        processing and broadcasts events to all participants.

        Args:
            event_data: The process_message_request event data
        """
        content = event_data.get("content", "")
        display_name = event_data.get("display_name", "User")
        chat_context = event_data.get("chat_context", [])

        if not content:
            return

        # Use the SharedDecorator's process_agent_request method
        # which handles processing and broadcasting
        if self._decorator and isinstance(self._decorator, SharedDecorator):
            try:
                async for event in self._decorator.process_agent_request(
                    content, display_name, chat_context=chat_context,
                ):
                    event_type = event["type"]
                    ev_data = event.get("data", {})
                    await self.send_event(event_type, ev_data)
            except Exception as e:
                await self.send_event("error", {"message": str(e)})
        elif self._on_submit:
            # Fallback: process through handler directly (shouldn't happen in shared mode)
            await self.send_event("response", {
                "content": f"**{display_name}** asked: {content}"
            })
            try:
                async for event in self._on_submit(content):
                    event_type = event["type"]
                    ev_data = event.get("data", {})
                    await self.send_event(event_type, ev_data)
            except Exception as e:
                await self.send_event("error", {"message": str(e)})

    async def stop_multiuser_listener(self) -> None:
        """Stop the multiuser SSE listener if running."""
        if self._multiuser_listener:
            await self._multiuser_listener.stop()
            self._multiuser_listener = None
        self._multiuser_session_id = None
        self._multiuser_user_id = None
        self._multiuser_server_url = None

    async def start_sync(
        self, server_url: str, user_id: str, team_id: str = ""
    ) -> None:
        """Start bidirectional store ↔ core sync for all entity types.

        Auto-detects backend from environment:
            - EMDASH_MULTIUSER_PROVIDER=firebase → Firebase
            - EMDASH_MULTIUSER_PROVIDER=local → local JSON files
            - unset → Firebase if configured, else local files
        """
        import logging

        log = logging.getLogger(__name__)

        await self.stop_sync()

        if not team_id:
            team_id = os.environ.get("EMDASH_TEAM_ID", "")
        if not team_id:
            # Use "local" as default team_id for local file persistence
            team_id = "local"
            log.debug("Using default team_id='local' for project sync")

        try:
            self._sync_manager = create_sync(
                core_url=server_url,
                user_id=user_id,
                team_id=team_id,
            )
            if self._sync_manager:
                await self._sync_manager.start()
                log.info("Sync manager started (store ↔ core)")
            else:
                log.debug("No sync backend configured")
        except Exception as e:
            log.warning(f"Failed to start sync manager: {e}")
            self._sync_manager = None

    async def stop_sync(self) -> None:
        """Stop sync manager if running."""
        if self._sync_manager:
            await self._sync_manager.stop()
            self._sync_manager = None

    def set_shared_mode(
        self,
        session_id: str,
        user_id: str,
        server_url: str,
        is_owner: bool,
    ) -> None:
        """Switch to shared decorator for multiuser mode.

        In shared mode, messages are sent to the server and events
        come back via SSE. This provides a single source of truth
        for all participants.

        Args:
            session_id: The shared session ID
            user_id: This user's ID
            server_url: API base URL
            is_owner: Whether this user is the session owner
        """
        if not self._on_submit:
            return

        self._multiuser_session_id = session_id
        self._multiuser_user_id = user_id
        self._multiuser_server_url = server_url
        self._multiuser_is_owner = is_owner

        self._decorator = SharedDecorator(
            session_id=session_id,
            user_id=user_id,
            server_url=server_url,
            handler=self._on_submit,
            is_owner=is_owner,
        )

    def set_standard_mode(self) -> None:
        """Switch back to standard decorator for solo mode.

        In solo mode, events are processed locally and yielded
        directly to the TUI.
        """
        self._decorator = self._standard_decorator
        self._multiuser_is_owner = False

    async def broadcast_typing(self, is_typing: bool) -> None:
        """Broadcast typing indicator to multiuser session.

        Args:
            is_typing: True if user started typing, False if stopped
        """
        if not self._multiuser_session_id or not self._multiuser_user_id:
            return

        if not self._multiuser_listener:
            return

        server_url = self._multiuser_listener.base_url
        event_type = "user_typing" if is_typing else "user_stopped_typing"

        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{server_url}/api/multiuser/session/{self._multiuser_session_id}/broadcast_event",
                    json={
                        "user_id": self._multiuser_user_id,
                        "event_type": event_type,
                        "data": {
                            "user_id": self._multiuser_user_id,
                            "display_name": self._multiuser_user_id,  # TODO: Use actual display name
                        },
                    },
                )
        except Exception:
            # Silently ignore typing broadcast failures
            pass


async def run_ink_tui(
    on_submit: Callable[[str], AsyncIterator[dict]],
    model: str | None = None,
    mode: str = "code",
) -> None:
    """Run the Ink TUI with the given handler.

    Args:
        on_submit: Async callable that takes a message and yields event dicts
        model: Model name to use
        mode: Agent mode (code or plan)
    """
    bridge = InkTUIBridge(model=model, mode=mode)
    bridge._on_submit = on_submit  # Store handler for multiuser message processing

    # Initialize decorators
    bridge._standard_decorator = StandardDecorator(on_submit)
    bridge._decorator = bridge._standard_decorator

    # Handle signals
    def signal_handler(_sig, _frame):
        asyncio.create_task(bridge.stop())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await bridge.start()

        # Start project sync at TUI startup (persists projects/tasks to disk)
        try:
            from ..server_manager import get_server_manager
            import hashlib
            import socket

            server = get_server_manager()
            server_url = server.get_server_url()

            # Generate a default user_id for local persistence
            hostname = socket.gethostname()
            username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
            pid = os.getpid()
            user_id = hashlib.sha256(f"{username}@{hostname}:{pid}".encode()).hexdigest()[:16]

            # Start sync (will use "local" team_id by default)
            await bridge.start_sync(server_url=server_url, user_id=user_id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to start project sync at startup: {e}")

        while bridge.is_running():
            # Wait for user input
            msg = await bridge.read_message(timeout=0.1)

            if msg is None:
                continue

            msg_type = msg.get("type")
            data = msg.get("data", {})

            if msg_type == "user_input":
                content = data.get("content", "")
                if not content or content == "__ink_ready__":
                    continue

                # Extract and convert image attachments
                attachments = data.get("attachments", [])
                images = _convert_attachments_to_images(attachments) if attachments else None

                # Process message through the active decorator
                # In standard mode: direct passthrough to handler
                # In shared mode: sends to server, events come via SSE
                bridge._cancelled = False  # Reset cancellation flag
                try:
                    if bridge._decorator:
                        async for event in bridge._decorator.process_message(content, images=images):
                            # Check for cancellation by peeking at message queue
                            try:
                                peek_msg = bridge._message_queue.get_nowait()
                                if peek_msg and peek_msg.get("type") == "cancel":
                                    # User cancelled - abort and break out
                                    bridge._cancelled = True
                                    if hasattr(on_submit, "abort_session"):
                                        try:
                                            await on_submit.abort_session()
                                        except Exception:
                                            pass
                                    await bridge.send_event("response", {
                                        "content": "Operation cancelled."
                                    })
                                    break
                                else:
                                    # Not a cancel, put it back
                                    await bridge._message_queue.put(peek_msg)
                            except asyncio.QueueEmpty:
                                pass  # No message waiting, continue

                            event_type = event["type"]
                            event_data = event.get("data", {})

                            # Forward event to TUI
                            await bridge.send_event(event_type, event_data)

                            # Handle multiuser mode transitions
                            if event_type == "multiuser_started":
                                server_url = event_data.get("server_url", "")
                                session_id = event_data.get("session_id", "")
                                user_id = event_data.get("user_id", "")
                                is_owner = event_data.get("is_owner", False)
                                if server_url and session_id and user_id:
                                    # Switch to shared decorator
                                    bridge.set_shared_mode(
                                        session_id=session_id,
                                        user_id=user_id,
                                        server_url=server_url,
                                        is_owner=is_owner,
                                    )
                                    # Start SSE listener for incoming events
                                    await bridge.start_multiuser_listener(
                                        server_url=server_url,
                                        session_id=session_id,
                                        user_id=user_id,
                                        is_owner=is_owner,
                                    )
                                    # Start store ↔ core bidirectional sync
                                    team_id = os.environ.get("EMDASH_TEAM_ID", "")
                                    await bridge.start_sync(
                                        server_url=server_url,
                                        user_id=user_id,
                                        team_id=team_id,
                                    )
                            elif event_type == "multiuser_stopped":
                                # Switch back to standard decorator
                                bridge.set_standard_mode()
                                await bridge.stop_multiuser_listener()
                                await bridge.stop_sync()
                except Exception as e:
                    if not bridge._cancelled:  # Don't show error if cancelled
                        await bridge.send_event("error", {"message": str(e)})

            elif msg_type == "cancel":
                # User cancelled - only handle if not already cancelled during processing
                if not bridge._cancelled:
                    # Call abort endpoint to stop the agent
                    if hasattr(on_submit, "abort_session"):
                        try:
                            await on_submit.abort_session()
                        except Exception:
                            pass  # Ignore abort errors
                    await bridge.send_event("response", {
                        "content": "Operation cancelled."
                    })

            elif msg_type == "quit":
                break

            elif msg_type == "choice_answer":
                # Handle choice responses - send the answer as a user message
                # This continues the conversation with the user's choice
                selected = data.get("selected", "")
                custom_value = data.get("custom_value", "")
                answer = custom_value if data.get("is_other") else selected

                # Format as a clear response and send to handler
                if answer:
                    # In shared mode, broadcast prompt_resolved so non-owners
                    # clear their read-only overlay.
                    if bridge._decorator and isinstance(bridge._decorator, SharedDecorator):
                        await bridge._decorator.broadcast_event(
                            "prompt_resolved",
                            {"resolved_by": bridge._multiuser_user_id, "answer": answer},
                        )
                    try:
                        async for event in on_submit(answer):
                            await bridge.send_event(event["type"], event.get("data", {}))
                    except Exception as e:
                        await bridge.send_event("error", {"message": str(e)})

            elif msg_type == "plan_approval":
                # Handle plan approval - these go to the handler
                # The handler needs to support receiving these
                approved = data.get("approved", False)
                reply = data.get("reply")
                approval_type = data.get("approvalType", "planmode")  # 'planmode' or 'plan'

                # In shared mode, broadcast prompt_resolved so non-owners
                # clear their read-only overlay.
                if bridge._decorator and isinstance(bridge._decorator, SharedDecorator):
                    await bridge._decorator.broadcast_event(
                        "prompt_resolved",
                        {
                            "resolved_by": bridge._multiuser_user_id,
                            "approved": approved,
                            "approval_type": approval_type,
                        },
                    )

                if hasattr(on_submit, "approve_plan_mode"):
                    async for event in on_submit.approve_plan_mode(approved, reply, approval_type):
                        await bridge.send_event(event["type"], event.get("data", {}))

            elif msg_type == "set_mode":
                # Handle mode change from TUI
                new_mode = data.get("mode", "code")
                bridge.mode = new_mode
                # Notify handler if it supports mode changes
                if hasattr(on_submit, "set_mode"):
                    on_submit.set_mode(new_mode)

            elif msg_type == "set_model":
                # Handle model change from TUI
                new_model = data.get("model", "")
                if new_model:
                    bridge.model = new_model
                    # Notify handler if it supports model changes
                    if hasattr(on_submit, "set_model"):
                        on_submit.set_model(new_model)

            elif msg_type == "reset_session":
                # Handle session reset from TUI
                if hasattr(on_submit, "reset_session"):
                    on_submit.reset_session()

            elif msg_type == "registry_install":
                # Handle registry install request from TUI
                category = data.get("category", "")
                name = data.get("name", "")
                if category and name:
                    try:
                        result = await _install_registry_component(category, name)
                        await bridge.send_event("registry_install_result", result)
                    except Exception as e:
                        await bridge.send_event("registry_install_result", {
                            "success": False,
                            "category": category,
                            "name": name,
                            "message": str(e),
                        })

            elif msg_type == "user_typing":
                # Broadcast typing indicator to multiuser session
                await bridge.broadcast_typing(True)

            elif msg_type == "user_stopped_typing":
                # Broadcast stopped typing to multiuser session
                await bridge.broadcast_typing(False)

    finally:
        await bridge.stop()


async def _install_registry_component(category: str, name: str) -> dict:
    """Install a component from the registry.

    Args:
        category: Component type (skills, rules, agents, verifiers)
        name: Component name

    Returns:
        Result dict with success, category, name, message, and optionally path
    """
    import httpx
    from pathlib import Path

    REGISTRY_URL = "https://raw.githubusercontent.com/mendyEdri/emdash-registry/main/registry.json"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch registry
        resp = await client.get(REGISTRY_URL)
        resp.raise_for_status()
        registry = resp.json()

        # Find component
        components = registry.get(category, {})
        if name not in components:
            return {
                "success": False,
                "category": category,
                "name": name,
                "message": f"Component '{name}' not found in {category}",
            }

        component = components[name]
        content_url = component.get("url") or component.get("content_url")

        if not content_url:
            return {
                "success": False,
                "category": category,
                "name": name,
                "message": "Component has no content URL",
            }

        # Fetch component content
        content_resp = await client.get(content_url)
        content_resp.raise_for_status()
        content = content_resp.text

        # Determine installation path
        emdash_dir = Path.cwd() / ".emdash"

        if category == "skills":
            install_dir = emdash_dir / "skills" / name
            install_dir.mkdir(parents=True, exist_ok=True)
            install_path = install_dir / "SKILL.md"
        elif category == "rules":
            install_dir = emdash_dir / "rules"
            install_dir.mkdir(parents=True, exist_ok=True)
            install_path = install_dir / f"{name}.md"
        elif category == "agents":
            install_dir = emdash_dir / "agents"
            install_dir.mkdir(parents=True, exist_ok=True)
            install_path = install_dir / f"{name}.md"
        elif category == "verifiers":
            install_dir = emdash_dir / "verifiers"
            install_dir.mkdir(parents=True, exist_ok=True)
            install_path = install_dir / f"{name}.md"
        else:
            return {
                "success": False,
                "category": category,
                "name": name,
                "message": f"Unknown category: {category}",
            }

        # Write content
        install_path.write_text(content)

        return {
            "success": True,
            "category": category,
            "name": name,
            "message": "Installed successfully",
            "path": str(install_path),
        }

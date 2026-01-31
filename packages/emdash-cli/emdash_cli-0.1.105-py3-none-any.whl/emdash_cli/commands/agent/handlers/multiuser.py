"""Handlers for multiuser slash commands (/share, /join, /leave, /who) and team commands."""

import asyncio
import os
import subprocess
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markup import escape

console = Console()


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if sys.platform == "darwin":
            # macOS
            subprocess.run(
                ["pbcopy"],
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            return True
        elif sys.platform == "win32":
            # Windows
            subprocess.run(
                ["clip"],
                input=text.encode("utf-16le"),
                check=True,
                capture_output=True,
            )
            return True
        else:
            # Linux - try xclip first, then xsel
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    subprocess.run(
                        cmd,
                        input=text.encode("utf-8"),
                        check=True,
                        capture_output=True,
                    )
                    return True
                except FileNotFoundError:
                    continue
            return False
    except Exception:
        return False


def get_default_team_id() -> str:
    """Get default team ID from environment."""
    return os.environ.get("EMDASH_TEAM_ID", "")


def send_shared_message(
    client,
    session_id: str,
    user_id: str,
    content: str,
    images: list[dict] | None = None,
    server_url: str | None = None,
) -> dict:
    """Send a message to a shared session.

    The message will be queued if the agent is busy processing another message.

    Args:
        client: API client with base_url
        session_id: The shared session ID
        user_id: The sending user's ID
        content: Message content
        images: Optional list of image dicts
        server_url: Optional server URL to use instead of client.base_url

    Returns:
        Dict with message_id, queued_at, queue_position, agent_busy
        Empty dict on error.
    """
    import httpx

    # Use explicit server_url if provided, otherwise fall back to client.base_url
    base_url = server_url or client.base_url
    console.print(f"[dim]Sending message to session {session_id[:8]}... (user={user_id[:8]}, server={base_url})[/dim]")

    try:
        response = httpx.post(
            f"{base_url}/api/multiuser/session/{session_id}/message",
            json={
                "user_id": user_id,
                "content": content,
                "images": images,
                "priority": 0,
            },
            timeout=30.0,
        )

        console.print(f"[dim]Server response: {response.status_code}[/dim]")

        if response.status_code == 200:
            result = response.json()
            console.print(f"[dim]Message queued: id={result.get('message_id', 'unknown')[:8]}...[/dim]")
            return result
        else:
            console.print(f"[red]Failed to send message: {response.status_code} - {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error sending message: {e}[/red]")
        return {}


def broadcast_event(
    client,
    session_id: str,
    user_id: str,
    event_type: str,
    data: dict | None = None,
) -> bool:
    """Broadcast a generic event to all participants in a shared session.

    Args:
        client: API client with base_url
        session_id: The shared session ID
        user_id: Sending user's ID
        event_type: Event type string
        data: Optional event data

    Returns:
        True if successful, False otherwise.
    """
    import httpx

    try:
        response = httpx.post(
            f"{client.base_url}/api/multiuser/session/{session_id}/broadcast_event",
            json={
                "user_id": user_id,
                "event_type": event_type,
                "data": data or {},
            },
            timeout=5.0,  # Shorter timeout for faster failures
        )
        return response.status_code == 200

    except Exception:
        return False  # Silently fail for non-critical events


def broadcast_typing(client, session_id: str, user_id: str, is_typing: bool = True) -> bool:
    """Broadcast typing indicator to all participants."""
    event_type = "user_typing" if is_typing else "user_stopped_typing"
    return broadcast_event(client, session_id, user_id, event_type)


def broadcast_agent_response(
    client,
    session_id: str,
    user_id: str,
    original_user_id: str | None,
    original_content: str,
    response_content: str,
) -> bool:
    """Broadcast an agent response to all participants in a shared session.

    This is called by the session owner after processing a message locally.

    Args:
        client: API client with base_url
        session_id: The shared session ID
        user_id: Owner's user ID
        original_user_id: User ID who sent the original message (None if owner)
        original_content: Original message content
        response_content: Agent's response content

    Returns:
        True if successful, False otherwise.
    """
    import httpx

    console.print(f"[dim]Broadcasting response to shared session...[/dim]")

    try:
        response = httpx.post(
            f"{client.base_url}/api/multiuser/session/{session_id}/broadcast_response",
            json={
                "user_id": user_id,
                "original_user_id": original_user_id,
                "original_content": original_content,
                "response_content": response_content,
            },
            timeout=60.0,
        )

        if response.status_code == 200:
            console.print(f"[dim]Broadcast successful[/dim]")
            return True
        else:
            console.print(f"[yellow]Failed to broadcast response: {response.text}[/yellow]")
            return False

    except Exception as e:
        console.print(f"[yellow]Error broadcasting response: {e}[/yellow]")
        return False


def _generate_user_id() -> str:
    """Generate a unique user ID for this CLI instance.

    Includes PID to ensure uniqueness when testing with multiple
    terminals on the same machine.
    """
    import hashlib
    import socket
    hostname = socket.gethostname()
    username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    pid = os.getpid()
    return hashlib.sha256(f"{username}@{hostname}:{pid}".encode()).hexdigest()[:16]


def handle_share(args: str, client, session_id: str, model: str | None, plan_mode: bool) -> dict:
    """Handle /share command to create a shared session.

    Args:
        args: Optional display name
        client: API client
        session_id: Current session ID
        model: Current model (can be None)
        plan_mode: Whether in plan mode

    Returns:
        Dict with shared session info (session_id, invite_code, user_id, server_url) or empty dict on error
    """
    import httpx
    import socket

    # Get display name from args or use default
    display_name = args.strip() if args else None
    hostname = socket.gethostname()
    username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    if not display_name:
        display_name = f"{username}@{hostname}"

    # Generate unique user_id for this CLI instance
    user_id = _generate_user_id()

    # Use default model if not set
    effective_model = model or os.environ.get("EMDASH_MODEL", "default")

    try:
        # Call API to create shared session
        response = httpx.post(
            f"{client.base_url}/api/multiuser/session/create",
            json={
                "user_id": user_id,
                "display_name": display_name,
                "model": effective_model,
                "plan_mode": plan_mode,
            },
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            invite_code = data.get("invite_code", "")
            shared_session_id = data.get("session_id", "")

            # Encode server URL into invite code so joiner connects to same server
            # Format: INVITE_CODE@PORT (e.g., ABC123@57220)
            port = client.base_url.split(":")[-1]  # Extract port from URL
            full_invite = f"{invite_code}@{port}"

            # Copy full invite code to clipboard
            copied = copy_to_clipboard(full_invite)
            clipboard_msg = "[dim](copied to clipboard)[/dim]" if copied else ""

            console.print()
            console.print(Panel(
                f"[bold green]Session shared![/bold green]\n\n"
                f"[bold]Invite code:[/bold] [cyan]{full_invite}[/cyan] {clipboard_msg}\n\n"
                f"Share this code with others to let them join.\n"
                f"They can join with: [dim]/join {full_invite}[/dim]",
                title="🔗 Shared Session",
                border_style="green",
            ))
            console.print()

            return {
                "session_id": shared_session_id,
                "invite_code": invite_code,
                "user_id": user_id,
                "server_url": client.base_url,
            }
        else:
            console.print(f"[red]Failed to create shared session: {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error creating shared session: {e}[/red]")
        return {}


def fetch_session_messages_from_url(server_url: str, session_id: str, limit: int = 20) -> list:
    """Fetch recent messages from a session using explicit server URL.

    Args:
        server_url: Server URL (e.g., http://localhost:57220)
        session_id: The session ID
        limit: Maximum number of messages to fetch

    Returns:
        List of message dicts with role, content, etc.
    """
    import httpx

    try:
        response = httpx.get(
            f"{server_url}/api/multiuser/session/{session_id}/messages",
            params={"limit": limit},
            timeout=30.0,
        )

        if response.status_code == 200:
            return response.json().get("messages", [])
    except Exception:
        pass

    return []


def fetch_session_messages(client, session_id: str, limit: int = 20) -> list:
    """Fetch recent messages from a session.

    Args:
        client: API client with base_url
        session_id: The session ID
        limit: Maximum number of messages to fetch

    Returns:
        List of message dicts with role, content, etc.
    """
    return fetch_session_messages_from_url(client.base_url, session_id, limit)


def handle_join(args: str, client) -> dict:
    """Handle /join command to join a shared session.

    Args:
        args: Invite code (format: INVITE_CODE or INVITE_CODE@PORT)
        client: API client

    Returns:
        Dict with joined session info (session_id, user_id, participants, message_count, server_url) or empty dict on error
    """
    import httpx
    import socket

    if not args:
        console.print("[yellow]Usage: /join <invite-code>[/yellow]")
        console.print("[dim]Example: /join ABC123@57220[/dim]")
        return {}

    raw_invite = args.strip()

    # Parse invite code - may include port (e.g., ABC123@57220)
    if "@" in raw_invite:
        invite_code, port_str = raw_invite.rsplit("@", 1)
        invite_code = invite_code.upper()
        try:
            port = int(port_str)
            # Use the server from the invite code
            server_url = f"http://localhost:{port}"
            console.print(f"[dim]Connecting to session server at port {port}...[/dim]")
        except ValueError:
            # Not a port number, treat whole thing as invite code
            invite_code = raw_invite.upper()
            server_url = client.base_url
    else:
        invite_code = raw_invite.upper()
        server_url = client.base_url

    # Get display name and generate unique user_id
    hostname = socket.gethostname()
    username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    display_name = f"{username}@{hostname}"
    user_id = _generate_user_id()

    try:
        # Call API to join session (use server_url which may be from invite code)
        response = httpx.post(
            f"{server_url}/api/multiuser/session/join",
            json={
                "invite_code": invite_code,
                "user_id": user_id,
                "display_name": display_name,
            },
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            joined_session_id = data.get("session_id", "")
            participants = data.get("participants", [])
            message_count = data.get("message_count", 0)

            # Fetch conversation history if there are messages (from same server)
            messages = []
            if message_count > 0:
                messages = fetch_session_messages_from_url(server_url, joined_session_id, limit=10)

            console.print()
            console.print(Panel(
                f"[bold green]Joined session![/bold green]\n\n"
                f"[bold]Session:[/bold] {joined_session_id[:8]}...\n"
                f"[bold]Participants:[/bold] {len(participants)}\n"
                f"[bold]Messages:[/bold] {message_count}\n\n"
                f"[dim]Use /who to see participants[/dim]",
                title="✓ Joined",
                border_style="green",
            ))
            console.print()

            # Display message history if available
            if messages:
                console.print(Panel(
                    f"[dim]Showing last {len(messages)} message(s)...[/dim]",
                    title="Session History",
                    border_style="dim",
                ))
                console.print()

                for msg in messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "")

                    # Truncate long messages for display
                    display_content = content[:300] + "..." if len(content) > 300 else content

                    if role == "user":
                        console.print(f"[bold]User:[/bold] {display_content}")
                    elif role == "assistant":
                        console.print(f"[cyan]Assistant:[/cyan] {display_content}")
                    console.print()

            return {
                "session_id": joined_session_id,
                "user_id": user_id,
                "participants": participants,
                "message_count": message_count,
                "messages": messages,
                "server_url": server_url,  # Return server URL for SSE listener
            }

        elif response.status_code == 404:
            console.print(f"[red]Invalid invite code: {invite_code}[/red]")
            console.print("[dim]Check the code and try again.[/dim]")
            return {}
        else:
            console.print(f"[red]Failed to join session: {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error joining session: {e}[/red]")
        return {}


def handle_leave(args: str, client, session_id: str, user_id: str) -> bool:
    """Handle /leave command to leave a shared session.

    Args:
        args: Unused
        client: API client
        session_id: Current session ID
        user_id: Current user ID

    Returns:
        True if left successfully
    """
    import httpx

    if not session_id:
        console.print("[yellow]Not in a shared session.[/yellow]")
        return False

    try:
        response = httpx.post(
            f"{client.base_url}/api/multiuser/session/{session_id}/leave",
            json={"user_id": user_id},
            timeout=30.0,
        )

        if response.status_code == 200:
            console.print("[green]Left the shared session.[/green]")
            return True
        else:
            console.print(f"[red]Failed to leave session: {response.text}[/red]")
            return False

    except Exception as e:
        console.print(f"[red]Error leaving session: {e}[/red]")
        return False


def handle_who(args: str, client, session_id: str) -> None:
    """Handle /who command to list participants in a shared session.

    Args:
        args: Unused
        client: API client
        session_id: Current session ID
    """
    import httpx

    if not session_id:
        console.print("[yellow]Not in a shared session.[/yellow]")
        console.print("[dim]Use /share to create one or /join to join one.[/dim]")
        return

    try:
        response = httpx.get(
            f"{client.base_url}/api/multiuser/session/{session_id}/participants",
            timeout=30.0,
        )

        if response.status_code == 200:
            participants = response.json()

            if not participants:
                console.print("[dim]No participants found.[/dim]")
                return

            table = Table(title="Session Participants", show_header=True)
            table.add_column("Name", style="cyan")
            table.add_column("Role", style="yellow")
            table.add_column("Status", style="green")
            table.add_column("Joined", style="dim")

            for p in participants:
                status = "🟢 Online" if p.get("is_online") else "⚪ Offline"
                role = p.get("role", "editor").title()
                if role == "Owner":
                    role = "👑 Owner"

                # Format joined time
                joined = p.get("joined_at", "")
                if joined:
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(joined.replace("Z", "+00:00"))
                        joined = dt.strftime("%H:%M")
                    except Exception:
                        joined = joined[:10]

                table.add_row(
                    p.get("display_name", "Unknown"),
                    role,
                    status,
                    joined,
                )

            console.print()
            console.print(table)
            console.print()

        elif response.status_code == 404:
            console.print("[yellow]Session not found. It may have been closed.[/yellow]")
        else:
            console.print(f"[red]Failed to get participants: {response.text}[/red]")

    except Exception as e:
        console.print(f"[red]Error getting participants: {e}[/red]")


def handle_invite(args: str, client, session_id: str) -> None:
    """Handle /invite command to show/refresh invite code.

    Args:
        args: Unused
        client: API client
        session_id: Current session ID
    """
    import httpx

    if not session_id:
        console.print("[yellow]Not in a shared session.[/yellow]")
        console.print("[dim]Use /share to create one first.[/dim]")
        return

    try:
        response = httpx.get(
            f"{client.base_url}/api/multiuser/session/{session_id}/state",
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            invite_code = data.get("invite_code", "")

            if invite_code:
                console.print()
                console.print(Panel(
                    f"[bold]Invite code:[/bold] [cyan]{invite_code}[/cyan]\n\n"
                    f"Others can join with: [dim]/join {invite_code}[/dim]",
                    title="🔗 Invite Code",
                    border_style="blue",
                ))
                console.print()
            else:
                console.print("[yellow]No invite code available.[/yellow]")
        else:
            console.print(f"[red]Failed to get session info: {response.text}[/red]")

    except Exception as e:
        console.print(f"[red]Error getting invite code: {e}[/red]")


def handle_multiuser_status(args: str, client, session_id: str) -> None:
    """Handle multiuser status display.

    Shows current shared session status including queue state.

    Args:
        args: Unused
        client: API client
        session_id: Current session ID
    """
    import httpx

    if not session_id:
        console.print("[dim]Not in a shared session.[/dim]")
        return

    try:
        response = httpx.get(
            f"{client.base_url}/api/multiuser/session/{session_id}/state",
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()

            state = data.get("state", "unknown")
            participants = data.get("participants", [])
            queue_length = data.get("queue_length", 0)
            agent_busy = data.get("agent_busy", False)
            invite_code = data.get("invite_code", "")

            # Status emoji
            if agent_busy:
                status_emoji = "🔄"
                status_text = "Agent processing"
            elif state == "active":
                status_emoji = "🟢"
                status_text = "Active"
            else:
                status_emoji = "⚪"
                status_text = state.title()

            console.print()
            console.print(Panel(
                f"[bold]Status:[/bold] {status_emoji} {status_text}\n"
                f"[bold]Invite:[/bold] [cyan]{invite_code}[/cyan]\n"
                f"[bold]Participants:[/bold] {len(participants)}\n"
                f"[bold]Queue:[/bold] {queue_length} message(s)",
                title="📡 Shared Session",
                border_style="blue",
            ))
            console.print()

        elif response.status_code == 404:
            console.print("[yellow]Session not found.[/yellow]")
        else:
            console.print(f"[red]Failed to get status: {response.text}[/red]")

    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")


# ─────────────────────────────────────────────────────────────────────────────
# Team Commands
# ─────────────────────────────────────────────────────────────────────────────


def handle_team(args: str, client, session_id: str, user_id: str) -> dict:
    """Handle /team command and subcommands.

    Subcommands:
        /team create <name>      - Create a new team
        /team join <invite>      - Join a team using invite code
        /team leave [team-id]    - Leave a team
        /team list               - List your teams
        /team sessions [team-id] - List sessions in a team
        /team add [session-id]   - Add current/specified session to team
        /team join-session <id>  - Join a team session directly

    Args:
        args: Subcommand and arguments
        client: API client
        session_id: Current session ID
        user_id: Current user ID

    Returns:
        Dict with result info
    """
    parts = args.strip().split(maxsplit=1)
    subcommand = parts[0].lower() if parts else ""
    subargs = parts[1] if len(parts) > 1 else ""

    if not subcommand:
        _show_team_help()
        return {}

    if subcommand == "create":
        return handle_team_create(subargs, client, user_id)
    elif subcommand == "join":
        return handle_team_join(subargs, client, user_id)
    elif subcommand == "leave":
        return handle_team_leave(subargs, client, user_id)
    elif subcommand == "list":
        return handle_team_list(subargs, client, user_id)
    elif subcommand == "sessions":
        return handle_team_sessions(subargs, client, user_id)
    elif subcommand == "add":
        return handle_team_add_session(subargs, client, session_id, user_id)
    elif subcommand in ("join-session", "js"):
        return handle_team_join_session(subargs, client, user_id)
    elif subcommand == "info":
        return handle_team_info(subargs, client, user_id)
    else:
        console.print(f"[yellow]Unknown team subcommand: {subcommand}[/yellow]")
        _show_team_help()
        return {}


def _show_team_help() -> None:
    """Show help for team commands."""
    console.print()
    console.print(Panel(
        "[bold]Team Commands[/bold]\n\n"
        "[cyan]/team create <name>[/cyan]      - Create a new team\n"
        "[cyan]/team join <invite>[/cyan]      - Join a team using invite code\n"
        "[cyan]/team leave [team-id][/cyan]    - Leave a team\n"
        "[cyan]/team list[/cyan]               - List your teams\n"
        "[cyan]/team sessions [team-id][/cyan] - List sessions in a team\n"
        "[cyan]/team add [session-id][/cyan]   - Add session to default team\n"
        "[cyan]/team join-session <id>[/cyan]  - Join a team session\n"
        "[cyan]/team info [team-id][/cyan]     - Show team info",
        title="📋 Team Help",
        border_style="blue",
    ))
    console.print()


def handle_team_create(args: str, client, user_id: str) -> dict:
    """Handle /team create <name> command."""
    import httpx

    if not args:
        console.print("[yellow]Usage: /team create <team-name>[/yellow]")
        console.print("[dim]Example: /team create \"My Project Team\"[/dim]")
        return {}

    team_name = args.strip().strip('"').strip("'")

    # Get display name
    import socket
    hostname = socket.gethostname()
    username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    display_name = f"{username}@{hostname}"

    try:
        response = httpx.post(
            f"{client.base_url}/api/multiuser/team/create",
            json={
                "name": team_name,
                "user_id": user_id,
                "display_name": display_name,
            },
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            team_id = data.get("team_id", "")
            invite_code = data.get("invite_code", "")

            console.print()
            console.print(Panel(
                f"[bold green]Team created![/bold green]\n\n"
                f"[bold]Name:[/bold] {escape(team_name)}\n"
                f"[bold]Team ID:[/bold] [dim]{team_id[:12]}...[/dim]\n"
                f"[bold]Invite code:[/bold] [cyan]{invite_code}[/cyan]\n\n"
                f"Share this invite code with team members.\n"
                f"They can join with: [dim]/team join {invite_code}[/dim]\n\n"
                f"[dim]Tip: Set EMDASH_TEAM_ID={team_id} to use as default[/dim]",
                title="👥 Team Created",
                border_style="green",
            ))
            console.print()

            return {
                "team_id": team_id,
                "invite_code": invite_code,
                "name": team_name,
            }
        else:
            console.print(f"[red]Failed to create team: {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error creating team: {e}[/red]")
        return {}


def handle_team_join(args: str, client, user_id: str) -> dict:
    """Handle /team join <invite-code> command."""
    import httpx

    if not args:
        console.print("[yellow]Usage: /team join <invite-code>[/yellow]")
        console.print("[dim]Example: /team join T-ABC12345[/dim]")
        return {}

    invite_code = args.strip().upper()

    # Get display name
    import socket
    hostname = socket.gethostname()
    username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    display_name = f"{username}@{hostname}"

    try:
        response = httpx.post(
            f"{client.base_url}/api/multiuser/team/join",
            json={
                "invite_code": invite_code,
                "user_id": user_id,
                "display_name": display_name,
            },
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            team_id = data.get("team_id", "")
            team_name = data.get("name", "")
            member_count = data.get("member_count", 1)

            console.print()
            console.print(Panel(
                f"[bold green]Joined team![/bold green]\n\n"
                f"[bold]Name:[/bold] {escape(team_name)}\n"
                f"[bold]Members:[/bold] {member_count}\n\n"
                f"Use [cyan]/team sessions[/cyan] to see team sessions.\n"
                f"Use [cyan]/team join-session <id>[/cyan] to join one.",
                title="✓ Joined Team",
                border_style="green",
            ))
            console.print()

            return {
                "team_id": team_id,
                "name": team_name,
            }

        elif response.status_code == 404:
            console.print(f"[red]Invalid team invite code: {invite_code}[/red]")
            return {}
        else:
            console.print(f"[red]Failed to join team: {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error joining team: {e}[/red]")
        return {}


def handle_team_leave(args: str, client, user_id: str) -> dict:
    """Handle /team leave [team-id] command."""
    import httpx

    team_id = args.strip() if args else get_default_team_id()
    if not team_id:
        console.print("[yellow]Usage: /team leave <team-id>[/yellow]")
        console.print("[dim]Or set EMDASH_TEAM_ID environment variable[/dim]")
        return {}

    try:
        response = httpx.post(
            f"{client.base_url}/api/multiuser/team/{team_id}/leave",
            json={"user_id": user_id},
            timeout=30.0,
        )

        if response.status_code == 200:
            console.print("[green]Left the team.[/green]")
            return {"success": True}
        elif response.status_code == 404:
            console.print("[yellow]Team not found.[/yellow]")
            return {}
        else:
            console.print(f"[red]Failed to leave team: {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error leaving team: {e}[/red]")
        return {}


def handle_team_list(args: str, client, user_id: str) -> dict:
    """Handle /team list command."""
    import httpx

    try:
        response = httpx.get(
            f"{client.base_url}/api/multiuser/teams",
            params={"user_id": user_id},
            timeout=30.0,
        )

        if response.status_code == 200:
            teams = response.json()

            if not teams:
                console.print()
                console.print("[dim]You are not a member of any teams.[/dim]")
                console.print("[dim]Create one with: /team create <name>[/dim]")
                console.print()
                return {"teams": []}

            default_team = get_default_team_id()

            table = Table(title="Your Teams", show_header=True)
            table.add_column("Name", style="cyan")
            table.add_column("Role", style="yellow")
            table.add_column("Members", style="green", justify="right")
            table.add_column("Team ID", style="dim")
            table.add_column("", style="dim")  # Default marker

            for team in teams:
                team_id = team.get("team_id", "")
                name = team.get("name", "Unknown")
                role = team.get("your_role", "member").title()
                members = str(team.get("member_count", 1))

                # Check if this is default team
                is_default = team_id == default_team
                default_marker = "⭐ default" if is_default else ""

                table.add_row(
                    name,
                    "👑 Admin" if role == "Admin" else role,
                    members,
                    f"{team_id[:12]}...",
                    default_marker,
                )

            console.print()
            console.print(table)
            console.print()

            return {"teams": teams}
        else:
            console.print(f"[red]Failed to list teams: {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error listing teams: {e}[/red]")
        return {}


def handle_team_sessions(args: str, client, user_id: str) -> dict:
    """Handle /team sessions [team-id] command."""
    import httpx

    team_id = args.strip() if args else get_default_team_id()
    if not team_id:
        console.print("[yellow]Usage: /team sessions <team-id>[/yellow]")
        console.print("[dim]Or set EMDASH_TEAM_ID environment variable[/dim]")
        return {}

    try:
        response = httpx.get(
            f"{client.base_url}/api/multiuser/team/{team_id}/sessions",
            params={"user_id": user_id},
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            sessions = data.get("sessions", [])
            team_name = data.get("team_name", "Team")

            if not sessions:
                console.print()
                console.print(f"[dim]No sessions in {escape(team_name)} yet.[/dim]")
                console.print("[dim]Add your session with: /team add[/dim]")
                console.print()
                return {"sessions": []}

            table = Table(title=f"Sessions in {team_name}", show_header=True)
            table.add_column("Title", style="cyan")
            table.add_column("Owner", style="yellow")
            table.add_column("Participants", style="green", justify="right")
            table.add_column("Status", style="dim")
            table.add_column("Session ID", style="dim")

            for session in sessions:
                session_id = session.get("session_id", "")
                title = session.get("title", "Untitled")[:30]
                owner = session.get("owner_name", "Unknown")
                participants = str(session.get("participant_count", 1))
                is_active = session.get("is_active", False)
                status = "🟢 Active" if is_active else "⚪ Inactive"

                table.add_row(
                    title,
                    owner,
                    participants,
                    status,
                    f"{session_id[:12]}...",
                )

            console.print()
            console.print(table)
            console.print()
            console.print("[dim]Join with: /team join-session <session-id>[/dim]")
            console.print()

            return {"sessions": sessions}

        elif response.status_code == 403:
            console.print("[yellow]You are not a member of this team.[/yellow]")
            return {}
        elif response.status_code == 404:
            console.print("[yellow]Team not found.[/yellow]")
            return {}
        else:
            console.print(f"[red]Failed to list sessions: {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error listing sessions: {e}[/red]")
        return {}


def handle_team_add_session(args: str, client, session_id: str, user_id: str) -> dict:
    """Handle /team add [session-id] command to add session to team."""
    import httpx

    # Get team ID from default or we need to ask
    team_id = get_default_team_id()
    if not team_id:
        console.print("[yellow]No default team set.[/yellow]")
        console.print("[dim]Set EMDASH_TEAM_ID or use: /team add --team=<team-id>[/dim]")
        return {}

    # Use provided session ID or current session
    target_session = args.strip() if args else session_id
    if not target_session:
        console.print("[yellow]Not in a shared session and no session ID provided.[/yellow]")
        console.print("[dim]First /share your session, then /team add[/dim]")
        return {}

    # Optional title
    title = None

    try:
        response = httpx.post(
            f"{client.base_url}/api/multiuser/team/{team_id}/add-session",
            json={
                "session_id": target_session,
                "user_id": user_id,
                "title": title,
            },
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            team_name = data.get("team_name", "team")

            console.print()
            console.print(Panel(
                f"[bold green]Session added to {escape(team_name)}![/bold green]\n\n"
                f"Team members can now see and join this session.\n"
                f"[dim]They can use: /team sessions[/dim]",
                title="✓ Added to Team",
                border_style="green",
            ))
            console.print()

            return {"success": True}

        elif response.status_code == 403:
            console.print("[yellow]You must be the session owner or team admin.[/yellow]")
            return {}
        elif response.status_code == 404:
            console.print("[yellow]Session or team not found.[/yellow]")
            return {}
        else:
            console.print(f"[red]Failed to add session: {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error adding session: {e}[/red]")
        return {}


def handle_team_join_session(args: str, client, user_id: str) -> dict:
    """Handle /team join-session <session-id> command."""
    import httpx

    if not args:
        console.print("[yellow]Usage: /team join-session <session-id>[/yellow]")
        console.print("[dim]See sessions with: /team sessions[/dim]")
        return {}

    parts = args.strip().split()
    target_session = parts[0]

    # Get team ID - required for joining team session
    team_id = get_default_team_id()
    if not team_id:
        console.print("[yellow]No default team set.[/yellow]")
        console.print("[dim]Set EMDASH_TEAM_ID environment variable[/dim]")
        return {}

    # Get display name
    import socket
    hostname = socket.gethostname()
    username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    display_name = f"{username}@{hostname}"

    try:
        response = httpx.post(
            f"{client.base_url}/api/multiuser/team/{team_id}/join-session",
            json={
                "session_id": target_session,
                "user_id": user_id,
                "display_name": display_name,
            },
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id", target_session)
            title = data.get("title", "Untitled")
            participants = data.get("participants", [])

            console.print()
            console.print(Panel(
                f"[bold green]Joined team session![/bold green]\n\n"
                f"[bold]Title:[/bold] {escape(title)}\n"
                f"[bold]Participants:[/bold] {len(participants)}\n\n"
                f"[dim]Use /who to see participants[/dim]",
                title="✓ Joined Session",
                border_style="green",
            ))
            console.print()

            return {
                "session_id": session_id,
                "participants": participants,
            }

        elif response.status_code == 403:
            console.print("[yellow]You must be a team member to join team sessions.[/yellow]")
            return {}
        elif response.status_code == 404:
            console.print("[yellow]Session not found or not in this team.[/yellow]")
            return {}
        else:
            console.print(f"[red]Failed to join session: {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error joining session: {e}[/red]")
        return {}


def handle_team_info(args: str, client, user_id: str) -> dict:
    """Handle /team info [team-id] command."""
    import httpx

    team_id = args.strip() if args else get_default_team_id()
    if not team_id:
        console.print("[yellow]Usage: /team info <team-id>[/yellow]")
        console.print("[dim]Or set EMDASH_TEAM_ID environment variable[/dim]")
        return {}

    try:
        response = httpx.get(
            f"{client.base_url}/api/multiuser/team/{team_id}",
            params={"user_id": user_id},
            timeout=30.0,
        )

        if response.status_code == 200:
            team = response.json()
            name = team.get("name", "Unknown")
            description = team.get("description", "")
            invite_code = team.get("invite_code", "")
            members = team.get("members", [])
            session_count = team.get("session_count", 0)
            your_role = team.get("your_role", "member")

            # Build members list
            member_lines = []
            for m in members[:5]:  # Show first 5
                role_icon = "👑 " if m.get("role") == "admin" else ""
                member_lines.append(f"  {role_icon}{m.get('display_name', 'Unknown')}")
            if len(members) > 5:
                member_lines.append(f"  ... and {len(members) - 5} more")

            console.print()
            console.print(Panel(
                f"[bold]{escape(name)}[/bold]\n"
                + (f"[dim]{escape(description)}[/dim]\n" if description else "")
                + f"\n[bold]Invite code:[/bold] [cyan]{invite_code}[/cyan]\n"
                + f"[bold]Your role:[/bold] {your_role.title()}\n"
                + f"[bold]Sessions:[/bold] {session_count}\n"
                + f"[bold]Members ({len(members)}):[/bold]\n"
                + "\n".join(member_lines),
                title="👥 Team Info",
                border_style="blue",
            ))
            console.print()

            return team
        elif response.status_code == 403:
            console.print("[yellow]You are not a member of this team.[/yellow]")
            return {}
        elif response.status_code == 404:
            console.print("[yellow]Team not found.[/yellow]")
            return {}
        else:
            console.print(f"[red]Failed to get team info: {response.text}[/red]")
            return {}

    except Exception as e:
        console.print(f"[red]Error getting team info: {e}[/red]")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Registry Commands
# ─────────────────────────────────────────────────────────────────────────────


def handle_registry(args: str, client, user_id: str) -> dict:
    """Handle /registry command and subcommands.

    Subcommands:
        /registry rules [list|add|remove|show]   - Manage prompt rules
        /registry agents [list|add|remove|show]  - Manage agent configs
        /registry mcps [list|add|remove|show]    - Manage MCP configs
        /registry skills [list|add|remove|show]  - Manage skills
        /registry sync                           - Sync registry with remote
        /registry export                         - Export registry to JSON
        /registry import <file>                  - Import registry from JSON

    Args:
        args: Subcommand and arguments
        client: API client
        user_id: Current user ID

    Returns:
        Dict with result info
    """
    parts = args.strip().split(maxsplit=2)
    subcommand = parts[0].lower() if parts else ""
    action = parts[1].lower() if len(parts) > 1 else "list"
    subargs = parts[2] if len(parts) > 2 else ""

    if not subcommand:
        _show_registry_help()
        return {}

    team_id = get_default_team_id()
    if not team_id and subcommand not in ("help",):
        console.print("[yellow]No default team set.[/yellow]")
        console.print("[dim]Set EMDASH_TEAM_ID environment variable[/dim]")
        return {}

    if subcommand in ("rules", "rule"):
        return handle_registry_rules(action, subargs, client, team_id, user_id)
    elif subcommand in ("agents", "agent"):
        return handle_registry_agents(action, subargs, client, team_id, user_id)
    elif subcommand in ("mcps", "mcp"):
        return handle_registry_mcps(action, subargs, client, team_id, user_id)
    elif subcommand in ("skills", "skill"):
        return handle_registry_skills(action, subargs, client, team_id, user_id)
    elif subcommand == "sync":
        return handle_registry_sync(subargs, client, team_id, user_id)
    elif subcommand == "export":
        return handle_registry_export(subargs, client, team_id, user_id)
    elif subcommand == "import":
        return handle_registry_import(action + " " + subargs, client, team_id, user_id)
    elif subcommand == "help":
        _show_registry_help()
        return {}
    else:
        console.print(f"[yellow]Unknown registry subcommand: {subcommand}[/yellow]")
        _show_registry_help()
        return {}


def _show_registry_help() -> None:
    """Show help for registry commands."""
    console.print()
    console.print(Panel(
        "[bold]Team Registry Commands[/bold]\n\n"
        "[bold cyan]Rules (prompt guidelines):[/bold cyan]\n"
        "  [cyan]/registry rules[/cyan]              - List all rules\n"
        "  [cyan]/registry rules add <name>[/cyan]   - Add a rule (opens editor)\n"
        "  [cyan]/registry rules show <name>[/cyan]  - Show rule details\n"
        "  [cyan]/registry rules remove <id>[/cyan]  - Remove a rule\n\n"
        "[bold cyan]Agents (pre-configured agents):[/bold cyan]\n"
        "  [cyan]/registry agents[/cyan]             - List all agents\n"
        "  [cyan]/registry agents add <name>[/cyan]  - Add an agent config\n"
        "  [cyan]/registry agents show <name>[/cyan] - Show agent details\n"
        "  [cyan]/registry agents remove <id>[/cyan] - Remove an agent\n\n"
        "[bold cyan]MCPs (MCP server configs):[/bold cyan]\n"
        "  [cyan]/registry mcps[/cyan]               - List all MCPs\n"
        "  [cyan]/registry mcps add <name>[/cyan]    - Add an MCP config\n"
        "  [cyan]/registry mcps show <name>[/cyan]   - Show MCP details\n"
        "  [cyan]/registry mcps remove <id>[/cyan]   - Remove an MCP\n\n"
        "[bold cyan]Skills (prompt templates):[/bold cyan]\n"
        "  [cyan]/registry skills[/cyan]             - List all skills\n"
        "  [cyan]/registry skills add <name>[/cyan]  - Add a skill\n"
        "  [cyan]/registry skills show <name>[/cyan] - Show skill details\n"
        "  [cyan]/registry skills remove <id>[/cyan] - Remove a skill\n\n"
        "[bold cyan]Other:[/bold cyan]\n"
        "  [cyan]/registry sync[/cyan]               - Sync with remote\n"
        "  [cyan]/registry export[/cyan]             - Export to JSON\n"
        "  [cyan]/registry import <file>[/cyan]      - Import from JSON\n",
        title="📚 Registry Help",
        border_style="blue",
    ))
    console.print()


def handle_registry_rules(action: str, args: str, client, team_id: str, user_id: str) -> dict:
    """Handle /registry rules subcommands."""
    import httpx

    if action == "list" or not action:
        try:
            response = httpx.get(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/rules",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                rules = response.json()

                if not rules:
                    console.print()
                    console.print("[dim]No rules defined for this team.[/dim]")
                    console.print("[dim]Add one with: /registry rules add <name>[/dim]")
                    console.print()
                    return {"rules": []}

                table = Table(title="Team Rules", show_header=True)
                table.add_column("Name", style="cyan")
                table.add_column("Priority", style="yellow", justify="right")
                table.add_column("Status", style="green")
                table.add_column("Tags", style="dim")

                for rule in rules:
                    status = "✓ Enabled" if rule.get("enabled", True) else "○ Disabled"
                    tags = ", ".join(rule.get("tags", [])[:3])
                    if len(rule.get("tags", [])) > 3:
                        tags += "..."

                    table.add_row(
                        rule.get("name", "Unknown"),
                        str(rule.get("priority", 0)),
                        status,
                        tags or "-",
                    )

                console.print()
                console.print(table)
                console.print()
                return {"rules": rules}
            else:
                console.print(f"[red]Failed to list rules: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error listing rules: {e}[/red]")
            return {}

    elif action == "add":
        name = args.strip()
        if not name:
            console.print("[yellow]Usage: /registry rules add <rule-name>[/yellow]")
            return {}

        # For now, prompt for content inline
        console.print(f"[dim]Adding rule: {name}[/dim]")
        console.print("[yellow]Enter rule content (end with empty line):[/yellow]")

        lines = []
        try:
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
        except EOFError:
            pass

        content = "\n".join(lines)
        if not content:
            console.print("[yellow]No content provided. Rule not added.[/yellow]")
            return {}

        try:
            response = httpx.post(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/rules",
                json={
                    "user_id": user_id,
                    "name": name,
                    "content": content,
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]Rule '{name}' added![/green]")
                return data
            else:
                console.print(f"[red]Failed to add rule: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error adding rule: {e}[/red]")
            return {}

    elif action == "show":
        name = args.strip()
        if not name:
            console.print("[yellow]Usage: /registry rules show <rule-name>[/yellow]")
            return {}

        try:
            response = httpx.get(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/rules/{name}",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                rule = response.json()

                console.print()
                console.print(Panel(
                    f"[bold]Name:[/bold] {escape(rule.get('name', ''))}\n"
                    f"[bold]Priority:[/bold] {rule.get('priority', 0)}\n"
                    f"[bold]Enabled:[/bold] {'Yes' if rule.get('enabled', True) else 'No'}\n"
                    f"[bold]Tags:[/bold] {', '.join(rule.get('tags', [])) or 'None'}\n"
                    f"[bold]Description:[/bold] {rule.get('description', 'None')}\n\n"
                    f"[bold]Content:[/bold]\n{escape(rule.get('content', ''))}",
                    title="📋 Rule Details",
                    border_style="blue",
                ))
                console.print()
                return rule
            elif response.status_code == 404:
                console.print(f"[yellow]Rule '{name}' not found.[/yellow]")
                return {}
            else:
                console.print(f"[red]Failed to get rule: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error getting rule: {e}[/red]")
            return {}

    elif action == "remove":
        rule_id = args.strip()
        if not rule_id:
            console.print("[yellow]Usage: /registry rules remove <rule-id-or-name>[/yellow]")
            return {}

        try:
            response = httpx.delete(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/rules/{rule_id}",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                console.print(f"[green]Rule removed.[/green]")
                return {"success": True}
            elif response.status_code == 404:
                console.print(f"[yellow]Rule '{rule_id}' not found.[/yellow]")
                return {}
            else:
                console.print(f"[red]Failed to remove rule: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error removing rule: {e}[/red]")
            return {}

    else:
        console.print(f"[yellow]Unknown action: {action}[/yellow]")
        console.print("[dim]Available: list, add, show, remove[/dim]")
        return {}


def handle_registry_agents(action: str, args: str, client, team_id: str, user_id: str) -> dict:
    """Handle /registry agents subcommands."""
    import httpx

    if action == "list" or not action:
        try:
            response = httpx.get(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/agents",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                agents = response.json()

                if not agents:
                    console.print()
                    console.print("[dim]No agent configs defined for this team.[/dim]")
                    console.print("[dim]Add one with: /registry agents add <name>[/dim]")
                    console.print()
                    return {"agents": []}

                table = Table(title="Team Agents", show_header=True)
                table.add_column("Name", style="cyan")
                table.add_column("Model", style="yellow")
                table.add_column("Tools", style="green", justify="right")
                table.add_column("Status", style="dim")

                for agent in agents:
                    status = "✓ Enabled" if agent.get("enabled", True) else "○ Disabled"
                    tools_count = len(agent.get("tools", []))

                    table.add_row(
                        agent.get("name", "Unknown"),
                        agent.get("model", "default") or "default",
                        str(tools_count),
                        status,
                    )

                console.print()
                console.print(table)
                console.print()
                return {"agents": agents}
            else:
                console.print(f"[red]Failed to list agents: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error listing agents: {e}[/red]")
            return {}

    elif action == "add":
        name = args.strip()
        if not name:
            console.print("[yellow]Usage: /registry agents add <agent-name>[/yellow]")
            return {}

        # Interactive prompts for agent config
        console.print(f"[dim]Adding agent config: {name}[/dim]")

        model = input("Model (e.g., claude-3-opus, leave empty for default): ").strip()

        console.print("Enter system prompt (end with empty line):")
        lines = []
        try:
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
        except EOFError:
            pass
        system_prompt = "\n".join(lines)

        try:
            response = httpx.post(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/agents",
                json={
                    "user_id": user_id,
                    "name": name,
                    "model": model,
                    "system_prompt": system_prompt,
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]Agent config '{name}' added![/green]")
                return data
            else:
                console.print(f"[red]Failed to add agent: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error adding agent: {e}[/red]")
            return {}

    elif action == "show":
        name = args.strip()
        if not name:
            console.print("[yellow]Usage: /registry agents show <agent-name>[/yellow]")
            return {}

        try:
            response = httpx.get(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/agents/{name}",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                agent = response.json()

                tools_str = ", ".join(agent.get("tools", [])) or "None"

                console.print()
                console.print(Panel(
                    f"[bold]Name:[/bold] {escape(agent.get('name', ''))}\n"
                    f"[bold]Model:[/bold] {agent.get('model', 'default') or 'default'}\n"
                    f"[bold]Enabled:[/bold] {'Yes' if agent.get('enabled', True) else 'No'}\n"
                    f"[bold]Tools:[/bold] {tools_str}\n"
                    f"[bold]Description:[/bold] {agent.get('description', 'None')}\n\n"
                    f"[bold]System Prompt:[/bold]\n{escape(agent.get('system_prompt', '')[:500])}{'...' if len(agent.get('system_prompt', '')) > 500 else ''}",
                    title="🤖 Agent Details",
                    border_style="blue",
                ))
                console.print()
                return agent
            elif response.status_code == 404:
                console.print(f"[yellow]Agent '{name}' not found.[/yellow]")
                return {}
            else:
                console.print(f"[red]Failed to get agent: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error getting agent: {e}[/red]")
            return {}

    elif action == "remove":
        agent_id = args.strip()
        if not agent_id:
            console.print("[yellow]Usage: /registry agents remove <agent-id-or-name>[/yellow]")
            return {}

        try:
            response = httpx.delete(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/agents/{agent_id}",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                console.print(f"[green]Agent config removed.[/green]")
                return {"success": True}
            elif response.status_code == 404:
                console.print(f"[yellow]Agent '{agent_id}' not found.[/yellow]")
                return {}
            else:
                console.print(f"[red]Failed to remove agent: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error removing agent: {e}[/red]")
            return {}

    else:
        console.print(f"[yellow]Unknown action: {action}[/yellow]")
        console.print("[dim]Available: list, add, show, remove[/dim]")
        return {}


def handle_registry_mcps(action: str, args: str, client, team_id: str, user_id: str) -> dict:
    """Handle /registry mcps subcommands."""
    import httpx

    if action == "list" or not action:
        try:
            response = httpx.get(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/mcps",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                mcps = response.json()

                if not mcps:
                    console.print()
                    console.print("[dim]No MCP configs defined for this team.[/dim]")
                    console.print("[dim]Add one with: /registry mcps add <name>[/dim]")
                    console.print()
                    return {"mcps": []}

                table = Table(title="Team MCPs", show_header=True)
                table.add_column("Name", style="cyan")
                table.add_column("Command", style="yellow")
                table.add_column("Auto-start", style="green")
                table.add_column("Status", style="dim")

                for mcp in mcps:
                    status = "✓ Enabled" if mcp.get("enabled", True) else "○ Disabled"
                    auto_start = "Yes" if mcp.get("auto_start", False) else "No"
                    command = mcp.get("command", "")[:30]

                    table.add_row(
                        mcp.get("name", "Unknown"),
                        command,
                        auto_start,
                        status,
                    )

                console.print()
                console.print(table)
                console.print()
                return {"mcps": mcps}
            else:
                console.print(f"[red]Failed to list MCPs: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error listing MCPs: {e}[/red]")
            return {}

    elif action == "add":
        name = args.strip()
        if not name:
            console.print("[yellow]Usage: /registry mcps add <mcp-name>[/yellow]")
            return {}

        console.print(f"[dim]Adding MCP config: {name}[/dim]")

        command = input("Command (e.g., npx, uvx): ").strip()
        args_str = input("Arguments (space-separated): ").strip()
        auto_start = input("Auto-start with sessions? (y/n): ").strip().lower() == "y"

        try:
            response = httpx.post(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/mcps",
                json={
                    "user_id": user_id,
                    "name": name,
                    "command": command,
                    "args": args_str.split() if args_str else [],
                    "auto_start": auto_start,
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]MCP config '{name}' added![/green]")
                return data
            else:
                console.print(f"[red]Failed to add MCP: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error adding MCP: {e}[/red]")
            return {}

    elif action == "show":
        name = args.strip()
        if not name:
            console.print("[yellow]Usage: /registry mcps show <mcp-name>[/yellow]")
            return {}

        try:
            response = httpx.get(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/mcps/{name}",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                mcp = response.json()

                args_str = " ".join(mcp.get("args", []))
                env_str = "\n  ".join(f"{k}={v}" for k, v in mcp.get("env", {}).items()) or "None"

                console.print()
                console.print(Panel(
                    f"[bold]Name:[/bold] {escape(mcp.get('name', ''))}\n"
                    f"[bold]Command:[/bold] {mcp.get('command', '')}\n"
                    f"[bold]Arguments:[/bold] {args_str or 'None'}\n"
                    f"[bold]Auto-start:[/bold] {'Yes' if mcp.get('auto_start', False) else 'No'}\n"
                    f"[bold]Enabled:[/bold] {'Yes' if mcp.get('enabled', True) else 'No'}\n"
                    f"[bold]Description:[/bold] {mcp.get('description', 'None')}\n"
                    f"[bold]Environment:[/bold]\n  {env_str}",
                    title="🔌 MCP Details",
                    border_style="blue",
                ))
                console.print()
                return mcp
            elif response.status_code == 404:
                console.print(f"[yellow]MCP '{name}' not found.[/yellow]")
                return {}
            else:
                console.print(f"[red]Failed to get MCP: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error getting MCP: {e}[/red]")
            return {}

    elif action == "remove":
        mcp_id = args.strip()
        if not mcp_id:
            console.print("[yellow]Usage: /registry mcps remove <mcp-id-or-name>[/yellow]")
            return {}

        try:
            response = httpx.delete(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/mcps/{mcp_id}",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                console.print(f"[green]MCP config removed.[/green]")
                return {"success": True}
            elif response.status_code == 404:
                console.print(f"[yellow]MCP '{mcp_id}' not found.[/yellow]")
                return {}
            else:
                console.print(f"[red]Failed to remove MCP: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error removing MCP: {e}[/red]")
            return {}

    else:
        console.print(f"[yellow]Unknown action: {action}[/yellow]")
        console.print("[dim]Available: list, add, show, remove[/dim]")
        return {}


def handle_registry_skills(action: str, args: str, client, team_id: str, user_id: str) -> dict:
    """Handle /registry skills subcommands."""
    import httpx

    if action == "list" or not action:
        try:
            response = httpx.get(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/skills",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                skills = response.json()

                if not skills:
                    console.print()
                    console.print("[dim]No skills defined for this team.[/dim]")
                    console.print("[dim]Add one with: /registry skills add <name>[/dim]")
                    console.print()
                    return {"skills": []}

                table = Table(title="Team Skills", show_header=True)
                table.add_column("Name", style="cyan")
                table.add_column("Variables", style="yellow")
                table.add_column("Tags", style="green")
                table.add_column("Status", style="dim")

                for skill in skills:
                    status = "✓ Enabled" if skill.get("enabled", True) else "○ Disabled"
                    vars_str = ", ".join(skill.get("variables", [])[:3])
                    if len(skill.get("variables", [])) > 3:
                        vars_str += "..."
                    tags_str = ", ".join(skill.get("tags", [])[:2])

                    table.add_row(
                        skill.get("name", "Unknown"),
                        vars_str or "None",
                        tags_str or "-",
                        status,
                    )

                console.print()
                console.print(table)
                console.print()
                return {"skills": skills}
            else:
                console.print(f"[red]Failed to list skills: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error listing skills: {e}[/red]")
            return {}

    elif action == "add":
        name = args.strip()
        if not name:
            console.print("[yellow]Usage: /registry skills add <skill-name>[/yellow]")
            return {}

        console.print(f"[dim]Adding skill: {name}[/dim]")
        console.print("[dim]Use {{variable}} for placeholders[/dim]")
        console.print("Enter prompt template (end with empty line):")

        lines = []
        try:
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
        except EOFError:
            pass

        prompt_template = "\n".join(lines)
        if not prompt_template:
            console.print("[yellow]No template provided. Skill not added.[/yellow]")
            return {}

        try:
            response = httpx.post(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/skills",
                json={
                    "user_id": user_id,
                    "name": name,
                    "prompt_template": prompt_template,
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                console.print(f"[green]Skill '{name}' added![/green]")
                return data
            else:
                console.print(f"[red]Failed to add skill: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error adding skill: {e}[/red]")
            return {}

    elif action == "show":
        name = args.strip()
        if not name:
            console.print("[yellow]Usage: /registry skills show <skill-name>[/yellow]")
            return {}

        try:
            response = httpx.get(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/skills/{name}",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                skill = response.json()

                vars_str = ", ".join(skill.get("variables", [])) or "None"
                tags_str = ", ".join(skill.get("tags", [])) or "None"

                console.print()
                console.print(Panel(
                    f"[bold]Name:[/bold] {escape(skill.get('name', ''))}\n"
                    f"[bold]Variables:[/bold] {vars_str}\n"
                    f"[bold]Tags:[/bold] {tags_str}\n"
                    f"[bold]Enabled:[/bold] {'Yes' if skill.get('enabled', True) else 'No'}\n"
                    f"[bold]Description:[/bold] {skill.get('description', 'None')}\n\n"
                    f"[bold]Prompt Template:[/bold]\n{escape(skill.get('prompt_template', ''))}",
                    title="⚡ Skill Details",
                    border_style="blue",
                ))
                console.print()

                # Show examples if any
                examples = skill.get("examples", [])
                if examples:
                    console.print("[bold]Examples:[/bold]")
                    for i, ex in enumerate(examples[:2], 1):
                        console.print(f"  {i}. Input: {ex.get('input', '')}")
                        console.print(f"     Output: {ex.get('output', '')[:50]}...")
                    console.print()

                return skill
            elif response.status_code == 404:
                console.print(f"[yellow]Skill '{name}' not found.[/yellow]")
                return {}
            else:
                console.print(f"[red]Failed to get skill: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error getting skill: {e}[/red]")
            return {}

    elif action == "remove":
        skill_id = args.strip()
        if not skill_id:
            console.print("[yellow]Usage: /registry skills remove <skill-id-or-name>[/yellow]")
            return {}

        try:
            response = httpx.delete(
                f"{client.base_url}/api/multiuser/team/{team_id}/registry/skills/{skill_id}",
                params={"user_id": user_id},
                timeout=30.0,
            )

            if response.status_code == 200:
                console.print(f"[green]Skill removed.[/green]")
                return {"success": True}
            elif response.status_code == 404:
                console.print(f"[yellow]Skill '{skill_id}' not found.[/yellow]")
                return {}
            else:
                console.print(f"[red]Failed to remove skill: {response.text}[/red]")
                return {}
        except Exception as e:
            console.print(f"[red]Error removing skill: {e}[/red]")
            return {}

    else:
        console.print(f"[yellow]Unknown action: {action}[/yellow]")
        console.print("[dim]Available: list, add, show, remove[/dim]")
        return {}


def handle_registry_sync(args: str, client, team_id: str, user_id: str) -> dict:
    """Handle /registry sync command."""
    import httpx

    strategy = args.strip() if args else "remote_wins"
    if strategy not in ("remote_wins", "local_wins", "merge"):
        console.print("[yellow]Strategy must be: remote_wins, local_wins, or merge[/yellow]")
        return {}

    try:
        response = httpx.post(
            f"{client.base_url}/api/multiuser/team/{team_id}/registry/sync",
            json={
                "user_id": user_id,
                "strategy": strategy,
            },
            timeout=60.0,
        )

        if response.status_code == 200:
            data = response.json()
            console.print()
            console.print(Panel(
                f"[bold green]Registry synced![/bold green]\n\n"
                f"Strategy: {strategy}\n"
                f"Rules: {data.get('rules_count', 0)}\n"
                f"Agents: {data.get('agents_count', 0)}\n"
                f"MCPs: {data.get('mcps_count', 0)}\n"
                f"Skills: {data.get('skills_count', 0)}",
                title="✓ Sync Complete",
                border_style="green",
            ))
            console.print()
            return data
        else:
            console.print(f"[red]Failed to sync registry: {response.text}[/red]")
            return {}
    except Exception as e:
        console.print(f"[red]Error syncing registry: {e}[/red]")
        return {}


def handle_registry_export(args: str, client, team_id: str, user_id: str) -> dict:
    """Handle /registry export command."""
    import httpx
    import json

    output_file = args.strip() if args else f"registry_{team_id[:8]}.json"

    try:
        response = httpx.get(
            f"{client.base_url}/api/multiuser/team/{team_id}/registry",
            params={"user_id": user_id},
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()

            # Write to file
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            console.print(f"[green]Registry exported to {output_file}[/green]")
            return {"file": output_file}
        else:
            console.print(f"[red]Failed to export registry: {response.text}[/red]")
            return {}
    except Exception as e:
        console.print(f"[red]Error exporting registry: {e}[/red]")
        return {}


def handle_registry_import(args: str, client, team_id: str, user_id: str) -> dict:
    """Handle /registry import <file> command."""
    import httpx
    import json

    input_file = args.strip()
    if not input_file:
        console.print("[yellow]Usage: /registry import <file.json>[/yellow]")
        return {}

    try:
        with open(input_file, "r") as f:
            data = json.load(f)

        response = httpx.post(
            f"{client.base_url}/api/multiuser/team/{team_id}/registry/import",
            json={
                "user_id": user_id,
                "registry": data,
                "merge": True,  # Default to merging
            },
            timeout=60.0,
        )

        if response.status_code == 200:
            result = response.json()
            console.print()
            console.print(Panel(
                f"[bold green]Registry imported![/bold green]\n\n"
                f"Rules: {result.get('rules_count', 0)}\n"
                f"Agents: {result.get('agents_count', 0)}\n"
                f"MCPs: {result.get('mcps_count', 0)}\n"
                f"Skills: {result.get('skills_count', 0)}",
                title="✓ Import Complete",
                border_style="green",
            ))
            console.print()
            return result
        else:
            console.print(f"[red]Failed to import registry: {response.text}[/red]")
            return {}
    except FileNotFoundError:
        console.print(f"[red]File not found: {input_file}[/red]")
        return {}
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON file: {e}[/red]")
        return {}
    except Exception as e:
        console.print(f"[red]Error importing registry: {e}[/red]")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Multiuser Config Command
# ─────────────────────────────────────────────────────────────────────────────


def handle_multiuser_config(args: str) -> None:
    """Handle /multiuser command to show multiuser configuration.

    Shows current multiuser settings including provider type, enabled status,
    and provider-specific configuration.

    Args:
        args: Optional subcommand (currently unused, reserved for future use)
    """
    from pathlib import Path

    # Read environment variables
    enabled = os.environ.get("EMDASH_MULTIUSER_ENABLED", "false").lower() in ("true", "1", "yes")
    provider_env = os.environ.get("EMDASH_MULTIUSER_PROVIDER", "").lower()
    storage = os.environ.get("EMDASH_MULTIUSER_STORAGE", str(Path.home() / ".emdash" / "multiuser"))

    # Firebase config
    firebase_project = os.environ.get("FIREBASE_PROJECT_ID", "")
    firebase_db_url = os.environ.get("FIREBASE_DATABASE_URL", "")
    firebase_creds = os.environ.get("FIREBASE_CREDENTIALS_PATH", "")
    firebase_api_key = os.environ.get("FIREBASE_API_KEY", "")

    # Determine actual provider (matches create_sync logic)
    # - "firebase": uses Firebase
    # - "local": uses local files
    # - unset: Firebase if FIREBASE_DATABASE_URL is set, else local
    if provider_env == "firebase" or (not provider_env and firebase_db_url):
        provider = "firebase"
    else:
        provider = "local"

    # Build provider details
    if provider == "firebase":
        provider_type = "Firebase Realtime Database"
        provider_details = [
            f"[bold]Project ID:[/bold] {firebase_project or '[dim](not set)[/dim]'}",
            f"[bold]Database URL:[/bold] {firebase_db_url or '[dim](not set)[/dim]'}",
        ]
        if firebase_creds:
            provider_details.append(f"[bold]Credentials:[/bold] {firebase_creds}")
        elif firebase_api_key:
            provider_details.append("[bold]Credentials:[/bold] Using API key")
        else:
            provider_details.append("[bold]Credentials:[/bold] [yellow](not configured)[/yellow]")

        # Validation
        if not firebase_db_url:
            provider_details.append("")
            provider_details.append("[yellow]⚠ Missing FIREBASE_DATABASE_URL[/yellow]")
        if not firebase_creds and not firebase_api_key:
            provider_details.append("[yellow]⚠ Missing credentials (FIREBASE_CREDENTIALS_PATH or FIREBASE_API_KEY)[/yellow]")
    else:
        provider_type = "Local File Storage"
        provider_details = [
            f"[bold]Storage Path:[/bold] {storage}",
            "[dim]File-based sync for single-machine, multi-process use[/dim]",
            "[dim]Note: Does not support multi-machine sync[/dim]",
        ]

    # Build status indicators
    enabled_indicator = "[green]● Enabled[/green]" if enabled else "[dim]○ Disabled[/dim]"
    if provider == "firebase":
        if provider_env == "firebase":
            provider_indicator = "[cyan]firebase[/cyan]"
        else:
            provider_indicator = "[cyan]firebase[/cyan] [dim](auto-detected: FIREBASE_DATABASE_URL is set)[/dim]"
    else:
        provider_indicator = "[blue]local[/blue]"

    # Display
    console.print()
    console.print(Panel(
        f"[bold]Status:[/bold]   {enabled_indicator}\n"
        f"[bold]Provider:[/bold] {provider_indicator}\n\n"
        f"[bold underline]Provider Details ({provider_type})[/bold underline]\n"
        + "\n".join(provider_details),
        title="📡 Multiuser Settings",
        border_style="blue",
    ))
    console.print()

    # Show environment variable reference
    console.print("[dim]Environment Variables:[/dim]")
    console.print("[dim]  EMDASH_MULTIUSER_ENABLED   - Enable multiuser (true/false)[/dim]")
    console.print("[dim]  EMDASH_MULTIUSER_PROVIDER  - Provider type (local/firebase)[/dim]")
    console.print("[dim]  EMDASH_MULTIUSER_STORAGE   - Local storage path[/dim]")
    if provider == "firebase" or not enabled:
        console.print("[dim]  FIREBASE_PROJECT_ID        - Firebase project ID[/dim]")
        console.print("[dim]  FIREBASE_DATABASE_URL      - Firebase database URL[/dim]")
        console.print("[dim]  FIREBASE_CREDENTIALS_PATH  - Path to service account JSON[/dim]")
    console.print()

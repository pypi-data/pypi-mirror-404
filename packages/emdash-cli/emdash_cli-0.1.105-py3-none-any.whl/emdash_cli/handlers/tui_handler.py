"""TUI handler - connects the TUI to the EmDash agent via SSE."""

import json
import os
import re
from pathlib import Path
from typing import AsyncIterator

import httpx


def _update_env_model(new_model: str) -> None:
    """Update EMDASH_MODEL in the project .env file.

    Searches for .env in current directory or parent dirs (up to 5 levels).
    If no .env exists, creates one in the current directory.
    """
    # Find existing .env file
    env_path = None
    current = Path.cwd()
    for _ in range(5):
        candidate = current / ".env"
        if candidate.exists():
            env_path = candidate
            break
        current = current.parent

    # If no .env found, create one in cwd
    if env_path is None:
        env_path = Path.cwd() / ".env"

    # Read existing content
    content = ""
    if env_path.exists():
        content = env_path.read_text()

    # Update or add EMDASH_MODEL
    pattern = r'^EMDASH_MODEL=.*$'
    new_line = f'EMDASH_MODEL={new_model}'

    if re.search(pattern, content, re.MULTILINE):
        # Replace existing EMDASH_MODEL line
        content = re.sub(pattern, new_line, content, flags=re.MULTILINE)
    else:
        # Add new line (ensure newline before if file has content)
        if content and not content.endswith('\n'):
            content += '\n'
        content += new_line + '\n'

    env_path.write_text(content)


# Slash commands that have dedicated API endpoints
SLASH_COMMAND_ENDPOINTS = {
    "/stats": "stats",
    "/todos": "todos",
    "/compact": "compact",
    "/messages": "export",
    "/context": "context",
}


def create_agent_handler(
    model: str | None = None,
    mode: str = "code",
    max_iterations: int = 100,
):
    """Create an async handler that streams agent responses.

    This handler is a simple agent processor. In the decorator architecture:
    - Solo mode: StandardDecorator wraps this handler for direct passthrough
    - Shared mode: SharedDecorator handles multiuser logic via server

    The handler processes slash commands (/share, /join, /leave) which return
    multiuser_started/multiuser_stopped events to signal the bridge to switch
    decorators.

    Args:
        model: Model name to use
        mode: Agent mode (code or plan)
        max_iterations: Maximum agent iterations

    Returns:
        Async callable that takes a message and yields events.
        The handler has additional methods:
        - reset_session(): Clear session ID and user ID for new conversation
        - set_mode(mode): Change the agent mode
        - set_model(model): Change the model
        - get_session_id(): Get current session ID
        - get_user_id(): Get current multiuser user ID
        - approve_plan_mode(): Approve plan mode request (returns async iterator)
    """
    # Get server URL from server manager
    from ..server_manager import get_server_manager

    server = get_server_manager()
    server_url = server.get_server_url()

    # Track session ID for multi-turn conversations
    # session_id: from server after first /chat, used for /continue endpoint
    # local_identity_id: generated locally, used for project session linking
    import uuid
    session_id = None  # Set after first /chat response from server
    local_identity_id = f"local-{uuid.uuid4().hex[:12]}"  # For project linking
    current_mode = mode
    # Use EMDASH_MODEL env var if model not specified
    current_model = model or os.environ.get("EMDASH_MODEL", "claude-sonnet-4")
    multiuser_user_id = None  # User ID for multiuser sessions
    multiuser_session_id = None  # Shared session ID
    multiuser_is_owner = False  # Whether this user is the session owner
    multiuser_server_url = None  # Server URL for shared session

    async def _handle_slash_command(cmd: str) -> AsyncIterator[dict]:
        """Handle slash commands that have dedicated API endpoints."""
        nonlocal session_id, multiuser_user_id, multiuser_session_id, multiuser_is_owner, multiuser_server_url

        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # /stats - get session stats
                if command == "/stats":
                    if not session_id:
                        yield {"type": "response", "data": {"content": "No active session. Send a message first."}}
                        return
                    url = f"{server_url}/api/agent/chat/{session_id}/stats"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    content = f"""**Session Stats**

- Model: `{data.get('model', 'unknown')}`
- Input tokens: {data.get('input_tokens', 0):,}
- Output tokens: {data.get('output_tokens', 0):,}
- Thinking tokens: {data.get('thinking_tokens', 0):,}
- Total tokens: {data.get('total_tokens', 0):,}
- Estimated cost: {data.get('cost_formatted', '$0.00')}"""
                    yield {"type": "response", "data": {"content": content}}

                # /todos - get todo list
                elif command == "/todos":
                    if not session_id:
                        yield {"type": "response", "data": {"content": "No active session. Send a message first."}}
                        return
                    url = f"{server_url}/api/agent/chat/{session_id}/todos"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    todos = data.get("todos", [])
                    summary = data.get("summary", {})
                    if not todos:
                        yield {"type": "response", "data": {"content": "No todos in current session."}}
                        return
                    lines = ["**Todo List**", ""]
                    for todo in todos:
                        status_icon = {"pending": "○", "in_progress": "◐", "completed": "●"}.get(todo.get("status"), "○")
                        lines.append(f"- {status_icon} {todo.get('title', 'Untitled')}")
                    lines.append("")
                    lines.append(f"Total: {summary.get('total', 0)} | Pending: {summary.get('pending', 0)} | In Progress: {summary.get('in_progress', 0)} | Done: {summary.get('completed', 0)}")
                    yield {"type": "response", "data": {"content": "\n".join(lines)}}

                # /todo-add [title] - add a todo
                elif command == "/todo-add":
                    if not session_id:
                        yield {"type": "response", "data": {"content": "No active session. Send a message first."}}
                        return
                    if not args:
                        yield {"type": "response", "data": {"content": "Usage: /todo-add [title]"}}
                        return
                    url = f"{server_url}/api/agent/chat/{session_id}/todos"
                    resp = await client.post(url, params={"title": args})
                    resp.raise_for_status()
                    data = resp.json()
                    task = data.get("task", {})
                    yield {"type": "response", "data": {"content": f"Added todo: **{task.get('title', args)}**"}}

                # /compact - compact conversation
                elif command == "/compact":
                    if not session_id:
                        yield {"type": "response", "data": {"content": "No active session. Send a message first."}}
                        return
                    url = f"{server_url}/api/agent/chat/{session_id}/compact"
                    resp = await client.post(url)
                    resp.raise_for_status()
                    data = resp.json()
                    if not data.get("compacted"):
                        yield {"type": "response", "data": {"content": f"Could not compact: {data.get('reason', 'unknown')}"}}
                        return
                    content = f"""**Conversation Compacted**

- Original messages: {data.get('original_message_count', 0)}
- New messages: {data.get('new_message_count', 0)}
- Original tokens: {data.get('original_tokens', 0):,}
- New tokens: {data.get('new_tokens', 0):,}
- Reduction: {data.get('reduction_percent', 0)}%"""
                    if data.get("summary"):
                        content += f"\n\n**Summary:**\n{data['summary'][:500]}..."
                    yield {"type": "response", "data": {"content": content}}

                # /messages - show conversation history
                elif command == "/messages":
                    if not session_id:
                        yield {"type": "response", "data": {"content": "No active session. Send a message first."}}
                        return
                    url = f"{server_url}/api/agent/chat/{session_id}/export"
                    resp = await client.get(url, params={"limit": 10})
                    resp.raise_for_status()
                    data = resp.json()
                    messages = data.get("messages", [])
                    if not messages:
                        yield {"type": "response", "data": {"content": "No messages in session."}}
                        return
                    lines = [f"**Conversation** ({data.get('message_count', 0)} messages, model: {data.get('model', 'unknown')})", ""]
                    for msg in messages[-5:]:  # Show last 5
                        role = msg.get("role", "unknown")
                        content = str(msg.get("content", ""))[:100]
                        lines.append(f"**{role}:** {content}...")
                    yield {"type": "response", "data": {"content": "\n".join(lines)}}

                # /status - show index status
                elif command == "/status":
                    url = f"{server_url}/api/index/status"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    content = f"""**Index Status**

- Status: {data.get('status', 'unknown')}
- Files indexed: {data.get('files_indexed', 0):,}
- Total files: {data.get('total_files', 0):,}
- Last updated: {data.get('last_updated', 'never')}"""
                    yield {"type": "response", "data": {"content": content}}

                # /diff - show git diff
                elif command == "/diff":
                    import subprocess
                    result = subprocess.run(
                        ["git", "diff", "--stat"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        yield {"type": "response", "data": {"content": f"**Uncommitted Changes**\n\n```\n{result.stdout}\n```"}}
                    else:
                        yield {"type": "response", "data": {"content": "No uncommitted changes."}}

                # /doctor - run diagnostics
                elif command == "/doctor":
                    url = f"{server_url}/api/health"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    content = f"""**Health Check**

- Status: {data.get('status', 'unknown')}
- Database: {data.get('database', 'unknown')}
- Version: {data.get('version', 'unknown')}"""
                    yield {"type": "response", "data": {"content": content}}

                # /share - create shareable session link
                elif command == "/share":
                    import hashlib
                    import socket
                    import subprocess
                    import sys

                    # Generate user_id and display_name like the interactive CLI does
                    hostname = socket.gethostname()
                    username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
                    display_name = args.strip() if args else f"{username}@{hostname}"
                    pid = os.getpid()
                    user_id = hashlib.sha256(f"{username}@{hostname}:{pid}".encode()).hexdigest()[:16]

                    # Create a multiuser session
                    url = f"{server_url}/api/multiuser/session/create"
                    resp = await client.post(url, json={
                        "user_id": user_id,
                        "display_name": display_name,
                        "model": current_model,
                        "plan_mode": current_mode == "plan",
                    })
                    resp.raise_for_status()
                    data = resp.json()
                    invite_code = data.get("invite_code", "")
                    shared_session_id = data.get("session_id", "")

                    # Store multiuser state
                    multiuser_user_id = user_id
                    multiuser_session_id = shared_session_id
                    multiuser_is_owner = True
                    multiuser_server_url = server_url

                    # Encode server URL into invite code so joiner connects to same server
                    # Format: INVITE_CODE@PORT (e.g., ABC123@57220)
                    port = server_url.split(":")[-1]
                    full_invite = f"{invite_code}@{port}"

                    # Copy to clipboard
                    clipboard_msg = ""
                    try:
                        if sys.platform == "darwin":
                            subprocess.run(["pbcopy"], input=full_invite.encode(), check=True, capture_output=True)
                            clipboard_msg = " *(copied to clipboard)*"
                        elif sys.platform == "win32":
                            subprocess.run(["clip"], input=full_invite.encode("utf-16le"), check=True, capture_output=True)
                            clipboard_msg = " *(copied to clipboard)*"
                        else:
                            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                                try:
                                    subprocess.run(cmd, input=full_invite.encode(), check=True, capture_output=True)
                                    clipboard_msg = " *(copied to clipboard)*"
                                    break
                                except FileNotFoundError:
                                    continue
                    except Exception:
                        pass

                    content = f"""**Session Shared!**

Invite code: `{full_invite}`{clipboard_msg}

Share this code with others to let them join.
They can join with: `/join {full_invite}`"""
                    yield {"type": "response", "data": {"content": content}}

                    # Signal TUI to start multiuser listener
                    yield {
                        "type": "multiuser_started",
                        "data": {
                            "session_id": shared_session_id,
                            "user_id": user_id,
                            "server_url": server_url,
                            "is_owner": True,
                        }
                    }

                # /join [code] - join a shared session
                elif command == "/join":
                    import hashlib
                    import socket

                    if not args:
                        yield {"type": "response", "data": {"content": "Usage: /join [invite-code]\n\nExample: `/join ABC123@57220`"}}
                        return

                    raw_invite = args.strip()

                    # Parse invite code - may include port (e.g., ABC123@57220)
                    if "@" in raw_invite:
                        invite_code, port_str = raw_invite.rsplit("@", 1)
                        invite_code = invite_code.upper()
                        try:
                            port = int(port_str)
                            # Use the server from the invite code
                            join_server_url = f"http://localhost:{port}"
                        except ValueError:
                            # Not a port number, treat whole thing as invite code
                            invite_code = raw_invite.upper()
                            join_server_url = server_url
                    else:
                        invite_code = raw_invite.upper()
                        join_server_url = server_url

                    # Generate user_id and display_name
                    hostname = socket.gethostname()
                    username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
                    display_name = f"{username}@{hostname}"
                    pid = os.getpid()
                    user_id = hashlib.sha256(f"{username}@{hostname}:{pid}".encode()).hexdigest()[:16]

                    url = f"{join_server_url}/api/multiuser/session/join"
                    resp = await client.post(url, json={
                        "invite_code": invite_code,
                        "user_id": user_id,
                        "display_name": display_name,
                    })
                    resp.raise_for_status()
                    data = resp.json()
                    joined_session_id = data.get("session_id", "")
                    participants = data.get("participants", [])
                    message_count = data.get("message_count", 0)

                    # Store multiuser state
                    multiuser_user_id = user_id
                    multiuser_session_id = joined_session_id
                    multiuser_is_owner = False
                    multiuser_server_url = join_server_url

                    # Build basic info
                    content_lines = [
                        "**Joined Session!**",
                        "",
                        f"- Session: `{joined_session_id[:8]}...`",
                        f"- Participants: {len(participants)}",
                        f"- Messages: {message_count}",
                        "",
                        "Use `/who` to see participants.",
                    ]

                    yield {"type": "response", "data": {"content": "\n".join(content_lines)}}

                    # Fetch and emit message history if there are messages
                    if message_count > 0:
                        try:
                            history_url = f"{join_server_url}/api/multiuser/session/{joined_session_id}/messages"
                            history_resp = await client.get(history_url, params={"limit": 50})
                            if history_resp.status_code == 200:
                                messages = history_resp.json().get("messages", [])
                                if messages:
                                    # Emit separator
                                    yield {"type": "history_start", "data": {"count": len(messages)}}

                                    # Emit each message as a history event
                                    for msg in messages:
                                        yield {
                                            "type": "history_message",
                                            "data": {
                                                "role": msg.get("role", "user"),
                                                "content": msg.get("content", ""),
                                                "user_id": msg.get("user_id", ""),
                                                "display_name": msg.get("display_name", "User"),
                                            }
                                        }

                                    # Emit separator
                                    yield {"type": "history_end", "data": {}}
                        except Exception:
                            pass  # Silently fail history fetch

                    # Signal TUI to start multiuser listener
                    yield {
                        "type": "multiuser_started",
                        "data": {
                            "session_id": joined_session_id,
                            "user_id": user_id,
                            "server_url": join_server_url,
                            "is_owner": False,
                        }
                    }

                # /who - show session participants
                elif command == "/who":
                    if not multiuser_session_id:
                        yield {"type": "response", "data": {"content": "No active session."}}
                        return
                    # Try multiuser endpoint
                    url = f"{multiuser_server_url}/api/multiuser/session/{multiuser_session_id}/participants"
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = resp.json()
                        participants = data.get("participants", []) if isinstance(data, dict) else data
                        if not participants:
                            yield {"type": "response", "data": {"content": "No other participants in session."}}
                            return
                        lines = ["**Session Participants**", ""]
                        for p in participants:
                            # Status indicator
                            is_online = p.get("is_online", p.get("is_active", False))
                            status = "🟢" if is_online else "⚪"

                            # Name and role
                            name = p.get("display_name", p.get("name", "Unknown"))
                            role = p.get("role", "editor")
                            role_display = "👑 Owner" if role == "owner" else role.title()

                            # Joined time
                            joined = p.get("joined_at", "")
                            joined_display = ""
                            if joined:
                                try:
                                    from datetime import datetime
                                    dt = datetime.fromisoformat(joined.replace("Z", "+00:00"))
                                    joined_display = f" *(joined {dt.strftime('%H:%M')})*"
                                except Exception:
                                    pass

                            lines.append(f"- {status} **{name}** - {role_display}{joined_display}")
                        yield {"type": "response", "data": {"content": "\n".join(lines)}}
                    except httpx.HTTPStatusError:
                        yield {"type": "response", "data": {"content": "This is a single-user session."}}

                # /leave - leave shared session
                elif command == "/leave":
                    if not multiuser_session_id:
                        yield {"type": "response", "data": {"content": "No active session."}}
                        return
                    if not multiuser_user_id:
                        yield {"type": "response", "data": {"content": "Not in a shared session. Use `/share` or `/join` first."}}
                        return
                    url = f"{multiuser_server_url}/api/multiuser/session/{multiuser_session_id}/leave"
                    try:
                        resp = await client.post(url, json={"user_id": multiuser_user_id})
                        resp.raise_for_status()
                        # Clear multiuser state
                        multiuser_user_id = None
                        multiuser_session_id = None
                        multiuser_is_owner = False
                        multiuser_server_url = None
                        yield {"type": "response", "data": {"content": "Left the shared session."}}
                        # Signal TUI to stop multiuser listener
                        yield {"type": "multiuser_stopped", "data": {}}
                    except httpx.HTTPStatusError:
                        yield {"type": "response", "data": {"content": "Not in a shared session."}}

                # /invite - show invite code for current session
                elif command == "/invite":
                    import subprocess
                    import sys

                    if not multiuser_session_id:
                        yield {"type": "response", "data": {"content": "No active session."}}
                        return
                    url = f"{multiuser_server_url}/api/multiuser/session/{multiuser_session_id}/state"
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = resp.json()
                        invite_code = data.get("invite_code", "")
                        if invite_code:
                            # Add port to invite code
                            port = server_url.split(":")[-1]
                            full_invite = f"{invite_code}@{port}"

                            # Copy to clipboard
                            clipboard_msg = ""
                            try:
                                if sys.platform == "darwin":
                                    subprocess.run(["pbcopy"], input=full_invite.encode(), check=True, capture_output=True)
                                    clipboard_msg = " *(copied to clipboard)*"
                                elif sys.platform == "win32":
                                    subprocess.run(["clip"], input=full_invite.encode("utf-16le"), check=True, capture_output=True)
                                    clipboard_msg = " *(copied to clipboard)*"
                                else:
                                    for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                                        try:
                                            subprocess.run(cmd, input=full_invite.encode(), check=True, capture_output=True)
                                            clipboard_msg = " *(copied to clipboard)*"
                                            break
                                        except FileNotFoundError:
                                            continue
                            except Exception:
                                pass

                            yield {"type": "response", "data": {"content": f"**Invite Code:** `{full_invite}`{clipboard_msg}\n\nShare this code so others can join with `/join {full_invite}`"}}
                        else:
                            yield {"type": "response", "data": {"content": "This session is not shared. Use `/share` first."}}
                    except httpx.HTTPStatusError:
                        yield {"type": "response", "data": {"content": "This session is not shared. Use `/share` first."}}

                # /projectmd - generate PROJECT.md
                elif command == "/projectmd":
                    url = f"{server_url}/api/projectmd/generate"
                    yield {"type": "thinking", "data": {"content": "Generating PROJECT.md..."}}
                    resp = await client.post(url, json={}, timeout=60.0)
                    resp.raise_for_status()
                    data = resp.json()
                    if data.get("success"):
                        yield {"type": "response", "data": {"content": f"PROJECT.md generated at: `{data.get('path', 'PROJECT.md')}`"}}
                    else:
                        yield {"type": "response", "data": {"content": f"Failed: {data.get('error', 'unknown error')}"}}

                # /research [goal] - deep research
                elif command == "/research":
                    if not args:
                        yield {"type": "response", "data": {"content": "Usage: /research [goal]"}}
                        return
                    url = f"{server_url}/api/research"
                    yield {"type": "thinking", "data": {"content": f"Researching: {args}"}}
                    # This is an SSE endpoint, so handle it specially
                    async with client.stream("POST", url, json={"goal": args}, timeout=120.0) as response:
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
                                        yield {"type": current_event, "data": data or {}}
                                    except json.JSONDecodeError:
                                        pass

                # /pr [url] - review a pull request
                elif command == "/pr":
                    if not args:
                        yield {"type": "response", "data": {"content": "Usage: /pr [url or pr-number]"}}
                        return
                    url = f"{server_url}/api/review"
                    yield {"type": "thinking", "data": {"content": f"Reviewing PR: {args}"}}
                    resp = await client.post(url, json={"pr_url": args.strip()}, timeout=120.0)
                    resp.raise_for_status()
                    data = resp.json()
                    yield {"type": "response", "data": {"content": data.get("review", "No review generated.")}}

                # /context - show context window usage
                elif command == "/context":
                    if not session_id:
                        yield {"type": "response", "data": {"content": "No active session. Send a message first."}}
                        return
                    url = f"{server_url}/api/agent/chat/{session_id}/stats"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    total = data.get("total_tokens", 0)
                    # Estimate context window size based on model
                    model = data.get("model", "unknown")
                    max_context = 200000  # Default assumption
                    if "opus" in model.lower():
                        max_context = 200000
                    elif "sonnet" in model.lower():
                        max_context = 200000
                    elif "haiku" in model.lower():
                        max_context = 200000
                    elif "gpt-4" in model.lower():
                        max_context = 128000
                    pct = (total / max_context * 100) if max_context > 0 else 0
                    bar_len = 20
                    filled = int(bar_len * pct / 100)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    content = f"""**Context Usage**

{bar} {pct:.1f}%

- Used: {total:,} tokens
- Capacity: ~{max_context:,} tokens
- Model: `{model}`"""
                    yield {"type": "response", "data": {"content": content}}

                # /registry - browse community registry (fetch from GitHub)
                elif command == "/registry":
                    REGISTRY_URL = "https://raw.githubusercontent.com/mendyEdri/emdash-registry/main/registry.json"

                    try:
                        yield {"type": "thinking", "data": {"content": "Fetching registry..."}}
                        resp = await client.get(REGISTRY_URL, timeout=10.0)
                        resp.raise_for_status()
                        registry = resp.json()

                        # Send registry data for interactive browsing
                        yield {
                            "type": "registry_browse",
                            "data": {
                                "skills": registry.get("skills", {}),
                                "rules": registry.get("rules", {}),
                                "agents": registry.get("agents", {}),
                                "verifiers": registry.get("verifiers", {}),
                            }
                        }
                    except Exception as e:
                        yield {"type": "error", "data": {"message": f"Failed to fetch registry: {str(e)[:100]}"}}

                # /skills - manage skills (send structured data for interactive UI)
                elif command == "/skills":
                    yield {"type": "thinking", "data": {"content": "Loading skills..."}}
                    skills_list = []
                    try:
                        url = f"{server_url}/api/skills"
                        resp = await client.get(url, timeout=5.0)
                        resp.raise_for_status()
                        data = resp.json()
                        skills_list = data.get("skills", [])
                    except Exception:
                        # Fallback: read from local .emdash/skills directory
                        from pathlib import Path
                        skills_dir = Path.cwd() / ".emdash" / "skills"
                        if skills_dir.exists():
                            for skill_path in skills_dir.iterdir():
                                if skill_path.is_dir():
                                    skill_file = skill_path / "SKILL.md"
                                    if skill_file.exists():
                                        content = skill_file.read_text()
                                        # Extract description from first line
                                        desc = content.split('\n')[0][:100] if content else "No description"
                                        skills_list.append({
                                            "name": skill_path.name,
                                            "description": desc,
                                            "builtin": False
                                        })
                    yield {
                        "type": "skills_browse",
                        "data": {"skills": skills_list}
                    }

                # /agents - manage agents (send structured data for interactive UI)
                elif command == "/agents":
                    yield {"type": "thinking", "data": {"content": "Loading agents..."}}
                    agents_list = []
                    try:
                        url = f"{server_url}/api/agents"
                        resp = await client.get(url, timeout=5.0)
                        resp.raise_for_status()
                        data = resp.json()
                        agents_list = data.get("agents", [])
                    except Exception:
                        # Fallback: read from local .emdash/agents directory
                        from pathlib import Path
                        agents_dir = Path.cwd() / ".emdash" / "agents"
                        if agents_dir.exists():
                            for agent_file in agents_dir.glob("*.md"):
                                content = agent_file.read_text()
                                desc = content.split('\n')[0][:100] if content else "No description"
                                agents_list.append({
                                    "name": agent_file.stem,
                                    "description": desc,
                                })
                    yield {
                        "type": "agents_browse",
                        "data": {"agents": agents_list}
                    }

                # /rules - manage rules (send structured data for interactive UI)
                elif command == "/rules":
                    yield {"type": "thinking", "data": {"content": "Loading rules..."}}
                    from pathlib import Path
                    rules_list = []
                    try:
                        rules_dir = Path.cwd() / ".emdash" / "rules"
                        rules_file = Path.cwd() / ".emdash" / "rules.md"

                        # Check rules directory first
                        if rules_dir.exists():
                            for rule_file in rules_dir.glob("*.md"):
                                content = rule_file.read_text()
                                preview = content[:100].replace("\n", " ").strip()
                                rules_list.append({
                                    "name": rule_file.stem,
                                    "preview": preview + ("..." if len(content) > 100 else ""),
                                    "path": str(rule_file)
                                })
                        # Also check single rules.md file
                        elif rules_file.exists():
                            content = rules_file.read_text()
                            preview = content[:100].replace("\n", " ").strip()
                            rules_list.append({
                                "name": "rules",
                                "preview": preview + ("..." if len(content) > 100 else ""),
                                "path": str(rules_file)
                            })
                    except Exception:
                        pass

                    yield {
                        "type": "rules_browse",
                        "data": {"rules": rules_list}
                    }

                # /hooks - manage hooks (send structured data for interactive UI)
                elif command == "/hooks":
                    yield {"type": "thinking", "data": {"content": "Loading hooks..."}}
                    from pathlib import Path
                    hooks_list = []
                    events = ["session_start", "session_end", "tool_start", "tool_result", "response", "error"]
                    try:
                        hooks_file = Path.cwd() / ".emdash" / "hooks.json"
                        if hooks_file.exists():
                            import json as json_mod
                            hooks_data = json_mod.loads(hooks_file.read_text())
                            hooks_list = hooks_data.get("hooks", [])
                    except Exception:
                        pass

                    yield {
                        "type": "hooks_browse",
                        "data": {"hooks": hooks_list, "events": events}
                    }

                # /verify - manage verifiers (send structured data for interactive UI)
                elif command == "/verify":
                    yield {"type": "thinking", "data": {"content": "Loading verifiers..."}}
                    from pathlib import Path
                    verifiers_list = []
                    try:
                        verifiers_file = Path.cwd() / ".emdash" / "verifiers.json"
                        if verifiers_file.exists():
                            import json as json_mod
                            data = json_mod.loads(verifiers_file.read_text())
                            verifiers_list = data.get("verifiers", [])
                    except Exception:
                        pass

                    yield {
                        "type": "verifiers_browse",
                        "data": {"verifiers": verifiers_list}
                    }

                # /mcp - manage MCP servers (send structured data for interactive UI)
                elif command == "/mcp":
                    yield {"type": "thinking", "data": {"content": "Loading MCP servers..."}}
                    from pathlib import Path
                    mcp_file = Path.cwd() / ".emdash" / "mcp.json"
                    servers_list = []

                    if mcp_file.exists():
                        import json as json_mod
                        try:
                            data = json_mod.loads(mcp_file.read_text())
                            servers = data.get("mcpServers", {})
                            for name, config in servers.items():
                                servers_list.append({
                                    "name": name,
                                    "command": config.get("command", ""),
                                    "enabled": config.get("enabled", True),
                                    "args": config.get("args", []),
                                })
                        except Exception:
                            pass

                    yield {
                        "type": "mcp_browse",
                        "data": {"servers": servers_list}
                    }

                # /project - project management (interactive browser)
                elif command == "/project":
                    cmd_parts = cmd.strip().split()
                    subcommand = cmd_parts[1] if len(cmd_parts) > 1 else None

                    # Sub-commands that return text responses
                    if subcommand in ("create", "edit", "delete", "task-create", "task-transition", "task-delete", "link-session", "add-session", "add-to-project"):
                        try:
                            # /project add-session <project_id> [task_id]
                            # Links the current session to a project (and optionally a task)
                            # Auto-shares the session so others can join
                            if subcommand == "add-session" and len(cmd_parts) > 2:
                                import hashlib
                                import socket

                                proj_id = cmd_parts[2]
                                tid = cmd_parts[3] if len(cmd_parts) > 3 else None

                                # First, create a shared multiuser session if not already shared
                                hostname = socket.gethostname()
                                username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
                                display_name = os.environ.get("EMDASH_USER_DISPLAY_NAME", f"{username}@{hostname}")
                                pid = os.getpid()
                                user_id = hashlib.sha256(f"{username}@{hostname}:{pid}".encode()).hexdigest()[:16]

                                # Create multiuser session to get invite code
                                share_url = f"{server_url}/api/multiuser/session/create"
                                share_resp = await client.post(share_url, json={
                                    "user_id": user_id,
                                    "display_name": display_name,
                                    "model": current_model,
                                    "plan_mode": current_mode == "plan",
                                }, timeout=10.0)
                                share_resp.raise_for_status()
                                share_data = share_resp.json()
                                invite_code = share_data.get("invite_code", "")
                                shared_session_id = share_data.get("session_id", "")

                                # Include port in invite code for joining
                                port = server_url.split(":")[-1]
                                full_invite = f"{invite_code}@{port}" if invite_code else ""

                                # Now link the session with the invite code
                                url = f"{server_url}/api/multiuser/project/{proj_id}/link-session"
                                payload = {
                                    "session_id": shared_session_id or local_identity_id,
                                    "invite_code": full_invite,
                                }
                                if tid:
                                    payload["task_id"] = tid
                                resp = await client.post(url, json=payload, timeout=10.0)
                                resp.raise_for_status()

                                msg = f"Session shared and added to project. Invite: `{full_invite}`"
                                if tid:
                                    msg += f" (linked to task)"
                                yield {"type": "response", "data": {"content": msg}}

                                # Signal TUI to start multiuser listener
                                yield {
                                    "type": "multiuser_started",
                                    "data": {
                                        "session_id": shared_session_id,
                                        "user_id": user_id,
                                        "server_url": server_url,
                                        "is_owner": True,
                                    }
                                }
                                return

                            # /project add-to-project <project_id>
                            # Alias: links current session to a project from any context
                            elif subcommand == "add-to-project" and len(cmd_parts) > 2:
                                proj_id = cmd_parts[2]
                                url = f"{server_url}/api/multiuser/project/{proj_id}/link-session"
                                resp = await client.post(url, json={"session_id": local_identity_id}, timeout=10.0)
                                resp.raise_for_status()
                                yield {"type": "response", "data": {"content": "Session added to project."}}
                                return

                            # /project create "name" ["description"]
                            # Creates a new project
                            elif subcommand == "create":
                                import shlex
                                try:
                                    # Parse quoted arguments: /project create "My Project" "Description"
                                    parsed = shlex.split(cmd)
                                    # parsed[0] = "/project", parsed[1] = "create", parsed[2] = name, parsed[3] = description
                                    if len(parsed) < 3:
                                        yield {"type": "error", "data": {"message": "Usage: /project create \"name\" [\"description\"]"}}
                                        return
                                    proj_name = parsed[2]
                                    proj_desc = parsed[3] if len(parsed) > 3 else ""
                                except ValueError as e:
                                    yield {"type": "error", "data": {"message": f"Invalid command format: {e}"}}
                                    return

                                uid = multiuser_user_id or "local"
                                display_name = os.environ.get("EMDASH_USER_DISPLAY_NAME", "Local User")
                                url = f"{server_url}/api/multiuser/project/create"
                                payload = {
                                    "name": proj_name,
                                    "description": proj_desc,
                                    "user_id": uid,
                                    "display_name": display_name,
                                }
                                resp = await client.post(url, json=payload, timeout=10.0)
                                resp.raise_for_status()
                                result = resp.json()
                                proj_id = result.get("project_id", "")
                                yield {"type": "response", "data": {"content": f"Project '{proj_name}' created successfully."}}
                                return

                            elif subcommand == "delete" and len(cmd_parts) > 2:
                                proj_id = cmd_parts[2]
                                uid = multiuser_user_id or "local"
                                url = f"{server_url}/api/multiuser/project/{proj_id}?user_id={uid}"
                                resp = await client.delete(url, timeout=10.0)
                                resp.raise_for_status()
                                yield {"type": "response", "data": {"content": "Project deleted successfully."}}
                                return

                            elif subcommand == "task-delete" and len(cmd_parts) > 2:
                                tid = cmd_parts[2]
                                url = f"{server_url}/api/multiuser/task/{tid}"
                                resp = await client.delete(url, timeout=10.0)
                                resp.raise_for_status()
                                yield {"type": "response", "data": {"content": "Task deleted successfully."}}
                                return

                            elif subcommand == "task-transition" and len(cmd_parts) > 3:
                                tid = cmd_parts[2]
                                cur_status = cmd_parts[3]
                                # Cycle to next status
                                status_cycle = ["open", "in_progress", "in_review", "done"]
                                try:
                                    idx = status_cycle.index(cur_status)
                                    next_status = status_cycle[(idx + 1) % len(status_cycle)]
                                except ValueError:
                                    next_status = "open"
                                url = f"{server_url}/api/multiuser/task/{tid}/transition"
                                resp = await client.post(url, json={"status": next_status}, timeout=10.0)
                                resp.raise_for_status()
                                yield {"type": "response", "data": {"content": f"Task status changed to: {next_status}"}}
                                return

                            # /project task-create <project_id> "title" ["description"]
                            # Creates a new task in a project
                            elif subcommand == "task-create":
                                import shlex
                                try:
                                    # Parse quoted arguments: /project task-create proj123 "Task title" "Description"
                                    parsed = shlex.split(cmd)
                                    # parsed[0] = "/project", parsed[1] = "task-create", parsed[2] = project_id, parsed[3] = title, parsed[4] = description
                                    if len(parsed) < 4:
                                        yield {"type": "error", "data": {"message": "Usage: /project task-create <project_id> \"title\" [\"description\"]"}}
                                        return
                                    proj_id = parsed[2]
                                    task_title = parsed[3]
                                    task_desc = parsed[4] if len(parsed) > 4 else ""
                                except ValueError as e:
                                    yield {"type": "error", "data": {"message": f"Invalid command format: {e}"}}
                                    return

                                uid = multiuser_user_id or "local"
                                display_name = os.environ.get("EMDASH_USER_DISPLAY_NAME", "Local User")
                                url = f"{server_url}/api/multiuser/project/{proj_id}/tasks"
                                payload = {
                                    "title": task_title,
                                    "description": task_desc,
                                    "reporter_id": uid,
                                    "reporter_name": display_name,
                                    "priority": "medium",
                                    "status": "open",
                                }
                                resp = await client.post(url, json=payload, timeout=10.0)
                                resp.raise_for_status()
                                yield {"type": "response", "data": {"content": f"Task '{task_title}' created successfully."}}
                                return

                            elif subcommand == "link-session" and len(cmd_parts) > 2:
                                import hashlib
                                import socket

                                tid = cmd_parts[2]

                                # Auto-share the session so others can join
                                hostname = socket.gethostname()
                                username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
                                display_name = os.environ.get("EMDASH_USER_DISPLAY_NAME", f"{username}@{hostname}")
                                pid = os.getpid()
                                user_id = hashlib.sha256(f"{username}@{hostname}:{pid}".encode()).hexdigest()[:16]

                                # Create multiuser session to get invite code
                                share_url = f"{server_url}/api/multiuser/session/create"
                                share_resp = await client.post(share_url, json={
                                    "user_id": user_id,
                                    "display_name": display_name,
                                    "model": current_model,
                                    "plan_mode": current_mode == "plan",
                                }, timeout=10.0)
                                share_resp.raise_for_status()
                                share_data = share_resp.json()
                                invite_code = share_data.get("invite_code", "")
                                shared_session_id = share_data.get("session_id", "")

                                # Include port in invite code
                                port = server_url.split(":")[-1]
                                full_invite = f"{invite_code}@{port}" if invite_code else ""

                                # Link with invite code
                                url = f"{server_url}/api/multiuser/task/{tid}/link-session"
                                resp = await client.post(url, json={
                                    "session_id": shared_session_id or local_identity_id,
                                    "invite_code": full_invite,
                                }, timeout=10.0)
                                resp.raise_for_status()
                                yield {"type": "response", "data": {"content": f"Session shared and linked to task. Invite: `{full_invite}`"}}

                                # Signal TUI to start multiuser listener
                                yield {
                                    "type": "multiuser_started",
                                    "data": {
                                        "session_id": shared_session_id,
                                        "user_id": user_id,
                                        "server_url": server_url,
                                        "is_owner": True,
                                    }
                                }
                                return

                            else:
                                # Pass through to agent for natural language handling
                                yield {"type": "_passthrough"}
                                return
                        except Exception as e:
                            yield {"type": "error", "data": {"message": f"Project action failed: {str(e)[:100]}"}}
                            return

                    # Default: load all project data for interactive browser
                    yield {"type": "thinking", "data": {"content": "Loading projects..."}}

                    projects = []
                    tasks = []
                    sessions_list = []
                    agents_list = []
                    skills_list = []
                    current_uid = multiuser_user_id or ""
                    current_sid = local_identity_id

                    try:
                        # Fetch all projects directly (no team scoping needed)
                        url = f"{server_url}/api/multiuser/projects"
                        resp = await client.get(url, timeout=10.0)
                        resp.raise_for_status()
                        data = resp.json()
                        projects = data.get("projects", [])

                        # Fetch tasks and sessions for each project
                        for proj in projects:
                            pid = proj.get("project_id", "")
                            if pid:
                                try:
                                    url = f"{server_url}/api/multiuser/project/{pid}/tasks"
                                    resp = await client.get(url, timeout=10.0)
                                    resp.raise_for_status()
                                    task_data = resp.json()
                                    tasks.extend(task_data.get("tasks", []))
                                except Exception:
                                    pass
                                try:
                                    url = f"{server_url}/api/multiuser/project/{pid}/sessions"
                                    resp = await client.get(url, timeout=10.0)
                                    resp.raise_for_status()
                                    sess_data = resp.json()
                                    for s in sess_data.get("sessions", []):
                                        s["project_id"] = pid
                                        sessions_list.append(s)
                                except Exception:
                                    pass

                        # Fetch agents from multiuser registry (use first team if available)
                        try:
                            teams_url = f"{server_url}/api/teams"
                            teams_resp = await client.get(teams_url, timeout=5.0)
                            teams_resp.raise_for_status()
                            teams_data = teams_resp.json()
                            teams_list = teams_data.get("teams", [])
                            if teams_list:
                                team_id = teams_list[0].get("team_id", "")
                                if team_id:
                                    try:
                                        url = f"{server_url}/api/multiuser/team/{team_id}/registry/agents"
                                        resp = await client.get(url, timeout=5.0)
                                        resp.raise_for_status()
                                        agents_list = resp.json().get("agents", [])
                                    except Exception:
                                        pass
                                    try:
                                        url = f"{server_url}/api/multiuser/team/{team_id}/registry/skills"
                                        resp = await client.get(url, timeout=5.0)
                                        resp.raise_for_status()
                                        skills_list = resp.json().get("skills", [])
                                    except Exception:
                                        pass
                        except Exception:
                            pass

                    except Exception:
                        # If API fails, provide empty data gracefully
                        pass

                    yield {
                        "type": "project_browse",
                        "data": {
                            "projects": projects,
                            "tasks": tasks,
                            "sessions": sessions_list,
                            "agents": agents_list,
                            "skills": skills_list,
                            "current_user_id": current_uid,
                            "current_session_id": current_sid,
                        }
                    }

                # /session - session management
                elif command == "/session":
                    url = f"{server_url}/api/sessions"
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = resp.json()
                        sessions = data.get("sessions", [])
                        if not sessions:
                            yield {"type": "response", "data": {"content": "No saved sessions. Use `/session save [name]` in CLI to save."}}
                            return
                        lines = ["**Saved Sessions**", ""]
                        for sess in sessions[:10]:
                            lines.append(f"- **{sess.get('name', 'unknown')}** - {sess.get('created_at', 'unknown')[:10]}")
                        yield {"type": "response", "data": {"content": "\n".join(lines)}}
                    except httpx.HTTPStatusError:
                        yield {"type": "response", "data": {"content": "No saved sessions. Use `/session save [name]` in CLI to save."}}

                # /index - manage codebase index
                elif command == "/index":
                    url = f"{server_url}/api/index/status"
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = resp.json()
                        content = f"""**Codebase Index**

- Status: {data.get('status', 'unknown')}
- Files indexed: {data.get('files_indexed', 0):,}
- Total files: {data.get('total_files', 0):,}
- Last updated: {data.get('last_updated', 'never')}

Use `/index start` in CLI to reindex."""
                        yield {"type": "response", "data": {"content": content}}
                    except httpx.HTTPStatusError:
                        yield {"type": "response", "data": {"content": "Index not configured. Use `em --index status` in CLI to check status."}}

                # /team - team management
                elif command == "/team":
                    url = f"{server_url}/api/teams"
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = resp.json()
                        teams = data.get("teams", [])
                        if not teams:
                            yield {"type": "response", "data": {"content": "Not a member of any teams. Use `/team create` or `/team join` in CLI."}}
                            return
                        lines = ["**Your Teams**", ""]
                        for team in teams:
                            lines.append(f"- **{team.get('name', 'unknown')}** ({team.get('member_count', 0)} members)")
                        yield {"type": "response", "data": {"content": "\n".join(lines)}}
                    except httpx.HTTPStatusError:
                        yield {"type": "response", "data": {"content": "Teams feature not available."}}

                # /auth - authentication status
                elif command == "/auth":
                    url = f"{server_url}/api/auth/status"
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = resp.json()
                        lines = ["**Authentication Status**", ""]
                        for service, status in data.items():
                            icon = "✓" if status.get("authenticated") else "○"
                            lines.append(f"- {icon} **{service}** - {status.get('user', 'Not logged in')}")
                        yield {"type": "response", "data": {"content": "\n".join(lines)}}
                    except httpx.HTTPStatusError:
                        yield {"type": "response", "data": {"content": "Use `/auth login` in CLI to authenticate."}}

                # /telegram - telegram status
                elif command == "/telegram":
                    url = f"{server_url}/api/telegram/status"
                    try:
                        resp = await client.get(url)
                        resp.raise_for_status()
                        data = resp.json()
                        connected = data.get("connected", False)
                        content = f"""**Telegram Integration**

- Status: {'Connected' if connected else 'Not connected'}
- Bot: {data.get('bot_username', 'Not configured')}
- Chats: {data.get('chat_count', 0)}

Use `/telegram setup` in CLI to configure."""
                        yield {"type": "response", "data": {"content": content}}
                    except httpx.HTTPStatusError:
                        yield {"type": "response", "data": {"content": "Telegram not configured. Use `/telegram setup` in CLI."}}

                # /setup - interactive wizard (not supported in TUI)
                elif command == "/setup":
                    yield {"type": "response", "data": {"content": "The setup wizard requires interactive terminal input.\n\nPlease run `em` in your terminal and use `/setup` there to configure rules, agents, skills, and verifiers."}}

                else:
                    # Unknown command - yield marker to pass to agent
                    yield {"type": "_passthrough", "data": {}}
                    return

            except httpx.HTTPStatusError as e:
                yield {"type": "error", "data": {"message": f"API error: {e.response.status_code} - {e.response.text[:100]}"}}
            except httpx.TimeoutException:
                yield {"type": "error", "data": {"message": "Request timed out"}}
            except Exception as e:
                yield {"type": "error", "data": {"message": str(e)}}

    async def handler(
        message: str, images: list[dict] | None = None
    ) -> AsyncIterator[dict]:
        """Process a message and stream events back.

        This is a simple agent processor. In the new decorator architecture,
        multiuser logic is handled by the decorators (StandardDecorator for
        solo mode, SharedDecorator for multiuser mode).

        Args:
            message: User message to process
            images: Optional list of images [{"data": base64_str, "format": "png"}]

        Yields:
            Event dicts with type and data keys
        """
        nonlocal session_id

        # Check if this is a slash command with a dedicated endpoint
        if message.strip().startswith("/"):
            cmd = message.strip().split()[0].lower()
            # List of commands that have dedicated API handlers
            dedicated_commands = {
                "/stats", "/todos", "/todo-add", "/compact", "/messages",
                "/status", "/diff", "/doctor", "/share", "/join", "/who",
                "/leave", "/invite", "/projectmd", "/research", "/pr", "/context",
                "/registry", "/skills", "/agents", "/rules", "/hooks", "/verify",
                "/mcp", "/session", "/index", "/team", "/auth", "/telegram", "/setup",
                "/project"
            }
            if cmd in dedicated_commands:
                passthrough = False
                async for event in _handle_slash_command(message):
                    if event and event.get("type") == "_passthrough":
                        passthrough = True
                        break
                    if event:
                        yield event
                if not passthrough:
                    return
                # If passthrough, fall through to send to agent

        # Process message through the agent API
        async with httpx.AsyncClient(timeout=None) as client:
            payload = {
                "message": message,
                "model": current_model,
                "options": {
                    "max_iterations": max_iterations,
                    "verbose": True,
                    "mode": current_mode,
                },
            }

            # Include images if provided (for vision-capable models)
            if images:
                payload["images"] = images

            # Use continue endpoint if we have an existing session, otherwise start new
            if session_id:
                url = f"{server_url}/api/agent/chat/{session_id}/continue"
            else:
                url = f"{server_url}/api/agent/chat"

            try:
                async with client.stream("POST", url, json=payload) as response:
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

                                    # Capture session ID for multi-turn
                                    if current_event == "session_start":
                                        if data.get("session_id"):
                                            session_id = data["session_id"]

                                    yield {
                                        "type": current_event,
                                        "data": data,
                                    }
                                except json.JSONDecodeError:
                                    pass
                        elif line == ": ping":
                            # Keep-alive ping - ignore
                            pass

            except httpx.HTTPError as e:
                yield {
                    "type": "error",
                    "data": {"message": f"HTTP error: {str(e)}"},
                }
            except Exception as e:
                yield {
                    "type": "error",
                    "data": {"message": str(e)},
                }

    def reset_session():
        """Clear session ID and user ID to start a new conversation."""
        nonlocal session_id, multiuser_user_id
        session_id = None
        multiuser_user_id = None

    def set_mode(new_mode: str):
        """Change the agent mode."""
        nonlocal current_mode
        current_mode = new_mode

    def set_model(new_model: str):
        """Change the model and persist to .env file."""
        nonlocal current_model
        current_model = new_model
        # Persist to .env so it survives restarts
        try:
            _update_env_model(new_model)
        except Exception:
            pass  # Don't fail if .env update fails

    def get_session_id() -> str | None:
        """Get current session ID."""
        return session_id

    def get_user_id() -> str | None:
        """Get current multiuser user ID."""
        return multiuser_user_id

    async def abort_session() -> bool:
        """Abort the current running session.

        Calls the abort endpoint to signal the agent to stop.

        Returns:
            True if abort was successful, False otherwise
        """
        if not session_id:
            return False

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                url = f"{server_url}/api/agent/chat/{session_id}/abort"
                resp = await client.post(url)
                resp.raise_for_status()
                data = resp.json()
                return data.get("aborted", False)
            except Exception:
                return False

    async def approve_plan_mode(approved: bool = True, reply: str | None = None, approval_type: str = "planmode") -> AsyncIterator[dict]:
        """Approve or reject plan mode request or plan submission and stream continuation.

        Args:
            approved: Whether the request was approved
            reply: Optional feedback message (used when rejecting)
            approval_type: Type of approval - 'planmode' for plan mode entry, 'plan' for plan submission

        Yields:
            Event dicts with type and data keys
        """
        if not session_id:
            yield {
                "type": "error",
                "data": {"message": "No active session"},
            }
            return

        async with httpx.AsyncClient(timeout=None) as client:
            # Choose endpoint based on approval type
            if approval_type == "plan":
                # Plan submission approval/rejection
                if approved:
                    url = f"{server_url}/api/agent/chat/{session_id}/plan/approve"
                    params = None
                else:
                    url = f"{server_url}/api/agent/chat/{session_id}/plan/reject"
                    params = {"feedback": reply} if reply else None
            else:
                # Plan mode entry approval/rejection (default)
                if approved:
                    url = f"{server_url}/api/agent/chat/{session_id}/planmode/approve"
                    params = None
                else:
                    url = f"{server_url}/api/agent/chat/{session_id}/planmode/reject"
                    params = {"feedback": reply} if reply else None

            try:
                async with client.stream("POST", url, params=params) as response:
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

                                    yield {
                                        "type": current_event,
                                        "data": data,
                                    }
                                except json.JSONDecodeError:
                                    pass
                        elif line == ": ping":
                            pass

            except httpx.HTTPError as e:
                yield {
                    "type": "error",
                    "data": {"message": f"HTTP error: {str(e)}"},
                }
            except Exception as e:
                yield {
                    "type": "error",
                    "data": {"message": str(e)},
                }

    # Attach methods to handler function
    handler.reset_session = reset_session
    handler.set_mode = set_mode
    handler.set_model = set_model
    handler.get_session_id = get_session_id
    handler.get_user_id = get_user_id
    handler.approve_plan_mode = approve_plan_mode
    handler.abort_session = abort_session

    return handler

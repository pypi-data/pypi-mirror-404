"""Slash command handlers for the agent CLI."""

from .agents import handle_agents
from .sessions import handle_session
from .todos import handle_todos, handle_todo_add
from .hooks import handle_hooks
from .rules import handle_rules
from .skills import handle_skills
from .index import handle_index
from .mcp import handle_mcp
from .registry import handle_registry
from .auth import handle_auth
from .doctor import handle_doctor
from .verify import handle_verify, handle_verify_loop
from .setup import handle_setup
from .stats import handle_stats
from .misc import (
    handle_status,
    handle_pr,
    handle_projectmd,
    handle_research,
    handle_context,
    handle_messages,
    handle_compact,
    handle_diff,
)
from .telegram import handle_telegram
from .multiuser import (
    handle_share,
    handle_join,
    handle_leave,
    handle_who,
    handle_invite,
    handle_team,
    handle_multiuser_status,
    handle_multiuser_config,
    send_shared_message,
    broadcast_agent_response,
    broadcast_event,
    broadcast_typing,
)

__all__ = [
    "handle_agents",
    "handle_session",
    "handle_todos",
    "handle_todo_add",
    "handle_hooks",
    "handle_rules",
    "handle_skills",
    "handle_index",
    "handle_mcp",
    "handle_registry",
    "handle_auth",
    "handle_doctor",
    "handle_verify",
    "handle_verify_loop",
    "handle_setup",
    "handle_stats",
    "handle_status",
    "handle_pr",
    "handle_projectmd",
    "handle_research",
    "handle_context",
    "handle_messages",
    "handle_compact",
    "handle_diff",
    "handle_telegram",
    # Multiuser
    "handle_share",
    "handle_join",
    "handle_leave",
    "handle_who",
    "handle_invite",
    "handle_team",
    "handle_multiuser_status",
    "handle_multiuser_config",
    "send_shared_message",
    "broadcast_agent_response",
    "broadcast_event",
    "broadcast_typing",
]

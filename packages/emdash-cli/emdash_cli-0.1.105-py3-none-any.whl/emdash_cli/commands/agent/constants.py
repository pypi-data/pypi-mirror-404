"""Constants and enums for the agent CLI."""

from enum import Enum


class AgentMode(Enum):
    """Agent operation modes."""
    PLAN = "plan"
    CODE = "code"


# Subcommands for slash commands that have them
SLASH_SUBCOMMANDS = {
    "/telegram": {
        "setup": "Configure bot token and authorize chats",
        "connect": "Start the Telegram bridge",
        "status": "Show current configuration",
        "test": "Send a test message",
        "disconnect": "Disable Telegram integration",
        "settings": "View/modify settings",
    },
    "/session": {
        "save": "Save current session (e.g., /session save my-task)",
        "load": "Load a saved session",
        "list": "List all saved sessions",
        "delete": "Delete a saved session",
    },
    "/agents": {
        "create": "Create a new agent",
        "show": "Show agent details",
        "edit": "Edit an existing agent",
        "delete": "Delete an agent",
        "list": "List all agents",
    },
    "/hooks": {
        "list": "List all hooks",
        "add": "Add a new hook",
        "remove": "Remove a hook",
        "toggle": "Enable/disable a hook",
    },
    "/rules": {
        "list": "List all rules",
        "add": "Add a new rule",
        "delete": "Delete a rule",
    },
    "/skills": {
        "list": "List all skills",
        "show": "Show skill details",
        "add": "Add a new skill",
        "delete": "Delete a skill",
    },
    "/index": {
        "status": "Show index status",
        "start": "Start indexing",
        "hook": "Manage index hooks (install/uninstall)",
    },
    "/mcp": {
        "list": "List MCP servers",
        "edit": "Edit MCP configuration",
    },
    "/auth": {
        "login": "Login to GitHub",
        "logout": "Logout from GitHub",
        "status": "Show auth status",
        "google": "Google auth (login, logout, status)",
        "google login": "Login to Google (Gmail, Calendar, Drive)",
        "google logout": "Logout from Google",
        "google status": "Show Google auth status",
    },
    "/registry": {
        "skills": "Browse skills",
        "rules": "Browse rules",
        "agents": "Browse agents",
        "verifiers": "Browse verifiers",
        "install": "Install from registry",
    },
    "/verify": {
        "run": "Run verification checks",
        "list": "List available verifiers",
        "add": "Add a verifier",
    },
    "/team": {
        "create": "Create a new team",
        "join": "Join a team using invite code",
        "leave": "Leave a team",
        "list": "List your teams",
        "sessions": "List sessions in a team",
        "add": "Add current session to team",
        "join-session": "Join a team session",
        "info": "Show team info",
    },
}

# Slash commands available in interactive mode
SLASH_COMMANDS = {
    # Mode switching
    "/plan": "Switch to plan mode (explore codebase, create plans)",
    "/code": "Switch to code mode (execute file changes)",
    "/mode": "Show current mode",
    # Generation commands
    "/pr [url]": "Review a pull request",
    "/projectmd": "Generate PROJECT.md for the codebase",
    "/research [goal]": "Deep research on a topic",
    # Status commands
    "/status": "Show index and PROJECT.md status",
    "/stats": "Show your activity statistics (tokens, sessions, activity)",
    "/diff": "Show uncommitted changes in GitHub-style diff view",
    "/agents": "Manage agents (interactive menu, or /agents [create|show|edit|delete] <name>)",
    # Model selection
    "/model": "Switch model (e.g., /model fireworks)",
    # Todo management
    "/todos": "Show current agent todo list",
    "/todo-add [title]": "Add a todo item for the agent (e.g., /todo-add Fix tests)",
    # Session management
    "/session": "Save, load, or list sessions (e.g., /session save my-task)",
    "/spec": "Show current specification",
    "/reset": "Reset session state",
    # Hooks
    "/hooks": "Manage hooks (list, add, remove, toggle)",
    # Rules
    "/rules": "Manage rules (list, add, delete)",
    # Skills
    "/skills": "Manage skills (list, show, add, delete)",
    # Index
    "/index": "Manage codebase index (status, start, hook install/uninstall)",
    # MCP
    "/mcp": "Manage global MCP servers (list, edit)",
    # Registry
    "/registry": "Browse and install community skills, rules, agents, verifiers",
    # Auth
    "/auth": "Authentication (GitHub, Google) - login, logout, status",
    # Context
    "/context": "Show current context frame (tokens, reranked items)",
    "/messages": "Show current session messages in JSON format",
    "/compact": "Compact message history using LLM summarization",
    # Image
    "/paste": "Attach image from clipboard (or use Ctrl+V)",
    # Diagnostics
    "/doctor": "Check Python environment and diagnose issues",
    # Verification
    "/verify": "Run verification checks on current work",
    "/verify-loop [task]": "Run task in loop until verifications pass",
    # Setup wizard
    "/setup": "Setup wizard for rules, agents, skills, and verifiers",
    # Telegram integration
    "/telegram": "Telegram integration (setup, connect, status, test)",
    # Multiuser/Shared sessions
    "/share": "Create a shared session and get an invite code",
    "/join": "Join a shared session using an invite code",
    "/leave": "Leave the current shared session",
    "/who": "List participants in the shared session",
    "/invite": "Show the invite code for the current session",
    # Teams
    "/team": "Manage teams (create, join, leave, list, sessions, add, join-session)",
    "/help": "Show available commands",
    "/quit": "Exit the agent",
}

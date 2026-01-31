"""Agent profile definitions for different agent types.

This module provides configuration profiles for different agent types,
defining their display name, available slash commands, and other settings.
"""

from abc import ABC, abstractmethod
from typing import Optional


class AgentProfile(ABC):
    """Base class for agent profiles.

    Defines the configuration for a specific agent type including:
    - Display name and branding
    - Available slash commands
    - Mode settings
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name for the agent (e.g., 'Emdash Code')."""
        pass

    @property
    @abstractmethod
    def short_name(self) -> str:
        """Short name for prompts (e.g., 'em', 'co')."""
        pass

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Agent type identifier ('coding' or 'coworker')."""
        pass

    @property
    @abstractmethod
    def slash_commands(self) -> dict[str, str]:
        """Available slash commands and their descriptions."""
        pass

    @property
    def slash_subcommands(self) -> dict[str, dict[str, str]]:
        """Subcommands for slash commands that have them."""
        return {}

    @property
    def default_mode(self) -> str:
        """Default mode for the agent."""
        return "code"

    @property
    def supports_plan_mode(self) -> bool:
        """Whether this agent supports plan mode."""
        return False


class CodingAgentProfile(AgentProfile):
    """Profile for the coding agent (em command).

    Full-featured coding assistant with file editing, code execution,
    plan mode, and all development-focused commands.
    """

    @property
    def name(self) -> str:
        return "Emdash Code"

    @property
    def short_name(self) -> str:
        return "em"

    @property
    def agent_type(self) -> str:
        return "coding"

    @property
    def supports_plan_mode(self) -> bool:
        return True

    @property
    def slash_commands(self) -> dict[str, str]:
        return {
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
            "/team": "Manage teams (create, join, leave, list, sessions)",
            "/help": "Show available commands",
            "/quit": "Exit the agent",
        }

    @property
    def slash_subcommands(self) -> dict[str, dict[str, str]]:
        return {
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


class CoworkerAgentProfile(AgentProfile):
    """Profile for the coworker agent (co command).

    General-purpose assistant focused on research, planning, and collaboration.
    Does NOT have file editing, code execution, or plan mode.
    """

    @property
    def name(self) -> str:
        return "Emdash Coworker"

    @property
    def short_name(self) -> str:
        return "co"

    @property
    def agent_type(self) -> str:
        return "coworker"

    @property
    def default_mode(self) -> str:
        return "coworker"

    @property
    def supports_plan_mode(self) -> bool:
        return False

    @property
    def slash_commands(self) -> dict[str, str]:
        return {
            # Research
            "/research [goal]": "Deep research on a topic",
            # Status commands
            "/stats": "Show your activity statistics (tokens, sessions, activity)",
            # Model selection
            "/model": "Switch model (e.g., /model fireworks)",
            # Todo management
            "/todos": "Show current agent todo list",
            "/todo-add [title]": "Add a todo item (e.g., /todo-add Research competitors)",
            # Session management
            "/session": "Save, load, or list sessions (e.g., /session save my-research)",
            "/reset": "Reset session state",
            # Skills
            "/skills": "Manage skills (list, show, add, delete)",
            # MCP
            "/mcp": "Manage MCP servers (list, edit)",
            # Auth
            "/auth": "Authentication (Google login for Gmail, Calendar, Drive)",
            # Context
            "/messages": "Show current session messages in JSON format",
            "/compact": "Compact message history using LLM summarization",
            # Image
            "/paste": "Attach image from clipboard (or use Ctrl+V)",
            # Notes (coworker-specific)
            "/notes": "Show saved notes from this session",
            "/help": "Show available commands",
            "/quit": "Exit the agent",
        }

    @property
    def slash_subcommands(self) -> dict[str, dict[str, str]]:
        return {
            "/session": {
                "save": "Save current session",
                "load": "Load a saved session",
                "list": "List all saved sessions",
                "delete": "Delete a saved session",
            },
            "/skills": {
                "list": "List all skills",
                "show": "Show skill details",
            },
            "/mcp": {
                "list": "List MCP servers",
                "edit": "Edit MCP configuration",
            },
            "/auth": {
                "status": "Show auth status",
                "google": "Google auth (login, logout, status)",
                "google login": "Login to Google (Gmail, Calendar, Drive)",
                "google logout": "Logout from Google",
                "google status": "Show Google auth status",
            },
        }


def get_agent_profile(agent_type: str) -> AgentProfile:
    """Get the appropriate profile for an agent type.

    Args:
        agent_type: Either 'coding' or 'coworker'

    Returns:
        AgentProfile instance for the specified type
    """
    if agent_type == "coworker":
        return CoworkerAgentProfile()
    return CodingAgentProfile()

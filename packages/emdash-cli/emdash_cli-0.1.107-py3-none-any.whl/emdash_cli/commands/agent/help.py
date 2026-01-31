"""Contextual help system for emdash CLI.

Provides detailed help for commands with zen styling.
"""

from rich.console import Console

from ...design import (
    Colors,
    STATUS_ACTIVE,
    DOT_BULLET,
    ARROW_PROMPT,
    header,
    footer,
    SEPARATOR_WIDTH,
)

console = Console()

# Detailed help for each command
COMMAND_HELP = {
    "/help": {
        "description": "Show available commands and help",
        "usage": ["/help", "/help <command>"],
        "examples": ["/help", "/help agents"],
    },
    "/plan": {
        "description": "Switch to plan mode for exploration and architecture",
        "usage": ["/plan"],
        "details": """Plan mode is read-only. The agent will explore your codebase,
analyze architecture, and create implementation plans without
making any changes.""",
        "examples": ["/plan"],
    },
    "/code": {
        "description": "Switch to code mode for implementation",
        "usage": ["/code"],
        "details": """Code mode allows the agent to make changes to your codebase.
Use this after approving a plan or for direct implementation tasks.""",
        "examples": ["/code"],
    },
    "/agents": {
        "description": "Manage custom agents for specialized tasks",
        "usage": [
            "/agents",
            "/agents create <name>",
            "/agents show <name>",
            "/agents edit <name>",
            "/agents delete <name>",
        ],
        "details": """Custom agents extend emdash with specialized capabilities.
Each agent has its own prompt, tools, and behavior configuration.""",
        "examples": [
            "/agents",
            "/agents create code-reviewer",
            "/agents edit planner",
        ],
    },
    "/rules": {
        "description": "Configure rules that guide agent behavior",
        "usage": ["/rules", "/rules create", "/rules list"],
        "details": """Rules define coding standards, preferences, and project
conventions. The agent follows these guidelines when working
on your codebase.""",
        "examples": ["/rules", "/rules create"],
    },
    "/skills": {
        "description": "Manage reusable skill templates",
        "usage": ["/skills", "/skills create", "/skills list"],
        "details": """Skills are reusable prompt templates that can be invoked
for common tasks like code review, testing, or documentation.""",
        "examples": ["/skills", "/skills create"],
    },
    "/stats": {
        "description": "View your activity statistics",
        "usage": ["/stats", "/stats --tokens", "/stats --sessions"],
        "details": """Displays your activity metrics including total sessions,
token usage breakdown (input/output/thinking), and model usage stats.
Data is aggregated from your conversation history.""",
        "examples": ["/stats", "/stats --tokens"],
    },
    "/session": {
        "description": "Manage conversation sessions",
        "usage": ["/session", "/session save <name>", "/session load <name>"],
        "details": """Sessions preserve conversation context. Save sessions to
continue work later or switch between different tasks.""",
        "examples": [
            "/session",
            "/session save my-feature",
            "/session load my-feature",
        ],
    },
    "/verify": {
        "description": "Run verification checks on the codebase",
        "usage": ["/verify", "/verify <check>"],
        "details": """Runs configured verifiers (tests, linting, type checking)
to ensure code quality. Use /verify-loop for automatic fixing.""",
        "examples": ["/verify", "/verify tests"],
    },
    "/verify-loop": {
        "description": "Run verification loop with automatic fixing",
        "usage": ["/verify-loop <task>"],
        "details": """Runs verifiers repeatedly, letting the agent fix issues
until all checks pass or you stop the loop.""",
        "examples": ["/verify-loop fix the failing tests"],
    },
    "/pr": {
        "description": "Review or create pull requests",
        "usage": ["/pr <url>", "/pr create"],
        "details": """Review GitHub pull requests or create new ones.
Provides detailed analysis of changes and suggestions.""",
        "examples": [
            "/pr https://github.com/org/repo/pull/123",
            "/pr create",
        ],
    },
    "/research": {
        "description": "Research a topic using web search",
        "usage": ["/research <query>"],
        "details": """Searches the web for information and provides a summary.
Useful for finding documentation, examples, or solutions.""",
        "examples": ["/research react hooks best practices"],
    },
    "/todos": {
        "description": "View and manage task list",
        "usage": ["/todos", "/todo-add <task>"],
        "details": """Track tasks and progress. The agent can also add todos
during planning and implementation.""",
        "examples": ["/todos", "/todo-add implement auth"],
    },
    "/context": {
        "description": "View current context information",
        "usage": ["/context"],
        "details": """Shows token usage, context breakdown, and reranked items
in the current session.""",
        "examples": ["/context"],
    },
    "/compact": {
        "description": "Compact conversation context",
        "usage": ["/compact"],
        "details": """Summarizes the conversation to reduce context size while
preserving important information. Use when hitting limits.""",
        "examples": ["/compact"],
    },
    "/status": {
        "description": "Show current status and configuration",
        "usage": ["/status"],
        "details": """Displays current mode, model, session info, and
active configuration.""",
        "examples": ["/status"],
    },
    "/stats": {
        "description": "Show your activity statistics",
        "usage": ["/stats", "/stats --tokens", "/stats --sessions"],
        "details": """Displays your usage statistics including total sessions,
token breakdown (input/output/thinking), and recent activity.
Use --tokens for detailed token usage, --sessions for session list.""",
        "examples": [
            "/stats",
            "/stats --tokens",
            "/stats --sessions",
        ],
    },
    "/doctor": {
        "description": "Run diagnostic checks",
        "usage": ["/doctor"],
        "details": """Checks environment, dependencies, and configuration
for potential issues.""",
        "examples": ["/doctor"],
    },
    "/auth": {
        "description": "Manage authentication (GitHub and Google)",
        "usage": ["/auth", "/auth login", "/auth google login", "/auth google status"],
        "details": """Manage authentication for GitHub and Google services.

GitHub: Enables PR reviews, issue management, and repository access.
Google: Enables Gmail, Calendar, Drive, Docs, and Sheets access.

Subcommands:
  /auth              - Show all auth status
  /auth login        - Login to GitHub
  /auth logout       - Logout from GitHub
  /auth google login - Login to Google (opens browser)
  /auth google logout - Logout from Google
  /auth google status - Show Google auth status""",
        "examples": ["/auth", "/auth login", "/auth google login"],
    },
    "/setup": {
        "description": "Run interactive setup wizard",
        "usage": ["/setup", "/setup rules", "/setup agents"],
        "details": """AI-assisted setup for configuring rules, agents, skills,
and verifiers with templates and guidance.""",
        "examples": ["/setup", "/setup rules"],
    },
    "/reset": {
        "description": "Reset current session",
        "usage": ["/reset"],
        "details": """Clears the current session context. Use to start fresh
without closing the CLI.""",
        "examples": ["/reset"],
    },
    "/quit": {
        "description": "Exit emdash",
        "usage": ["/quit", "/exit", "/q"],
        "examples": ["/quit"],
    },
    # Multiuser commands
    "/share": {
        "description": "Create a shared session and get an invite code",
        "usage": ["/share", "/share <display-name>"],
        "details": """Creates a shared session that others can join with the invite code.
All participants see agent responses and tool calls in real-time.
Messages are queued when the agent is busy processing.""",
        "examples": ["/share", "/share Alice"],
    },
    "/join": {
        "description": "Join a shared session using an invite code",
        "usage": ["/join <invite-code>"],
        "details": """Join an existing shared session created by another user.
You'll receive all agent events and can send messages (queued if agent is busy).
The invite code is case-insensitive.""",
        "examples": ["/join ABC123", "/join abc-123"],
    },
    "/leave": {
        "description": "Leave the current shared session",
        "usage": ["/leave"],
        "details": """Leave the shared session you're currently in.
Other participants can continue using the session.""",
        "examples": ["/leave"],
    },
    "/who": {
        "description": "List participants in the shared session",
        "usage": ["/who"],
        "details": """Shows all participants in the current shared session,
including their role (owner/editor), online status, and join time.""",
        "examples": ["/who"],
    },
    "/invite": {
        "description": "Show the invite code for the current session",
        "usage": ["/invite"],
        "details": """Displays the invite code for the current shared session.
Share this code with others so they can join.""",
        "examples": ["/invite"],
    },
}


def show_command_help(command: str) -> None:
    """Show detailed help for a specific command."""
    # Normalize command
    if not command.startswith("/"):
        command = "/" + command

    help_info = COMMAND_HELP.get(command)

    if not help_info:
        console.print(f"  [{Colors.ERROR}]Unknown command: {command}[/{Colors.ERROR}]")
        console.print(f"  [{Colors.DIM}]Type /help to see all commands[/{Colors.DIM}]")
        return

    console.print()
    console.print(f"[{Colors.MUTED}]{header(command, SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  {help_info['description']}")
    console.print()

    # Usage
    console.print(f"  [{Colors.PRIMARY}]Usage:[/{Colors.PRIMARY}]")
    for usage in help_info.get("usage", []):
        console.print(f"    {usage}")
    console.print()

    # Details
    if "details" in help_info:
        console.print(f"  [{Colors.DIM}]{help_info['details']}[/{Colors.DIM}]")
        console.print()

    # Examples
    if "examples" in help_info:
        console.print(f"  [{Colors.PRIMARY}]Examples:[/{Colors.PRIMARY}]")
        for example in help_info["examples"]:
            console.print(f"    [{Colors.SUCCESS}]{example}[/{Colors.SUCCESS}]")
        console.print()

    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()


def show_quick_tips() -> None:
    """Show quick tips for new users."""
    console.print()
    console.print(f"[{Colors.MUTED}]{header('Quick Tips', 35)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.DIM}]Keyboard shortcuts:[/{Colors.DIM}]")
    console.print(f"    {DOT_BULLET} Ctrl+C to cancel")
    console.print(f"    {DOT_BULLET} Esc during execution to interrupt")
    console.print(f"    {DOT_BULLET} Alt+Enter for multiline input")
    console.print()
    console.print(f"  [{Colors.DIM}]File references:[/{Colors.DIM}]")
    console.print(f"    {DOT_BULLET} Use @filename to include files")
    console.print(f"    {DOT_BULLET} Tab completion for @file paths")
    console.print()
    console.print(f"[{Colors.MUTED}]{footer(35)}[/{Colors.MUTED}]")
    console.print()

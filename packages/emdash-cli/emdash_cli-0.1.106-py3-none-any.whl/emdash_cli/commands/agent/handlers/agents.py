"""Handler for /agents command."""

import os
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from ..menus import show_agents_interactive_menu, prompt_agent_name, confirm_delete
from ....design import (
    Colors,
    header,
    footer,
    SEPARATOR_WIDTH,
    STATUS_ACTIVE,
    ARROW_PROMPT,
    print_error,
)

console = Console()


def create_agent(name: str) -> bool:
    """Create a new agent with the given name."""
    agents_dir = Path.cwd() / ".emdash" / "agents"
    agent_file = agents_dir / f"{name}.md"

    if agent_file.exists():
        console.print(f"[yellow]Agent '{name}' already exists[/yellow]")
        return False

    agents_dir.mkdir(parents=True, exist_ok=True)

    template = f'''---
description: Custom agent for specific tasks
tools: [grep, glob, read_file, semantic_search]
# rules: [typescript, security]  # Optional: reference rules from .emdash/rules/
# skills: [code-review]  # Optional: reference skills from .emdash/skills/
# verifiers: [eslint]  # Optional: reference verifiers from .emdash/verifiers.json
---

# System Prompt

You are a specialized assistant for {name.replace("-", " ")} tasks.

## Your Mission

Describe what this agent should accomplish:
- Task 1
- Task 2
- Task 3

## Approach

1. **Step One**
   - Details about the first step

2. **Step Two**
   - Details about the second step

## Output Format

Describe how the agent should format its responses.
'''
    agent_file.write_text(template)
    console.print()
    console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] [{Colors.TEXT}]created:[/{Colors.TEXT}] {name}")
    console.print(f"  [{Colors.DIM}]{agent_file}[/{Colors.DIM}]")
    console.print()
    return True


def show_agent_details(name: str) -> None:
    """Show detailed view of an agent."""
    from emdash_core.agent.toolkits import get_custom_agent

    builtin_agents = ["Explore", "Plan"]

    console.print()
    console.print(f"[{Colors.MUTED}]{header(name, SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()

    if name in builtin_agents:
        console.print(f"  [{Colors.DIM}]type[/{Colors.DIM}]      [{Colors.MUTED}]built-in[/{Colors.MUTED}]")
        if name == "Explore":
            console.print(f"  [{Colors.DIM}]desc[/{Colors.DIM}]      Fast codebase exploration (read-only)")
            console.print(f"  [{Colors.DIM}]tools[/{Colors.DIM}]     glob, grep, read_file, list_files, semantic_search")
        elif name == "Plan":
            console.print(f"  [{Colors.DIM}]desc[/{Colors.DIM}]      Design implementation plans")
            console.print(f"  [{Colors.DIM}]tools[/{Colors.DIM}]     glob, grep, read_file, list_files, semantic_search")
        console.print()
        console.print(f"  [{Colors.DIM}]Built-in agents cannot be edited or deleted.[/{Colors.DIM}]")
    else:
        agent = get_custom_agent(name, Path.cwd())
        if agent:
            console.print(f"  [{Colors.DIM}]type[/{Colors.DIM}]      [{Colors.PRIMARY}]custom[/{Colors.PRIMARY}]")

            if agent.description:
                console.print(f"  [{Colors.DIM}]desc[/{Colors.DIM}]      {agent.description}")

            if agent.model:
                console.print(f"  [{Colors.DIM}]model[/{Colors.DIM}]     {agent.model}")

            if agent.tools:
                console.print(f"  [{Colors.DIM}]tools[/{Colors.DIM}]     {', '.join(agent.tools)}")

            if agent.mcp_servers:
                console.print()
                console.print(f"  [{Colors.DIM}]mcp servers:[/{Colors.DIM}]")
                for server in agent.mcp_servers:
                    status = f"[{Colors.SUCCESS}]●[/{Colors.SUCCESS}]" if server.enabled else f"[{Colors.MUTED}]○[/{Colors.MUTED}]"
                    console.print(f"    {status} [{Colors.PRIMARY}]{server.name}[/{Colors.PRIMARY}]")
                    console.print(f"      [{Colors.DIM}]{server.command} {' '.join(server.args)}[/{Colors.DIM}]")

            if agent.rules:
                console.print(f"  [{Colors.DIM}]rules[/{Colors.DIM}]     {', '.join(agent.rules)}")

            if agent.skills:
                console.print(f"  [{Colors.DIM}]skills[/{Colors.DIM}]    {', '.join(agent.skills)}")

            if agent.verifiers:
                console.print(f"  [{Colors.DIM}]verify[/{Colors.DIM}]    {', '.join(agent.verifiers)}")

            if agent.file_path:
                console.print()
                console.print(f"  [{Colors.DIM}]file[/{Colors.DIM}]      {agent.file_path}")

            if agent.system_prompt:
                console.print()
                console.print(f"  [{Colors.DIM}]prompt preview:[/{Colors.DIM}]")
                preview = agent.system_prompt[:250]
                if len(agent.system_prompt) > 250:
                    preview += "..."
                for line in preview.split('\n')[:6]:
                    console.print(f"    [{Colors.MUTED}]{line}[/{Colors.MUTED}]")
        else:
            console.print(f"  [{Colors.WARNING}]Agent '{name}' not found[/{Colors.WARNING}]")

    console.print()
    console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")


def delete_agent(name: str) -> bool:
    """Delete a custom agent."""
    agents_dir = Path.cwd() / ".emdash" / "agents"
    agent_file = agents_dir / f"{name}.md"

    if not agent_file.exists():
        console.print(f"[yellow]Agent file not found: {agent_file}[/yellow]")
        return False

    if confirm_delete(name):
        agent_file.unlink()
        console.print(f"[green]Deleted agent: {name}[/green]")
        return True
    else:
        console.print("[dim]Cancelled[/dim]")
        return False


def edit_agent(name: str) -> None:
    """Open agent file in editor."""
    agents_dir = Path.cwd() / ".emdash" / "agents"
    agent_file = agents_dir / f"{name}.md"

    if not agent_file.exists():
        console.print(f"[yellow]Agent file not found: {agent_file}[/yellow]")
        return

    # Try to open in editor
    editor = os.environ.get("EDITOR", "")
    if not editor:
        # Try common editors
        for ed in ["code", "vim", "nano", "vi"]:
            try:
                subprocess.run(["which", ed], capture_output=True, check=True)
                editor = ed
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

    if editor:
        console.print(f"[dim]Opening {agent_file} in {editor}...[/dim]")
        try:
            subprocess.run([editor, str(agent_file)])
        except Exception as e:
            print_error(e, "Failed to open editor")
            console.print(f"[dim]Edit manually: {agent_file}[/dim]")
    else:
        console.print(f"[yellow]No editor found. Edit manually:[/yellow]")
        console.print(f"  {agent_file}")


def chat_edit_agent(name: str, client, renderer, model, max_iterations, render_with_interrupt) -> None:
    """Start a chat session to edit an agent with AI assistance."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style

    agents_dir = Path.cwd() / ".emdash" / "agents"
    agent_file = agents_dir / f"{name}.md"

    if not agent_file.exists():
        console.print(f"  [{Colors.WARNING}]Agent file not found: {agent_file}[/{Colors.WARNING}]")
        return

    # Read current content
    content = agent_file.read_text()

    console.print()
    console.print(f"[{Colors.MUTED}]{header(f'Edit: {name}', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.DIM}]Describe changes. Type 'done' to finish.[/{Colors.DIM}]")
    console.print()

    chat_style = Style.from_dict({
        "prompt": f"{Colors.PRIMARY} bold",
    })

    ps = PromptSession(style=chat_style)
    chat_session_id = None
    first_message = True

    # Chat loop
    while True:
        try:
            user_input = ps.prompt([("class:prompt", "› ")]).strip()

            if not user_input:
                continue

            if user_input.lower() in ("done", "quit", "exit", "q"):
                console.print("[dim]Finished editing agent[/dim]")
                break

            # First message includes agent context
            if first_message:
                message_with_context = f"""I want to edit my custom agent "{name}".

**File:** `{agent_file}`

**Current content:**
```markdown
{content}
```

**My request:** {user_input}

Please make the requested changes using the Edit tool."""
                stream = client.agent_chat_stream(
                    message=message_with_context,
                    model=model,
                    max_iterations=max_iterations,
                    options={"mode": "code"},
                )
                first_message = False
            elif chat_session_id:
                stream = client.agent_continue_stream(
                    chat_session_id, user_input
                )
            else:
                stream = client.agent_chat_stream(
                    message=user_input,
                    model=model,
                    max_iterations=max_iterations,
                    options={"mode": "code"},
                )

            result = render_with_interrupt(renderer, stream)
            if result and result.get("session_id"):
                chat_session_id = result["session_id"]

        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print("[dim]Finished editing agent[/dim]")
            break
        except Exception as e:
            print_error(e)


def chat_create_agent(client, renderer, model, max_iterations, render_with_interrupt) -> str | None:
    """Start a chat session to create a new agent with AI assistance.

    Returns:
        The name of the created agent, or None if cancelled.
    """
    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style

    agents_dir = Path.cwd() / ".emdash" / "agents"

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Create Agent', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.DIM}]Describe your agent. AI will help design it.[/{Colors.DIM}]")
    console.print(f"  [{Colors.DIM}]Type 'done' to finish.[/{Colors.DIM}]")
    console.print()

    chat_style = Style.from_dict({
        "prompt": f"{Colors.PRIMARY} bold",
    })

    ps = PromptSession(style=chat_style)
    chat_session_id = None
    first_message = True

    # Ensure agents directory exists
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Chat loop
    while True:
        try:
            user_input = ps.prompt([("class:prompt", "› ")]).strip()

            if not user_input:
                continue

            if user_input.lower() in ("done", "quit", "exit", "q"):
                console.print("[dim]Finished[/dim]")
                break

            # First message includes context about agents
            if first_message:
                message_with_context = f"""I want to create a new custom agent for my project.

**Agents directory:** `{agents_dir}`

Agents are markdown files with YAML frontmatter that define specialized assistants with custom system prompts and tools.

**Agent file format:**
```markdown
---
description: Brief description of what this agent does
model: claude-sonnet  # optional, defaults to main model
tools: [grep, glob, read_file, edit_file, bash]  # tools this agent can use
mcp_servers:  # optional, MCP servers for this agent
  - name: server-name
    command: npx
    args: ["-y", "@modelcontextprotocol/server-name"]
---

# System Prompt

You are a specialized assistant for [purpose].

## Your Mission
[What this agent should accomplish]

## Approach
[How this agent should work]

## Output Format
[How the agent should format responses]
```

**Available tools:** grep, glob, read_file, edit_file, write_file, bash, semantic_search, list_files, etc.

**My request:** {user_input}

Please help me design and create an agent. Ask me questions about what I need, then use the Write tool to create the file at `{agents_dir}/<agent-name>.md`."""
                stream = client.agent_chat_stream(
                    message=message_with_context,
                    model=model,
                    max_iterations=max_iterations,
                    options={"mode": "code"},
                )
                first_message = False
            elif chat_session_id:
                stream = client.agent_continue_stream(
                    chat_session_id, user_input
                )
            else:
                stream = client.agent_chat_stream(
                    message=user_input,
                    model=model,
                    max_iterations=max_iterations,
                    options={"mode": "code"},
                )

            result = render_with_interrupt(renderer, stream)
            if result and result.get("session_id"):
                chat_session_id = result["session_id"]

        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print("[dim]Cancelled[/dim]")
            break
        except Exception as e:
            print_error(e)

    return None


def handle_agents(args: str, client, renderer, model, max_iterations, render_with_interrupt) -> None:
    """Handle /agents command."""
    from prompt_toolkit import PromptSession

    # Handle subcommands for backward compatibility
    if args:
        subparts = args.split(maxsplit=1)
        subcommand = subparts[0].lower()
        subargs = subparts[1] if len(subparts) > 1 else ""

        if subcommand == "create" and subargs:
            create_agent(subargs.strip().lower().replace(" ", "-"))
        elif subcommand == "show" and subargs:
            show_agent_details(subargs.strip())
        elif subcommand == "delete" and subargs:
            delete_agent(subargs.strip())
        elif subcommand == "edit" and subargs:
            edit_agent(subargs.strip())
        else:
            console.print("[yellow]Usage: /agents [create|show|delete|edit] <name>[/yellow]")
            console.print("[dim]Or just /agents for interactive menu[/dim]")
    else:
        # Interactive menu
        while True:
            action, agent_name = show_agents_interactive_menu()

            if action == "cancel":
                break
            elif action == "view":
                show_agent_details(agent_name)
                # After viewing, show options based on agent type
                is_custom = agent_name not in ("Explore", "Plan")
                try:
                    if is_custom:
                        console.print("[cyan]'c'[/cyan] chat • [cyan]'e'[/cyan] edit • [red]'d'[/red] delete • [dim]Enter back[/dim]", end="")
                    else:
                        console.print("[dim]Press Enter to go back...[/dim]", end="")
                    ps = PromptSession()
                    resp = ps.prompt(" ").strip().lower()
                    if is_custom and resp == 'c':
                        chat_edit_agent(agent_name, client, renderer, model, max_iterations, render_with_interrupt)
                    elif is_custom and resp == 'e':
                        edit_agent(agent_name)
                    elif is_custom and resp == 'd':
                        if delete_agent(agent_name):
                            continue  # Refresh menu after deletion
                    console.print()  # Add spacing before menu reappears
                except (KeyboardInterrupt, EOFError):
                    break
            elif action == "create":
                # Use AI-assisted creation
                chat_create_agent(client, renderer, model, max_iterations, render_with_interrupt)
            elif action == "delete":
                delete_agent(agent_name)
            elif action == "edit":
                edit_agent(agent_name)
                break  # Exit menu after editing

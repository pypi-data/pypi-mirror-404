"""Handler for /verify command - run verification checks."""

import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from emdash_core.agent.verifier import VerifierManager, VerificationReport
from ....design import print_error

console = Console()


def get_git_diff() -> str:
    """Get git diff of staged and unstaged changes."""
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )
        return result.stdout
    except Exception:
        return ""


def get_changed_files() -> list[str]:
    """Get list of changed files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except Exception:
        return []


def display_report(report: VerificationReport) -> None:
    """Display verification report."""
    # Create results table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Status", width=6)
    table.add_column("Verifier", style="cyan")
    table.add_column("Duration", justify="right")
    table.add_column("Details")

    for result in report.results:
        status = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
        duration = f"{result.duration:.1f}s"

        # Build details
        if result.passed:
            details = "[dim]OK[/dim]"
        elif result.issues:
            details = result.issues[0][:50]
            if len(result.issues) > 1:
                details += f" (+{len(result.issues) - 1} more)"
        else:
            details = result.output[:50] if result.output else "Failed"

        table.add_row(status, result.name, duration, details)

    console.print(table)
    console.print()

    # Show summary
    if report.all_passed:
        console.print(f"[bold green]✓ {report.summary}[/bold green]")
    else:
        console.print(f"[bold red]✗ {report.summary}[/bold red]")

        # Show detailed failures
        for result in report.get_failures():
            console.print()
            console.print(Panel(
                result.output[:1000] if result.output else "No output",
                title=f"[red]{result.name}[/red]",
                border_style="red",
            ))


def build_retry_prompt(original_task: str, report: VerificationReport) -> str:
    """Build a retry prompt that includes failure information."""
    failures = report.get_failures()

    failure_text = "\n".join([
        f"- **{r.name}**: {', '.join(r.issues[:3]) if r.issues else r.output[:100]}"
        for r in failures
    ])

    return f"""Continue working on this task. Previous attempt had verification failures:

{failure_text}

Original task: {original_task}

Fix the issues and complete the task."""


def prompt_retry_menu() -> str:
    """Prompt user for action after failed verification.

    Returns:
        One of: 'retry', 'approve', 'stop'
    """
    from prompt_toolkit import PromptSession

    console.print()
    console.print("[bold]What would you like to do?[/bold]")
    console.print("  [cyan]r[/cyan] Retry - feed failures back to agent")
    console.print("  [green]a[/green] Approve - accept despite failures")
    console.print("  [red]s[/red] Stop - end the loop")
    console.print()

    try:
        ps = PromptSession()
        choice = ps.prompt("Choice [r/a/s]: ").strip().lower()

        if choice in ('r', 'retry'):
            return 'retry'
        elif choice in ('a', 'approve'):
            return 'approve'
        else:
            return 'stop'
    except (KeyboardInterrupt, EOFError):
        return 'stop'


def show_verifiers_menu() -> tuple[str, str]:
    """Show interactive verifiers menu.

    Returns:
        Tuple of (action, verifier_name) where action is one of:
        - 'run': Run all verifiers
        - 'create': Create new verifier
        - 'delete': Delete verifier
        - 'cancel': User cancelled
    """
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    manager = VerifierManager(Path.cwd())
    verifiers = manager.verifiers

    # Build menu items
    menu_items = []

    # Add "Run All" as first option if verifiers exist
    if verifiers:
        menu_items.append(("▶ Run All Verifiers", f"Run {len(verifiers)} verifier(s)", None, "run"))

    # Add existing verifiers
    for v in verifiers:
        vtype = "[cmd]" if v.type == "command" else "[llm]"
        desc = v.command[:40] if v.command else (v.prompt[:40] if v.prompt else "")
        menu_items.append((v.name, f"{vtype} {desc}", v.name, "view"))

    # Add create option
    menu_items.append(("+ Create New Verifier", "Add a verifier with AI assistance", None, "create"))

    selected_index = [0]
    result = [("cancel", "")]

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_index[0] = (selected_index[0] - 1) % len(menu_items)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_index[0] = (selected_index[0] + 1) % len(menu_items)

    @kb.add("enter")
    def select(event):
        item = menu_items[selected_index[0]]
        name, desc, verifier_name, action = item
        result[0] = (action, verifier_name or "")
        event.app.exit()

    @kb.add("d")
    def delete_verifier(event):
        item = menu_items[selected_index[0]]
        name, desc, verifier_name, action = item
        if verifier_name:  # Can only delete actual verifiers
            result[0] = ("delete", verifier_name)
            event.app.exit()

    @kb.add("n")
    def new_verifier(event):
        result[0] = ("create", "")
        event.app.exit()

    @kb.add("r")
    def run_all(event):
        if verifiers:
            result[0] = ("run", "")
            event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    @kb.add("q")
    def cancel(event):
        result[0] = ("cancel", "")
        event.app.exit()

    def get_formatted_menu():
        lines = [("class:title", "Verifiers\n\n")]

        if not verifiers:
            lines.append(("class:dim", "No verifiers configured yet.\n\n"))

        for i, (name, desc, vname, action) in enumerate(menu_items):
            is_selected = i == selected_index[0]
            prefix = "❯ " if is_selected else "  "

            if action in ("create", "run"):
                if is_selected:
                    lines.append(("class:action-selected", f"{prefix}{name}\n"))
                else:
                    lines.append(("class:action", f"{prefix}{name}\n"))
            else:
                if is_selected:
                    lines.append(("class:item-selected", f"{prefix}{name}"))
                    lines.append(("class:desc-selected", f" {desc}\n"))
                else:
                    lines.append(("class:item", f"{prefix}{name}"))
                    lines.append(("class:desc", f" {desc}\n"))

        lines.append(("class:hint", "\n↑/↓ navigate • Enter select • n new • d delete • r run • q quit"))
        return lines

    style = Style.from_dict({
        "title": "#00ccff bold",
        "dim": "#666666",
        "item": "#00ccff",
        "item-selected": "#00cc66 bold",
        "action": "#ffcc00",
        "action-selected": "#ffcc00 bold",
        "desc": "#666666",
        "desc-selected": "#00cc66",
        "hint": "#888888 italic",
    })

    height = len(menu_items) + 5

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_menu),
                height=height,
            ),
        ])
    )

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        full_screen=False,
    )

    console.print()

    try:
        app.run()
    except (KeyboardInterrupt, EOFError):
        result[0] = ("cancel", "")

    console.print()
    return result[0]


def chat_create_verifier(client, renderer, model, max_iterations, render_with_interrupt) -> None:
    """Start a chat session to create a new verifier with AI assistance."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style

    verifiers_file = Path.cwd() / ".emdash" / "verifiers.json"

    console.print()
    console.print("[bold cyan]Create New Verifier[/bold cyan]")
    console.print("[dim]Describe what verification you want. The AI will help you configure it.[/dim]")
    console.print("[dim]Type 'done' to finish, Ctrl+C to cancel[/dim]")
    console.print()

    chat_style = Style.from_dict({
        "prompt": "#00cc66 bold",
    })

    ps = PromptSession(style=chat_style)
    chat_session_id = None
    first_message = True

    # Ensure .emdash directory exists
    verifiers_file.parent.mkdir(parents=True, exist_ok=True)

    # Get current config
    manager = VerifierManager(Path.cwd())
    current_config = manager.get_config()

    # Chat loop
    while True:
        try:
            user_input = ps.prompt([("class:prompt", "› ")]).strip()

            if not user_input:
                continue

            if user_input.lower() in ("done", "quit", "exit", "q"):
                console.print("[dim]Finished[/dim]")
                break

            # First message includes context
            if first_message:
                current_json = "{\n  \"verifiers\": [],\n  \"max_attempts\": 3\n}"
                if current_config.get("verifiers"):
                    import json
                    current_json = json.dumps(current_config, indent=2)

                message_with_context = f"""I want to add a new verifier to my project.

**Verifiers file:** `{verifiers_file}`

**Current configuration:**
```json
{current_json}
```

**Config options:**
- `max_attempts`: Maximum verification loop attempts (default: 3). Set to `0` for infinite attempts.

**Verifier types:**
1. **Command verifier** - runs a shell command, passes if exit code is 0:
   ```json
   {{"type": "command", "name": "tests", "command": "npm test", "timeout": 120}}
   ```

2. **LLM verifier** - asks gpt-oss-120b to review, passes if AI says pass:
   ```json
   {{"type": "llm", "name": "review", "prompt": "Review the git diff for bugs"}}
   ```

**My request:** {user_input}

Please help me create a verifier. Ask clarifying questions if needed, then use the Write tool to update `{verifiers_file}` with the new verifier added to the verifiers array."""
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


def delete_verifier(name: str) -> bool:
    """Delete a verifier by name."""
    from prompt_toolkit import PromptSession
    import json

    manager = VerifierManager(Path.cwd())
    config = manager.get_config()

    # Find the verifier
    verifiers = config.get("verifiers", [])
    found = any(v.get("name") == name for v in verifiers)

    if not found:
        console.print(f"[yellow]Verifier '{name}' not found[/yellow]")
        return False

    # Confirm deletion
    console.print()
    console.print(f"[yellow]Delete verifier '{name}'?[/yellow]")
    console.print("[dim]Type 'yes' to confirm.[/dim]")

    try:
        ps = PromptSession()
        response = ps.prompt("Confirm > ").strip().lower()
        if response not in ("yes", "y"):
            console.print("[dim]Cancelled[/dim]")
            return False
    except (KeyboardInterrupt, EOFError):
        return False

    # Remove the verifier
    config["verifiers"] = [v for v in verifiers if v.get("name") != name]
    manager.save_config(config)
    console.print(f"[green]Deleted verifier: {name}[/green]")
    return True


def handle_verify(args: str, client=None, renderer=None, model=None, max_iterations=10, render_with_interrupt=None) -> None:
    """Handle /verify command - run verification checks or manage verifiers."""
    manager = VerifierManager(Path.cwd())

    # If args provided, handle subcommands
    if args:
        subparts = args.split(maxsplit=1)
        subcommand = subparts[0].lower()

        if subcommand == "run":
            # Run verifiers directly
            _run_verifiers(manager)
        elif subcommand in ("add", "create", "new"):
            if client and renderer:
                chat_create_verifier(client, renderer, model, max_iterations, render_with_interrupt)
            else:
                console.print("[yellow]AI assistance not available. Use /setup for guided creation.[/yellow]")
        elif subcommand == "list":
            _list_verifiers(manager)
        else:
            console.print("[yellow]Usage: /verify [run|add|list][/yellow]")
            console.print("[dim]Or just /verify for interactive menu[/dim]")
        return

    # No args - show interactive menu if we have client, otherwise just run
    if client and renderer:
        while True:
            action, verifier_name = show_verifiers_menu()

            if action == "cancel":
                break
            elif action == "run":
                _run_verifiers(manager)
                break  # Exit menu after running
            elif action == "create":
                chat_create_verifier(client, renderer, model, max_iterations, render_with_interrupt)
                # Refresh manager after creating
                manager = VerifierManager(Path.cwd())
            elif action == "delete":
                delete_verifier(verifier_name)
                manager = VerifierManager(Path.cwd())
            elif action == "view":
                _show_verifier_details(manager, verifier_name)
    else:
        # No client - just run verifiers
        _run_verifiers(manager)


def _run_verifiers(manager: VerifierManager) -> None:
    """Run all verifiers and display results."""
    console.print()

    if not manager.verifiers:
        console.print("[yellow]No verifiers configured.[/yellow]")
        console.print("[dim]Use /verify add or /setup to create verifiers[/dim]")
        console.print()
        return

    console.print(f"[bold]Running {len(manager.verifiers)} verifier(s)...[/bold]")

    context = {
        "git_diff": get_git_diff(),
        "files_changed": get_changed_files(),
    }

    # Run with spinner for better UX
    with console.status("[cyan]Running verifiers...", spinner="dots"):
        report = manager.run_all(context)

    console.print()
    display_report(report)
    console.print()


def _list_verifiers(manager: VerifierManager) -> None:
    """List all configured verifiers."""
    console.print()
    if not manager.verifiers:
        console.print("[dim]No verifiers configured.[/dim]")
    else:
        console.print("[bold cyan]Verifiers[/bold cyan]\n")
        for v in manager.verifiers:
            vtype = "[cmd]" if v.type == "command" else "[llm]"
            desc = v.command if v.command else v.prompt
            console.print(f"  [cyan]{v.name}[/cyan] {vtype} - {desc[:50]}")
    console.print()


def _show_verifier_details(manager: VerifierManager, name: str) -> None:
    """Show details of a specific verifier."""
    console.print()
    console.print("[dim]─" * 50 + "[/dim]")

    for v in manager.verifiers:
        if v.name == name:
            console.print(f"\n[bold cyan]{v.name}[/bold cyan]\n")
            console.print(f"[bold]Type:[/bold] {v.type}")
            if v.type == "command":
                console.print(f"[bold]Command:[/bold] {v.command}")
                console.print(f"[bold]Timeout:[/bold] {v.timeout}s")
            else:
                console.print(f"[bold]Prompt:[/bold] {v.prompt}")
                console.print(f"[bold]Model:[/bold] gpt-oss-120b")
            console.print(f"[bold]Enabled:[/bold] {v.enabled}")
            break
    else:
        console.print(f"\n[yellow]Verifier '{name}' not found[/yellow]")

    console.print()
    console.print("[dim]─" * 50 + "[/dim]")


def run_verification(goal: str | None = None) -> tuple[VerificationReport, bool]:
    """Run verification and return report.

    Args:
        goal: Optional goal/task being verified

    Returns:
        Tuple of (report, should_continue_loop)
        should_continue_loop is True if user wants to retry
    """
    manager = VerifierManager(Path.cwd())

    if not manager.verifiers:
        console.print("[yellow]No verifiers configured. Skipping verification.[/yellow]")
        return VerificationReport(results=[], all_passed=True, summary="No verifiers"), False

    console.print()
    console.print(f"[bold cyan]Running {len(manager.verifiers)} verifier(s)...[/bold cyan]")

    # Build context
    context = {
        "goal": goal,
        "git_diff": get_git_diff(),
        "files_changed": get_changed_files(),
    }

    # Run verifiers with spinner
    with console.status("[cyan]Running verifiers...", spinner="dots"):
        report = manager.run_all(context)

    console.print()

    # Display results
    display_report(report)

    return report, not report.all_passed


def handle_verify_loop(
    task: str,
    run_task_fn,
    max_attempts: int = 3,
) -> bool:
    """Run a task in a verification loop.

    Args:
        task: The task to run
        run_task_fn: Function to run the task (takes task string, returns None)
        max_attempts: Maximum number of attempts (0 = infinite)

    Returns:
        True if completed successfully, False if stopped
    """
    manager = VerifierManager(Path.cwd())
    config = manager.get_config()
    max_attempts = config.get("max_attempts", max_attempts)
    is_infinite = max_attempts == 0

    if not manager.verifiers:
        console.print("[yellow]No verifiers configured.[/yellow]")
        console.print("[dim]Configure .emdash/verifiers.json to use verify-loop[/dim]")
        console.print()
        console.print("[dim]Running task without verification...[/dim]")
        run_task_fn(task)
        return True

    current_task = task
    attempt_count = 0

    while is_infinite or attempt_count < max_attempts:
        attempt_count += 1

        # Show attempt header
        console.print()
        if is_infinite:
            console.print(f"[bold cyan]━━━ Attempt {attempt_count}/∞ ━━━[/bold cyan]")
        else:
            console.print(f"[bold cyan]━━━ Attempt {attempt_count}/{max_attempts} ━━━[/bold cyan]")
        console.print()

        # Run the task
        run_task_fn(current_task)

        # Run verification
        report, has_failures = run_verification(task)

        if not has_failures:
            console.print()
            console.print("[bold green]✓ All verifications passed! Task complete.[/bold green]")
            console.print()
            return True

        # Failed - ask user what to do
        choice = prompt_retry_menu()

        if choice == 'retry':
            if not is_infinite and attempt_count >= max_attempts:
                console.print()
                console.print(f"[red]Max attempts ({max_attempts}) reached.[/red]")
                return False
            # Build retry prompt with failure context
            current_task = build_retry_prompt(task, report)
            console.print()
            console.print("[dim]Retrying with failure context...[/dim]")

        elif choice == 'approve':
            console.print()
            console.print("[yellow]Approved with failing verifications.[/yellow]")
            return True

        else:  # stop
            console.print()
            console.print("[red]Stopped by user.[/red]")
            return False

    console.print()
    console.print(f"[red]Max attempts ({max_attempts}) reached.[/red]")
    return False

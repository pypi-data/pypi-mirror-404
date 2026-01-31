"""Interactive menus for the agent CLI.

Contains all prompt_toolkit-based interactive menus with zen design language.
"""

from pathlib import Path

from rich.console import Console

from ...design import (
    Colors,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    STATUS_ERROR,
    DOT_BULLET,
    ARROW_PROMPT,
    header,
    footer,
    menu_hint,
)

console = Console()


def get_clarification_response(clarification: dict) -> str | None:
    """Get user response for clarification with interactive selection.

    Args:
        clarification: Dict with question, context, and options

    Returns:
        User's selected option or typed response, or None if cancelled
    """
    from prompt_toolkit import Application, PromptSession
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    options = clarification.get("options", [])

    if not options:
        # No options, just get free-form input
        session = PromptSession()
        try:
            return session.prompt("response > ").strip() or None
        except (KeyboardInterrupt, EOFError):
            return None

    selected_index = [0]
    result = [None]

    # Key bindings
    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_index[0] = (selected_index[0] - 1) % len(options)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_index[0] = (selected_index[0] + 1) % len(options)

    @kb.add("enter")
    def select(event):
        result[0] = options[selected_index[0]]
        event.app.exit()

    # Number key shortcuts (1-9)
    for i in range(min(9, len(options))):
        @kb.add(str(i + 1))
        def select_by_number(event, idx=i):
            result[0] = options[idx]
            event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    def cancel(event):
        result[0] = None
        event.app.exit()

    @kb.add("o")  # 'o' for Other - custom input
    def other_input(event):
        result[0] = "OTHER_INPUT"
        event.app.exit()

    def get_formatted_options():
        lines = []
        for i, opt in enumerate(options):
            if i == selected_index[0]:
                lines.append(("class:selected", f"  {STATUS_ACTIVE} "))
                lines.append(("class:selected", f"{i+1}. {opt}\n"))
            else:
                lines.append(("class:option", f"  {STATUS_INACTIVE} "))
                lines.append(("class:option", f"{i+1}. {opt}\n"))
        lines.append(("class:hint", f"\n{ARROW_PROMPT} ↑↓ move  Enter select  1-9 quick  o other"))
        return lines

    # Style (zen palette)
    style = Style.from_dict({
        "selected": f"{Colors.SUCCESS} bold",
        "option": Colors.MUTED,
        "hint": f"{Colors.DIM} italic",
    })

    # Calculate height based on options
    height = len(options) + 2  # options + hint line + padding

    # Layout
    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_options),
                height=height,
            ),
        ])
    )

    # Application
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
        return None

    # Handle "other" option - get custom input
    if result[0] == "OTHER_INPUT":
        session = PromptSession()
        console.print()
        try:
            return session.prompt("response > ").strip() or None
        except (KeyboardInterrupt, EOFError):
            return None

    # Check if selected option is an "other/explain" type that needs text input
    if result[0]:
        lower_result = result[0].lower()
        needs_input = any(phrase in lower_result for phrase in [
            "something else",
            "other",
            "i'll explain",
            "i will explain",
            "let me explain",
            "custom",
            "none of the above",
        ])
        if needs_input:
            session = PromptSession()
            console.print()
            console.print("[dim]Please explain:[/dim]")
            try:
                custom_input = session.prompt("response > ").strip()
                if custom_input:
                    return custom_input
            except (KeyboardInterrupt, EOFError):
                return None

    return result[0]


def get_choice_questions_response(choice_data: dict) -> list[dict] | None:
    """Get user responses for multiple choice questions with horizontal pagination.

    Displays questions as horizontal "pages" that user navigates with ← →.
    Each question allows selecting an option or entering custom text.

    Args:
        choice_data: Dict with 'choices' list and 'context' type

    Returns:
        List of dicts with question and answer, or None if cancelled
    """
    from prompt_toolkit import Application, PromptSession
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    choices = choice_data.get("choices", [])
    context = choice_data.get("context", "approach")

    if not choices:
        return None

    # State: current page, selected option per page, answers
    current_page = [0]
    # For each page: selected option index (-1 means custom input mode)
    selected_per_page = [0 for _ in choices]
    # Custom text input per page (if user chooses "Other")
    custom_inputs = ["" for _ in choices]
    # Final answers
    answers = [None for _ in choices]
    result = [None]  # Will be list of answers or None if cancelled

    kb = KeyBindings()

    @kb.add("left")
    @kb.add("h")
    def prev_page(event):
        if current_page[0] > 0:
            current_page[0] -= 1

    @kb.add("right")
    @kb.add("l")
    def next_page(event):
        if current_page[0] < len(choices) - 1:
            current_page[0] += 1

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        page = current_page[0]
        options = choices[page].get("options", [])
        max_idx = len(options)  # includes "Other" option
        selected_per_page[page] = (selected_per_page[page] - 1) % (max_idx + 1)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        page = current_page[0]
        options = choices[page].get("options", [])
        max_idx = len(options)  # includes "Other" option
        selected_per_page[page] = (selected_per_page[page] + 1) % (max_idx + 1)

    # Number key shortcuts for options
    for i in range(4):  # Max 4 options
        @kb.add(str(i + 1))
        def select_by_number(event, idx=i):
            page = current_page[0]
            options = choices[page].get("options", [])
            if idx < len(options):
                selected_per_page[page] = idx

    @kb.add("o")  # 'o' for Other
    def select_other(event):
        page = current_page[0]
        options = choices[page].get("options", [])
        selected_per_page[page] = len(options)  # Last index is "Other"

    @kb.add("enter")
    def confirm_and_continue(event):
        page = current_page[0]
        options = choices[page].get("options", [])
        selected = selected_per_page[page]

        if selected < len(options):
            # Regular option selected
            answers[page] = options[selected].get("label", options[selected])
        else:
            # "Other" selected - need custom input
            answers[page] = "OTHER_INPUT"

        # If on last page and all answered, submit
        if page == len(choices) - 1:
            # Check if any answer needs custom input
            if "OTHER_INPUT" in answers:
                result[0] = "NEED_CUSTOM"
            else:
                result[0] = answers
            event.app.exit()
        else:
            # Move to next page
            current_page[0] += 1

    @kb.add("c-c")
    @kb.add("escape")
    def cancel(event):
        result[0] = None
        event.app.exit()

    def get_formatted_content():
        lines = []
        page = current_page[0]
        choice = choices[page]
        question = choice.get("question", "")
        options = choice.get("options", [])
        selected = selected_per_page[page]

        # Header with context and pagination
        context_labels = {
            "approach": "Implementation Approach",
            "scope": "Scope Decision",
            "requirement": "Requirement Clarification",
        }
        context_label = context_labels.get(context, "Choice")

        # Title line with page indicator
        page_dots = "".join(
            f" {DOT_BULLET}" if i == page else f" {STATUS_INACTIVE}"
            for i in range(len(choices))
        )
        lines.append(("class:title", f"  {context_label} ({page + 1}/{len(choices)}){page_dots}\n\n"))

        # Question
        lines.append(("class:question", f"  {question}\n\n"))

        # Options
        for i, opt in enumerate(options):
            label = opt.get("label", opt) if isinstance(opt, dict) else opt
            desc = opt.get("description", "") if isinstance(opt, dict) else ""

            if i == selected:
                lines.append(("class:selected", f"    {STATUS_ACTIVE} "))
                lines.append(("class:selected", f"{i+1}. {label}\n"))
                if desc:
                    lines.append(("class:selected-desc", f"       {desc}\n"))
            else:
                lines.append(("class:option", f"    {STATUS_INACTIVE} "))
                lines.append(("class:option", f"{i+1}. {label}\n"))
                if desc:
                    lines.append(("class:desc", f"       {desc}\n"))

        # "Other" option
        other_idx = len(options)
        if selected == other_idx:
            lines.append(("class:selected", f"    {STATUS_ACTIVE} Other: [Enter custom response]\n"))
        else:
            lines.append(("class:option", f"    {STATUS_INACTIVE} Other: [Enter custom response]\n"))

        # Hint line
        lines.append(("class:hint", f"\n  {ARROW_PROMPT} ←→ pages  ↑↓ select  1-4 quick  o other  Enter confirm  Esc cancel"))

        return lines

    # Style (zen palette)
    style = Style.from_dict({
        "title": f"{Colors.PRIMARY} bold",
        "question": f"{Colors.WARNING}",
        "selected": f"{Colors.SUCCESS} bold",
        "selected-desc": Colors.SUCCESS,
        "option": Colors.MUTED,
        "desc": Colors.DIM,
        "hint": f"{Colors.DIM} italic",
    })

    # Calculate height
    max_options = max(len(c.get("options", [])) for c in choices)
    height = max_options * 2 + 8  # options with descriptions + header + hints

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_content),
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
        return None

    if result[0] is None:
        return None

    # Handle custom inputs if needed
    if result[0] == "NEED_CUSTOM":
        session = PromptSession()
        for i, ans in enumerate(answers):
            if ans == "OTHER_INPUT":
                question = choices[i].get("question", f"Choice {i+1}")
                console.print()
                console.print(f"[{Colors.DIM}]{question}[/{Colors.DIM}]")
                try:
                    custom = session.prompt("response > ").strip()
                    answers[i] = custom if custom else "No response"
                except (KeyboardInterrupt, EOFError):
                    return None

    # Build response list
    response_list = []
    for i, ans in enumerate(answers):
        response_list.append({
            "question": choices[i].get("question", f"Choice {i+1}"),
            "answer": ans,
        })

    return response_list


def show_plan_approval_menu() -> tuple[str, str]:
    """Show plan approval menu with simple approve/feedback options.

    Returns:
        Tuple of (choice, user_feedback) where user_feedback is only set for 'feedback'
    """
    from prompt_toolkit import Application, PromptSession
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    options = [
        ("approve", "Approve and start implementation"),
        ("feedback", "Provide feedback on the plan"),
    ]

    selected_index = [0]  # Use list to allow mutation in closure
    result = [None]

    # Key bindings
    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_index[0] = (selected_index[0] - 1) % len(options)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_index[0] = (selected_index[0] + 1) % len(options)

    @kb.add("enter")
    def select(event):
        result[0] = options[selected_index[0]][0]
        event.app.exit()

    @kb.add("1")
    @kb.add("y")
    def select_approve(event):
        result[0] = "approve"
        event.app.exit()

    @kb.add("2")
    @kb.add("n")
    def select_feedback(event):
        result[0] = "feedback"
        event.app.exit()

    @kb.add("c-c")
    @kb.add("q")
    @kb.add("escape")
    def cancel(event):
        result[0] = "feedback"
        event.app.exit()

    def get_formatted_options():
        lines = [("class:title", "Approve this plan?\n\n")]
        for i, (key, desc) in enumerate(options):
            if i == selected_index[0]:
                lines.append(("class:selected", f"  {STATUS_ACTIVE} {key}\n"))
                lines.append(("class:selected-desc", f"    {desc}\n"))
            else:
                lines.append(("class:option", f"  {STATUS_INACTIVE} {key}\n"))
                lines.append(("class:desc", f"    {desc}\n"))
        lines.append(("class:hint", f"\n{ARROW_PROMPT} y approve  n feedback  Esc cancel"))
        return lines

    # Style (zen palette)
    style = Style.from_dict({
        "title": f"{Colors.PRIMARY} bold",
        "selected": f"{Colors.SUCCESS} bold",
        "selected-desc": Colors.SUCCESS,
        "option": Colors.MUTED,
        "desc": Colors.DIM,
        "hint": f"{Colors.DIM} italic",
    })

    # Layout
    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_options),
                height=6,
            ),
        ])
    )

    # Application
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
        result[0] = "feedback"

    choice = result[0] or "feedback"

    # Get feedback if feedback was chosen
    user_feedback = ""
    if choice == "feedback":
        console.print()
        console.print("[dim]What changes would you like?[/dim]")
        try:
            session = PromptSession()
            user_feedback = session.prompt("feedback > ").strip()
        except (KeyboardInterrupt, EOFError):
            return "feedback", ""

    return choice, user_feedback


def show_agents_interactive_menu() -> tuple[str, str]:
    """Show interactive agents menu.

    Returns:
        Tuple of (action, agent_name) where action is one of:
        - 'view': View agent details
        - 'create': Create new agent
        - 'delete': Delete agent
        - 'edit': Edit agent file
        - 'cancel': User cancelled
    """
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style
    from emdash_core.agent.toolkits import list_agent_types, get_custom_agent

    # Get all agents
    all_agents = list_agent_types(Path.cwd())
    builtin = ["Explore", "Plan"]
    custom = [a for a in all_agents if a not in builtin]

    # Build menu items: each is (name, description, is_builtin, is_action)
    menu_items = []

    # Add built-in agents
    menu_items.append(("Explore", "Fast codebase exploration (read-only)", True, False))
    menu_items.append(("Plan", "Design implementation plans", True, False))

    # Add custom agents
    for name in custom:
        agent = get_custom_agent(name, Path.cwd())
        desc = agent.description if agent else "Custom agent"
        menu_items.append((name, desc, False, False))

    # Add action items at the bottom
    menu_items.append(("+ Create New Agent", "Create a new custom agent", False, True))

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
        name, desc, is_builtin, is_action = item
        if is_action:
            if "Create" in name:
                result[0] = ("create", "")
        else:
            result[0] = ("view", name)
        event.app.exit()

    @kb.add("d")
    def delete_agent(event):
        item = menu_items[selected_index[0]]
        name, desc, is_builtin, is_action = item
        if not is_builtin and not is_action:
            result[0] = ("delete", name)
            event.app.exit()

    @kb.add("e")
    def edit_agent(event):
        item = menu_items[selected_index[0]]
        name, desc, is_builtin, is_action = item
        if not is_builtin and not is_action:
            result[0] = ("edit", name)
            event.app.exit()

    @kb.add("n")
    def new_agent(event):
        result[0] = ("create", "")
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    @kb.add("q")
    def cancel(event):
        result[0] = ("cancel", "")
        event.app.exit()

    def get_formatted_menu():
        lines = [("class:title", "Agents\n\n")]

        for i, (name, desc, is_builtin, is_action) in enumerate(menu_items):
            is_selected = i == selected_index[0]
            indicator = STATUS_ACTIVE if is_selected else STATUS_INACTIVE

            if is_action:
                # Action item (like Create New)
                if is_selected:
                    lines.append(("class:action-selected", f"  {indicator} {name}\n"))
                else:
                    lines.append(("class:action", f"  {indicator} {name}\n"))
            elif is_builtin:
                # Built-in agent
                if is_selected:
                    lines.append(("class:builtin-selected", f"  {indicator} {name}\n"))
                    lines.append(("class:desc-selected", f"      {desc}\n"))
                else:
                    lines.append(("class:builtin", f"  {indicator} {name}\n"))
                    lines.append(("class:desc", f"      {desc}\n"))
            else:
                # Custom agent
                if is_selected:
                    lines.append(("class:custom-selected", f"  {indicator} {name}\n"))
                    lines.append(("class:desc-selected", f"      {desc}\n"))
                else:
                    lines.append(("class:custom", f"  {indicator} {name}\n"))
                    lines.append(("class:desc", f"      {desc}\n"))

        lines.append(("class:hint", f"\n{ARROW_PROMPT} ↑↓ navigate  Enter view  n new  e edit  d delete  q quit"))
        return lines

    # Style (zen palette)
    style = Style.from_dict({
        "title": f"{Colors.PRIMARY} bold",
        "builtin": Colors.MUTED,
        "builtin-selected": f"{Colors.SUCCESS} bold",
        "custom": Colors.PRIMARY,
        "custom-selected": f"{Colors.SUCCESS} bold",
        "action": Colors.WARNING,
        "action-selected": f"{Colors.WARNING} bold",
        "desc": Colors.DIM,
        "desc-selected": Colors.SUCCESS,
        "hint": f"{Colors.DIM} italic",
    })

    height = len(menu_items) + 4  # items + title + hint + padding

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

    return result[0]


def prompt_agent_name() -> str:
    """Prompt user for new agent name with zen styling."""
    from prompt_toolkit import PromptSession

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Create Agent', 35)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.DIM}]Enter a name for your agent[/{Colors.DIM}]")
    console.print(f"  [{Colors.DIM}](e.g., code-reviewer, bug-finder)[/{Colors.DIM}]")
    console.print()

    try:
        session = PromptSession()
        name = session.prompt(f"  {ARROW_PROMPT} ").strip()
        return name.lower().replace(" ", "-") if name else ""
    except (KeyboardInterrupt, EOFError):
        return ""


def confirm_delete(agent_name: str) -> bool:
    """Confirm agent deletion with zen styling."""
    from prompt_toolkit import PromptSession

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Delete Agent', 35)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.ERROR}]{STATUS_ERROR}[/{Colors.ERROR}] This will permanently delete:")
    console.print()
    console.print(f"      [{Colors.WARNING}]{agent_name}[/{Colors.WARNING}]")
    console.print()
    console.print(f"  [{Colors.DIM}]Type 'delete' to confirm[/{Colors.DIM}]")
    console.print()

    try:
        session = PromptSession()
        response = session.prompt(f"  {ARROW_PROMPT} ").strip().lower()
        return response == "delete"
    except (KeyboardInterrupt, EOFError):
        return False


def show_sessions_interactive_menu(sessions: list, active_session: str | None) -> tuple[str, str]:
    """Show interactive sessions menu.

    Args:
        sessions: List of SessionInfo objects
        active_session: Name of currently active session

    Returns:
        Tuple of (action, session_name) where action is one of:
        - 'load': Load the session
        - 'delete': Delete the session
        - 'cancel': User cancelled
    """
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    if not sessions:
        return ("cancel", "")

    # Build menu items: (name, summary, mode, message_count, updated_at, is_active)
    menu_items = []
    for s in sessions:
        is_active = active_session == s.name
        menu_items.append((s.name, s.summary or "", s.mode, s.message_count, s.updated_at, is_active))

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
        result[0] = ("load", item[0])
        event.app.exit()

    @kb.add("d")
    def delete_session(event):
        item = menu_items[selected_index[0]]
        result[0] = ("delete", item[0])
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    @kb.add("q")
    def cancel(event):
        result[0] = ("cancel", "")
        event.app.exit()

    def get_formatted_menu():
        lines = [("class:title", "Sessions\n\n")]

        for i, (name, summary, mode, msg_count, updated, is_active) in enumerate(menu_items):
            is_selected = i == selected_index[0]
            indicator = STATUS_ACTIVE if is_selected else STATUS_INACTIVE
            active_marker = f" {DOT_BULLET}" if is_active else ""

            if is_selected:
                lines.append(("class:name-selected", f"  {indicator} {name}{active_marker}"))
                lines.append(("class:mode-selected", f" [{mode}]"))
                lines.append(("class:info-selected", f" {msg_count} msgs\n"))
                if summary:
                    truncated = summary[:50] + "..." if len(summary) > 50 else summary
                    lines.append(("class:summary-selected", f"      {truncated}\n"))
            else:
                lines.append(("class:name", f"  {indicator} {name}{active_marker}"))
                lines.append(("class:mode", f" [{mode}]"))
                lines.append(("class:info", f" {msg_count} msgs\n"))
                if summary:
                    truncated = summary[:50] + "..." if len(summary) > 50 else summary
                    lines.append(("class:summary", f"      {truncated}\n"))

        lines.append(("class:hint", f"\n{ARROW_PROMPT} ↑↓ navigate  Enter load  d delete  q quit"))
        return lines

    # Style (zen palette)
    style = Style.from_dict({
        "title": f"{Colors.PRIMARY} bold",
        "name": Colors.PRIMARY,
        "name-selected": f"{Colors.SUCCESS} bold",
        "mode": Colors.MUTED,
        "mode-selected": Colors.SUCCESS,
        "info": Colors.DIM,
        "info-selected": Colors.SUCCESS,
        "summary": f"{Colors.DIM} italic",
        "summary-selected": f"{Colors.SUCCESS} italic",
        "hint": f"{Colors.DIM} italic",
    })

    height = len(menu_items) * 2 + 4  # items (with summaries) + title + hint + padding

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

    return result[0]


def confirm_session_delete(session_name: str) -> bool:
    """Confirm session deletion with zen styling."""
    from prompt_toolkit import PromptSession

    console.print()
    console.print(f"[{Colors.MUTED}]{header('Delete Session', 35)}[/{Colors.MUTED}]")
    console.print()
    console.print(f"  [{Colors.ERROR}]{STATUS_ERROR}[/{Colors.ERROR}] This will permanently delete:")
    console.print()
    console.print(f"      [{Colors.WARNING}]{session_name}[/{Colors.WARNING}]")
    console.print()
    console.print(f"  [{Colors.DIM}]Type 'delete' to confirm[/{Colors.DIM}]")
    console.print()

    try:
        session = PromptSession()
        response = session.prompt(f"  {ARROW_PROMPT} ").strip().lower()
        return response == "delete"
    except (KeyboardInterrupt, EOFError):
        return False


def show_plan_mode_approval_menu() -> tuple[str, str]:
    """Show plan mode entry approval menu.

    Returns:
        Tuple of (choice, feedback) where feedback is only set for 'reject'
    """
    from prompt_toolkit import Application, PromptSession
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout, HSplit, Window, FormattedTextControl
    from prompt_toolkit.styles import Style

    options = [
        ("approve", "Enter plan mode and explore"),
        ("reject", "Skip planning, proceed directly"),
    ]

    selected_index = [0]
    result = [None]

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def move_up(event):
        selected_index[0] = (selected_index[0] - 1) % len(options)

    @kb.add("down")
    @kb.add("j")
    def move_down(event):
        selected_index[0] = (selected_index[0] + 1) % len(options)

    @kb.add("enter")
    def select(event):
        result[0] = options[selected_index[0]][0]
        event.app.exit()

    @kb.add("1")
    @kb.add("y")
    def select_approve(event):
        result[0] = "approve"
        event.app.exit()

    @kb.add("2")
    @kb.add("n")
    def select_reject(event):
        result[0] = "reject"
        event.app.exit()

    @kb.add("c-c")
    @kb.add("q")
    @kb.add("escape")
    def cancel(event):
        result[0] = "reject"
        event.app.exit()

    def get_formatted_options():
        lines = [("class:title", "Enter plan mode?\n\n")]
        for i, (key, desc) in enumerate(options):
            if i == selected_index[0]:
                lines.append(("class:selected", f"  {STATUS_ACTIVE} {key}\n"))
                lines.append(("class:selected-desc", f"    {desc}\n"))
            else:
                lines.append(("class:option", f"  {STATUS_INACTIVE} {key}\n"))
                lines.append(("class:desc", f"    {desc}\n"))
        lines.append(("class:hint", f"\n{ARROW_PROMPT} y approve  n skip  Esc cancel"))
        return lines

    # Style (zen palette)
    style = Style.from_dict({
        "title": f"{Colors.WARNING} bold",
        "selected": f"{Colors.SUCCESS} bold",
        "selected-desc": Colors.SUCCESS,
        "option": Colors.MUTED,
        "desc": Colors.DIM,
        "hint": f"{Colors.DIM} italic",
    })

    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_formatted_options),
                height=6,
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
        result[0] = "reject"

    choice = result[0] or "reject"

    feedback = ""
    if choice == "reject":
        console.print()
        console.print("[dim]Reason for skipping plan mode (optional):[/dim]")
        try:
            session = PromptSession()
            feedback = session.prompt("feedback > ").strip()
        except (KeyboardInterrupt, EOFError):
            return "reject", ""

    return choice, feedback

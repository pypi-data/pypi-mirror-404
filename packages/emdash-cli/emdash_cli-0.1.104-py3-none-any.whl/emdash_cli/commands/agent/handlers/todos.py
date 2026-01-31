"""Handler for /todos and /todo-add commands."""

from rich.console import Console

from ....design import (
    Colors,
    header,
    footer,
    SEPARATOR_WIDTH,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    DOT_BULLET,
    print_error,
)

console = Console()


def handle_todos(args: str, client, session_id: str | None, pending_todos: list[str]) -> None:
    """Handle /todos command.

    Args:
        args: Command arguments (unused)
        client: EmdashClient instance
        session_id: Current session ID
        pending_todos: List of pending todos (before session starts)
    """
    if not session_id:
        if pending_todos:
            console.print()
            console.print(f"[{Colors.MUTED}]{header('Pending Todos', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
            console.print(f"  [{Colors.DIM}]will be added when session starts[/{Colors.DIM}]")
            console.print()
            for todo in pending_todos:
                console.print(f"  [{Colors.MUTED}]○[/{Colors.MUTED}] {todo}")
            console.print()
            console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
            console.print()
        else:
            console.print()
            console.print(f"  [{Colors.DIM}]No todos yet. Start a conversation to track tasks.[/{Colors.DIM}]")
            console.print()
    else:
        try:
            result = client.get_todos(session_id)
            todos = result.get("todos", [])
            summary = result.get("summary", {})

            if not todos:
                console.print()
                console.print(f"  [{Colors.DIM}]No todos in current session.[/{Colors.DIM}]")
                console.print()
            else:
                console.print()
                console.print(f"[{Colors.MUTED}]{header('Todo List', SEPARATOR_WIDTH)}[/{Colors.MUTED}]")
                console.print()

                for todo in todos:
                    title = todo["title"]
                    status = todo["status"]

                    if status == "completed":
                        console.print(f"  [{Colors.SUCCESS}]●[/{Colors.SUCCESS}] [{Colors.DIM} strike]{title}[/{Colors.DIM} strike]")
                    elif status == "in_progress":
                        console.print(f"  [{Colors.WARNING}]◐[/{Colors.WARNING}] [{Colors.TEXT} bold]{title}[/{Colors.TEXT} bold]")
                    else:
                        console.print(f"  [{Colors.MUTED}]○[/{Colors.MUTED}] {title}")

                    if todo.get("description"):
                        desc = todo["description"]
                        if len(desc) > 55:
                            desc = desc[:55] + "..."
                        console.print(f"      [{Colors.DIM}]{desc}[/{Colors.DIM}]")

                console.print()
                console.print(f"[{Colors.MUTED}]{footer(SEPARATOR_WIDTH)}[/{Colors.MUTED}]")

                # Summary bar
                total = summary.get('total', 0)
                completed = summary.get('completed', 0)
                in_progress = summary.get('in_progress', 0)
                pending = summary.get('pending', 0)

                console.print(f"  [{Colors.DIM}]○ {pending}[/{Colors.DIM}]  [{Colors.WARNING}]◐ {in_progress}[/{Colors.WARNING}]  [{Colors.SUCCESS}]● {completed}[/{Colors.SUCCESS}]  [{Colors.MUTED}]total {total}[/{Colors.MUTED}]")
                console.print()

        except Exception as e:
            print_error(e, "Error fetching todos")


def handle_todo_add(args: str, client, session_id: str | None, pending_todos: list[str]) -> None:
    """Handle /todo-add command.

    Args:
        args: Todo title to add
        client: EmdashClient instance
        session_id: Current session ID
        pending_todos: List of pending todos (before session starts)
    """
    if not args:
        console.print()
        console.print(f"  [{Colors.WARNING}]Usage:[/{Colors.WARNING}] /todo-add <title>")
        console.print(f"  [{Colors.DIM}]Example: /todo-add Fix the failing tests[/{Colors.DIM}]")
        console.print()
    elif not session_id:
        pending_todos.append(args)
        console.print()
        console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] [{Colors.MUTED}]noted:[/{Colors.MUTED}] {args}")
        console.print(f"  [{Colors.DIM}]will be added when session starts[/{Colors.DIM}]")
        console.print()
    else:
        try:
            result = client.add_todo(session_id, args)
            task = result.get("task", {})
            console.print()
            console.print(f"  [{Colors.SUCCESS}]{STATUS_ACTIVE}[/{Colors.SUCCESS}] [{Colors.MUTED}]added:[/{Colors.MUTED}] {task.get('title')}")
            console.print(f"  [{Colors.DIM}]total: {result.get('total_tasks', 0)}[/{Colors.DIM}]")
            console.print()
        except Exception as e:
            console.print(f"  [{Colors.ERROR}]error:[/{Colors.ERROR}] {e}")

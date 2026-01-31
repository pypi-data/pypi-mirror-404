"""Authentication CLI commands."""

import time
import webbrowser

import click
from rich.console import Console

from ..client import EmdashClient
from ..server_manager import get_server_manager
from ..design import print_error

console = Console()


@click.group()
def auth():
    """Manage GitHub authentication."""
    pass


@auth.command("login")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
def auth_login(no_browser: bool):
    """Authenticate with GitHub using device flow."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        # Start device flow
        result = client.auth_login()

        user_code = result.get("user_code")
        verification_uri = result.get("verification_uri")
        interval = result.get("interval", 5)
        expires_in = result.get("expires_in", 900)

        console.print()
        console.print("[bold]GitHub Device Authorization[/bold]")
        console.print()
        console.print(f"1. Go to: [cyan]{verification_uri}[/cyan]")
        console.print(f"2. Enter code: [bold yellow]{user_code}[/bold yellow]")
        console.print()

        if not no_browser:
            webbrowser.open(verification_uri)
            console.print("[dim]Browser opened automatically[/dim]")

        console.print("[dim]Waiting for authorization...[/dim]")

        # Poll for completion
        start_time = time.time()
        while time.time() - start_time < expires_in:
            time.sleep(interval)

            poll_result = client.auth_poll(user_code)
            status = poll_result.get("status")

            if status == "success":
                username = poll_result.get("username")
                console.print()
                console.print(f"[green]Successfully authenticated as {username}![/green]")
                return

            elif status == "expired":
                console.print("[red]Authorization expired. Please try again.[/red]")
                raise click.Abort()

            elif status == "error":
                error = poll_result.get("error", "Unknown error")
                console.print(f"[red]Error: {error}[/red]")
                raise click.Abort()

            # status == "pending" - continue polling

        console.print("[red]Authorization timed out. Please try again.[/red]")
        raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        print_error(e)
        raise click.Abort()


@auth.command("logout")
def auth_logout():
    """Remove stored GitHub authentication."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        result = client.auth_logout()
        if result.get("success"):
            console.print("[green]Successfully logged out.[/green]")
        else:
            console.print(f"[yellow]{result.get('message', 'Logout completed')}[/yellow]")
    except Exception as e:
        print_error(e)
        raise click.Abort()


@auth.command("status")
def auth_status():
    """Show current GitHub authentication status."""
    server = get_server_manager()
    client = EmdashClient(server.get_server_url())

    try:
        status = client.auth_status()

        if status.get("authenticated"):
            console.print("[green]Authenticated[/green]")
            console.print(f"  User: [cyan]{status.get('username')}[/cyan]")
            if status.get("scope"):
                console.print(f"  Scope: [dim]{status.get('scope')}[/dim]")
        else:
            console.print("[yellow]Not authenticated[/yellow]")
            console.print("[dim]Run 'emdash auth login' to authenticate[/dim]")
    except Exception as e:
        print_error(e)
        raise click.Abort()

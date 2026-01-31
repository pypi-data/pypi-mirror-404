"""Handler for /auth command."""

from rich.console import Console

from ....design import print_error

console = Console()


def handle_auth(args: str) -> None:
    """Handle /auth command.

    Supports both GitHub and Google authentication.

    Usage:
        /auth                  - Show all auth status
        /auth status           - Show all auth status
        /auth login            - GitHub login
        /auth logout           - GitHub logout
        /auth google           - Show Google auth status
        /auth google login     - Google OAuth login
        /auth google logout    - Google logout
        /auth google status    - Google auth status

    Args:
        args: Command arguments
    """
    # Parse subcommand
    subparts = args.split() if args else []
    subcommand = subparts[0].lower() if subparts else "status"

    # Handle Google-specific commands
    if subcommand == "google":
        google_subcommand = subparts[1].lower() if len(subparts) > 1 else "status"
        _handle_google_auth(google_subcommand)
        return

    # Handle GitHub commands (default)
    _handle_github_auth(subcommand)


def _handle_github_auth(subcommand: str) -> None:
    """Handle GitHub authentication commands."""
    from emdash_core.auth.github import GitHubAuth, get_auth_status

    if subcommand == "status" or subcommand == "":
        # Show all auth status
        _show_all_auth_status()

    elif subcommand == "login":
        # Start GitHub OAuth device flow
        console.print()
        console.print("[bold cyan]GitHub Login[/bold cyan]")
        console.print("[dim]Starting device authorization flow...[/dim]\n")

        auth = GitHubAuth()
        try:
            config = auth.login(open_browser=True)
            if config:
                console.print()
                console.print("[green]Authentication successful![/green]")
                console.print("[dim]MCP servers can now use ${GITHUB_TOKEN}[/dim]")
            else:
                console.print("[red]Authentication failed or was cancelled.[/red]")
        except Exception as e:
            print_error(e, "Login failed")

        console.print()

    elif subcommand == "logout":
        # Remove stored authentication
        auth = GitHubAuth()
        if auth.logout():
            console.print("[green]Logged out from GitHub successfully[/green]")
        else:
            console.print("[dim]No stored GitHub authentication to remove[/dim]")

    else:
        console.print(f"[yellow]Unknown subcommand: {subcommand}[/yellow]")
        console.print("[dim]Usage: /auth [status|login|logout|google][/dim]")


def _handle_google_auth(subcommand: str) -> None:
    """Handle Google authentication commands."""
    from emdash_core.auth.google import GoogleAuth, get_google_auth_status

    if subcommand == "status" or subcommand == "":
        # Show Google auth status
        status = get_google_auth_status()
        console.print()
        console.print("[bold blue]Google Authentication[/bold blue]\n")

        if status["authenticated"]:
            console.print(f"  Status: [green]Authenticated[/green]")
            console.print(f"  Source: {status['source']}")
            if status["email"]:
                console.print(f"  Email: {status['email']}")
            if status["scopes"]:
                # Show abbreviated scopes
                scope_names = []
                for scope in status["scopes"]:
                    if "gmail" in scope:
                        scope_names.append("Gmail")
                    elif "calendar" in scope:
                        scope_names.append("Calendar")
                    elif "drive" in scope:
                        scope_names.append("Drive")
                    elif "documents" in scope:
                        scope_names.append("Docs")
                    elif "spreadsheets" in scope:
                        scope_names.append("Sheets")
                unique_scopes = list(dict.fromkeys(scope_names))  # Preserve order, remove dupes
                if unique_scopes:
                    console.print(f"  Services: {', '.join(unique_scopes)}")
        else:
            console.print(f"  Status: [yellow]Not authenticated[/yellow]")
            console.print("\n[dim]Run /auth google login to authenticate with Google[/dim]")

        console.print()

    elif subcommand == "login":
        # Start Google OAuth flow
        console.print()
        console.print("[bold blue]Google Login[/bold blue]")
        console.print("[dim]Opening browser for Google authentication...[/dim]\n")

        auth = GoogleAuth()
        try:
            result = auth.login(open_browser=True)
            if result.get("success"):
                console.print()
                console.print("[green]Authentication successful![/green]")
                if result.get("email"):
                    console.print(f"[dim]Logged in as: {result['email']}[/dim]")
                console.print("[dim]Google Workspace tools now available[/dim]")
            else:
                error = result.get("error", "Unknown error")
                console.print(f"[red]Authentication failed: {error}[/red]")
        except Exception as e:
            print_error(e, "Google login failed")

        console.print()

    elif subcommand == "logout":
        # Remove Google authentication
        auth = GoogleAuth()
        result = auth.logout()
        if result.get("success"):
            console.print(f"[green]{result.get('message', 'Logged out from Google')}[/green]")
        else:
            console.print("[dim]No stored Google authentication to remove[/dim]")

    else:
        console.print(f"[yellow]Unknown Google subcommand: {subcommand}[/yellow]")
        console.print("[dim]Usage: /auth google [status|login|logout][/dim]")


def _show_all_auth_status() -> None:
    """Show authentication status for all providers."""
    from emdash_core.auth.github import get_auth_status as get_github_status
    from emdash_core.auth.google import get_google_auth_status

    console.print()

    # GitHub status
    github_status = get_github_status()
    console.print("[bold cyan]GitHub Authentication[/bold cyan]\n")

    if github_status["authenticated"]:
        console.print(f"  Status: [green]Authenticated[/green]")
        console.print(f"  Source: {github_status['source']}")
        if github_status["username"]:
            console.print(f"  Username: @{github_status['username']}")
    else:
        console.print(f"  Status: [yellow]Not authenticated[/yellow]")
        console.print("  [dim]Run /auth login to authenticate[/dim]")

    console.print()

    # Google status
    google_status = get_google_auth_status()
    console.print("[bold blue]Google Authentication[/bold blue]\n")

    if google_status["authenticated"]:
        console.print(f"  Status: [green]Authenticated[/green]")
        if google_status["email"]:
            console.print(f"  Email: {google_status['email']}")
        # Show abbreviated service names
        if google_status["scopes"]:
            services = set()
            for scope in google_status["scopes"]:
                if "gmail" in scope:
                    services.add("Gmail")
                elif "calendar" in scope:
                    services.add("Calendar")
                elif "drive" in scope:
                    services.add("Drive")
                elif "documents" in scope:
                    services.add("Docs")
                elif "spreadsheets" in scope:
                    services.add("Sheets")
            if services:
                console.print(f"  Services: {', '.join(sorted(services))}")
    else:
        console.print(f"  Status: [yellow]Not authenticated[/yellow]")
        console.print("  [dim]Run /auth google login to authenticate[/dim]")

    console.print()

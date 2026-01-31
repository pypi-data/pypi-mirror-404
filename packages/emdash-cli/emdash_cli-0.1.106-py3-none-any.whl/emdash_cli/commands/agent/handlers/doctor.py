"""Handler for /doctor command - environment diagnostics."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Minimum required Python version
MIN_PYTHON_VERSION = (3, 10)

# Required packages
REQUIRED_PACKAGES = [
    "emdash-cli",
    "emdash-core",
    "click",
    "rich",
    "httpx",
    "prompt_toolkit",
]

# Servers directory for per-repo servers
SERVERS_DIR = Path.home() / ".emdash" / "servers"


def check_python_version() -> tuple[bool, str, str]:
    """Check Python version.

    Returns:
        Tuple of (passed, current_version, message)
    """
    current = sys.version_info[:2]
    version_str = f"{current[0]}.{current[1]}"

    if current >= MIN_PYTHON_VERSION:
        return True, version_str, f"Python {version_str} (>= {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} required)"
    else:
        return False, version_str, f"Python {version_str} is below minimum {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}"


def check_package_installed(package: str) -> tuple[bool, str]:
    """Check if a package is installed.

    Returns:
        Tuple of (installed, version_or_error)
    """
    try:
        from importlib.metadata import version
        ver = version(package)
        return True, ver
    except Exception:
        return False, "not installed"


def check_git() -> tuple[bool, str]:
    """Check if git is available.

    Returns:
        Tuple of (available, version_or_error)
    """
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        version = result.stdout.strip().replace("git version ", "")
        return True, version
    except Exception:
        return False, "not found"


def check_git_repo() -> tuple[bool, str]:
    """Check if current directory is a git repo.

    Returns:
        Tuple of (is_repo, message)
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_path = result.stdout.strip()
        return True, repo_path
    except Exception:
        return False, "not a git repository"


def check_server_status() -> tuple[bool, str, list[dict]]:
    """Check emdash server status.

    Returns:
        Tuple of (any_running, message, server_list)
    """
    import httpx

    servers = []

    # Check per-repo servers
    if SERVERS_DIR.exists():
        for port_file in SERVERS_DIR.glob("*.port"):
            try:
                port = int(port_file.read_text().strip())
                hash_prefix = port_file.stem

                # Get repo path
                repo_file = SERVERS_DIR / f"{hash_prefix}.repo"
                repo_path = repo_file.read_text().strip() if repo_file.exists() else "unknown"

                # Check health
                try:
                    response = httpx.get(f"http://localhost:{port}/api/health", timeout=2.0)
                    healthy = response.status_code == 200
                except Exception:
                    healthy = False

                servers.append({
                    "port": port,
                    "repo": repo_path,
                    "healthy": healthy,
                })
            except Exception:
                pass

    if servers:
        healthy_count = sum(1 for s in servers if s["healthy"])
        return True, f"{healthy_count}/{len(servers)} healthy", servers
    else:
        return False, "no servers running", []


def check_api_keys() -> list[tuple[str, bool, str]]:
    """Check for common API keys.

    Returns:
        List of (key_name, is_set, hint)
    """
    keys = [
        ("ANTHROPIC_API_KEY", "Required for Claude models"),
        ("OPENAI_API_KEY", "Required for OpenAI models"),
        ("FIREWORKS_API_KEY", "Required for Fireworks models"),
        ("GITHUB_TOKEN", "Required for GitHub integration"),
    ]

    results = []
    for key, hint in keys:
        is_set = bool(os.environ.get(key))
        results.append((key, is_set, hint))

    return results


def check_disk_space() -> tuple[bool, str]:
    """Check available disk space.

    Returns:
        Tuple of (sufficient, message)
    """
    try:
        usage = shutil.disk_usage(Path.home())
        free_gb = usage.free / (1024 ** 3)
        if free_gb < 1:
            return False, f"{free_gb:.1f} GB free (low!)"
        else:
            return True, f"{free_gb:.1f} GB free"
    except Exception:
        return True, "unknown"


def check_path_config() -> list[tuple[str, bool, str]]:
    """Check if common bin directories are in PATH.

    Returns:
        List of (path, in_path, description)
    """
    path_env = os.environ.get("PATH", "")
    paths_to_check = [
        (Path.home() / ".local" / "bin", "pipx installs"),
        (Path.home() / ".pyenv" / "shims", "pyenv"),
        (Path("/opt/homebrew/bin"), "Homebrew (Apple Silicon)"),
        (Path("/usr/local/bin"), "Homebrew (Intel) / system"),
    ]

    results = []
    for path, desc in paths_to_check:
        in_path = str(path) in path_env
        results.append((str(path), in_path, desc))

    return results


def handle_doctor(args: str) -> None:
    """Handle /doctor command - run environment diagnostics."""
    console.print()
    console.print("[bold cyan]Emdash Doctor[/bold cyan] - Environment Diagnostics")
    console.print()

    issues = []

    # Python Version
    console.print("[bold]Python Environment[/bold]")
    py_ok, py_ver, py_msg = check_python_version()
    if py_ok:
        console.print(f"  [green]✓[/green] {py_msg}")
    else:
        console.print(f"  [red]✗[/red] {py_msg}")
        issues.append(("Python version", f"Upgrade to Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+"))

    console.print(f"  [dim]  Executable: {sys.executable}[/dim]")
    console.print()

    # Packages
    console.print("[bold]Required Packages[/bold]")
    for pkg in REQUIRED_PACKAGES:
        installed, ver = check_package_installed(pkg)
        if installed:
            console.print(f"  [green]✓[/green] {pkg} ({ver})")
        else:
            console.print(f"  [red]✗[/red] {pkg} - {ver}")
            issues.append((f"Package {pkg}", f"pip install {pkg}"))
    console.print()

    # Git
    console.print("[bold]Git[/bold]")
    git_ok, git_ver = check_git()
    if git_ok:
        console.print(f"  [green]✓[/green] git ({git_ver})")
    else:
        console.print(f"  [red]✗[/red] git not found")
        issues.append(("Git", "Install git"))

    repo_ok, repo_path = check_git_repo()
    if repo_ok:
        console.print(f"  [green]✓[/green] In git repo: {repo_path}")
    else:
        console.print(f"  [yellow]![/yellow] Not in a git repository")
    console.print()

    # Server Status
    console.print("[bold]Emdash Server[/bold]")
    srv_ok, srv_msg, servers = check_server_status()
    if srv_ok:
        console.print(f"  [green]✓[/green] Servers: {srv_msg}")
        for srv in servers:
            status = "[green]healthy[/green]" if srv["healthy"] else "[red]unhealthy[/red]"
            repo_short = srv["repo"].split("/")[-1] if "/" in srv["repo"] else srv["repo"]
            console.print(f"      Port {srv['port']}: {status} ({repo_short})")
    else:
        console.print(f"  [dim]-[/dim] {srv_msg}")
    console.print()

    # API Keys
    console.print("[bold]API Keys[/bold]")
    api_keys = check_api_keys()
    for key, is_set, hint in api_keys:
        if is_set:
            console.print(f"  [green]✓[/green] {key} [dim]({hint})[/dim]")
        else:
            console.print(f"  [dim]-[/dim] {key} not set [dim]({hint})[/dim]")
    console.print()

    # System
    console.print("[bold]System[/bold]")
    disk_ok, disk_msg = check_disk_space()
    if disk_ok:
        console.print(f"  [green]✓[/green] Disk space: {disk_msg}")
    else:
        console.print(f"  [yellow]![/yellow] Disk space: {disk_msg}")
        issues.append(("Disk space", "Free up disk space"))

    # PATH check
    path_results = check_path_config()
    local_bin = Path.home() / ".local" / "bin"
    local_bin_in_path = str(local_bin) in os.environ.get("PATH", "")
    if local_bin_in_path:
        console.print(f"  [green]✓[/green] ~/.local/bin in PATH (pipx)")
    else:
        console.print(f"  [red]✗[/red] ~/.local/bin not in PATH")
        issues.append(("PATH config", "Run: pipx ensurepath && source ~/.zshrc"))
    console.print()

    # Summary
    if issues:
        console.print("[bold red]Issues Found:[/bold red]")
        console.print()
        for issue, fix in issues:
            console.print(f"  [red]•[/red] {issue}")
            console.print(f"    [dim]Fix: {fix}[/dim]")
        console.print()

        # Python upgrade instructions if needed
        if not py_ok:
            console.print("[bold]To upgrade Python:[/bold]")
            console.print("  [cyan]macOS:[/cyan]     brew install python@3.12")
            console.print("  [cyan]Ubuntu:[/cyan]    sudo apt install python3.12")
            console.print("  [cyan]Windows:[/cyan]   winget install Python.Python.3.12")
            console.print("  [cyan]pyenv:[/cyan]     pyenv install 3.12 && pyenv global 3.12")
            console.print()

        # PATH fix instructions if needed
        if not local_bin_in_path:
            console.print("[bold]To fix PATH (for pipx/em command):[/bold]")
            console.print("  [cyan]Option 1:[/cyan]  pipx ensurepath")
            console.print("  [cyan]Option 2:[/cyan]  echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.zshrc")
            console.print("  [dim]Then restart your terminal or run: source ~/.zshrc[/dim]")
            console.print()
    else:
        console.print("[bold green]All checks passed![/bold green]")
        console.print()

"""Server management commands."""

import os
import signal
import subprocess
from pathlib import Path

import click
from rich.console import Console

console = Console()

# Per-repo servers directory
SERVERS_DIR = Path.home() / ".emdash" / "servers"


@click.group()
def server():
    """Manage the emdash-core server."""
    pass


@server.command("killall")
def server_killall():
    """Kill all running emdash servers.

    Example:
        emdash server killall
    """
    killed = 0

    # Kill servers by PID files in servers directory
    if SERVERS_DIR.exists():
        for pid_file in SERVERS_DIR.glob("*.pid"):
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, signal.SIGTERM)
                console.print(f"[green]Killed server process {pid}[/green]")
                killed += 1
            except (ValueError, ProcessLookupError, PermissionError):
                pass
            finally:
                # Clean up all files for this server
                hash_prefix = pid_file.stem
                for ext in [".port", ".pid", ".repo"]:
                    server_file = SERVERS_DIR / f"{hash_prefix}{ext}"
                    if server_file.exists():
                        server_file.unlink(missing_ok=True)

    # Also check legacy location
    legacy_pid_file = Path.home() / ".emdash" / "server.pid"
    if legacy_pid_file.exists():
        try:
            pid = int(legacy_pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            console.print(f"[green]Killed legacy server process {pid}[/green]")
            killed += 1
        except (ValueError, ProcessLookupError, PermissionError):
            pass
        finally:
            legacy_pid_file.unlink(missing_ok=True)

    # Clean up legacy port file
    legacy_port_file = Path.home() / ".emdash" / "server.port"
    if legacy_port_file.exists():
        legacy_port_file.unlink(missing_ok=True)

    # Kill any remaining emdash_core.server processes
    try:
        result = subprocess.run(
            ["pgrep", "-f", "emdash_core.server"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            for pid_str in pids:
                if pid_str:
                    try:
                        pid = int(pid_str)
                        os.kill(pid, signal.SIGTERM)
                        console.print(f"[green]Killed server process {pid}[/green]")
                        killed += 1
                    except (ValueError, ProcessLookupError, PermissionError):
                        pass
    except FileNotFoundError:
        # pgrep not available, try pkill
        subprocess.run(
            ["pkill", "-f", "emdash_core.server"],
            capture_output=True,
        )

    if killed > 0:
        console.print(f"\n[bold green]Killed {killed} server(s)[/bold green]")
    else:
        console.print("[yellow]No running servers found[/yellow]")


@server.command("status")
def server_status():
    """Show status of all running servers.

    Example:
        emdash server status
    """
    import httpx

    servers_found = []

    # Check per-repo servers directory
    if SERVERS_DIR.exists():
        for port_file in SERVERS_DIR.glob("*.port"):
            try:
                port = int(port_file.read_text().strip())
                hash_prefix = port_file.stem

                # Get repo path if available
                repo_file = SERVERS_DIR / f"{hash_prefix}.repo"
                repo_path = repo_file.read_text().strip() if repo_file.exists() else "unknown"

                # Get PID if available
                pid_file = SERVERS_DIR / f"{hash_prefix}.pid"
                pid = pid_file.read_text().strip() if pid_file.exists() else "unknown"

                # Check health
                try:
                    response = httpx.get(f"http://localhost:{port}/api/health", timeout=2.0)
                    healthy = response.status_code == 200
                except (httpx.RequestError, httpx.TimeoutException):
                    healthy = False

                servers_found.append({
                    "port": port,
                    "pid": pid,
                    "repo": repo_path,
                    "healthy": healthy,
                })
            except (ValueError, IOError):
                pass

    # Check legacy location
    legacy_port_file = Path.home() / ".emdash" / "server.port"
    if legacy_port_file.exists():
        try:
            port = int(legacy_port_file.read_text().strip())
            legacy_pid_file = Path.home() / ".emdash" / "server.pid"
            pid = legacy_pid_file.read_text().strip() if legacy_pid_file.exists() else "unknown"

            try:
                response = httpx.get(f"http://localhost:{port}/api/health", timeout=2.0)
                healthy = response.status_code == 200
            except (httpx.RequestError, httpx.TimeoutException):
                healthy = False

            servers_found.append({
                "port": port,
                "pid": pid,
                "repo": "(legacy)",
                "healthy": healthy,
            })
        except (ValueError, IOError):
            pass

    if not servers_found:
        console.print("[yellow]No servers running[/yellow]")
        return

    console.print(f"[bold]Found {len(servers_found)} server(s):[/bold]\n")
    for srv in servers_found:
        status = "[green]healthy[/green]" if srv["healthy"] else "[red]unhealthy[/red]"
        console.print(f"  {status}")
        console.print(f"    Port: {srv['port']}")
        console.print(f"    PID:  {srv['pid']}")
        console.print(f"    Repo: {srv['repo']}")
        console.print(f"    URL:  http://localhost:{srv['port']}")
        console.print()

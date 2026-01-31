"""Server lifecycle management for emdash-core."""

import atexit
import hashlib
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import httpx


class ServerManager:
    """Manages FastAPI server lifecycle for CLI.

    The ServerManager handles:
    - Per-repo server instances (each repo gets its own server)
    - Discovering running servers via port file
    - Starting new servers when needed
    - Health checking servers
    - Graceful shutdown on CLI exit
    - Cleanup of stale servers
    """

    SERVERS_DIR = Path.home() / ".emdash" / "servers"
    STARTUP_TIMEOUT = 30.0  # seconds
    HEALTH_TIMEOUT = 2.0  # seconds

    def __init__(self, repo_root: Optional[Path] = None):
        """Initialize the server manager.

        Args:
            repo_root: Repository root path (for server to use)
        """
        self.repo_root = repo_root or self._detect_repo_root()
        self.process: Optional[subprocess.Popen] = None
        self.port: Optional[int] = None
        self._started_by_us = False

        # Create servers directory
        self.SERVERS_DIR.mkdir(parents=True, exist_ok=True)

        # Cleanup stale servers on init
        self._cleanup_stale_servers()

    @property
    def _repo_hash(self) -> str:
        """Get a short hash of the repo root path for unique file naming."""
        path_str = str(self.repo_root.resolve())
        return hashlib.sha256(path_str.encode()).hexdigest()[:12]

    @property
    def _port_file(self) -> Path:
        """Get the port file path for this repo."""
        return self.SERVERS_DIR / f"{self._repo_hash}.port"

    @property
    def _pid_file(self) -> Path:
        """Get the PID file path for this repo."""
        return self.SERVERS_DIR / f"{self._repo_hash}.pid"

    @property
    def _repo_file(self) -> Path:
        """Get the repo path file for this repo (for debugging)."""
        return self.SERVERS_DIR / f"{self._repo_hash}.repo"

    def get_server_url(self) -> str:
        """Get URL of running server for this repo, starting one if needed.

        Returns:
            Base URL of the running server (e.g., "http://localhost:8765")

        Raises:
            RuntimeError: If server fails to start
        """
        # Check if server already running for THIS repo
        if self._port_file.exists():
            try:
                port = int(self._port_file.read_text().strip())
                if self._check_health(port):
                    self.port = port
                    return f"http://localhost:{port}"
            except (ValueError, IOError):
                pass
            # Server not healthy, clean up stale files
            self._cleanup_files()

        # Start new server for this repo
        self.port = self._find_free_port()
        self._spawn_server()
        return f"http://localhost:{self.port}"

    def ensure_server(self) -> str:
        """Ensure server is running and return URL.

        Alias for get_server_url() for clearer intent.
        """
        return self.get_server_url()

    def shutdown(self) -> None:
        """Shutdown the server if we started it."""
        if self._started_by_us and self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            finally:
                self._cleanup_files()
                self.process = None

    def _detect_repo_root(self) -> Path:
        """Detect repository root from current directory."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            return Path.cwd()

    def _find_free_port(self) -> int:
        """Find an available port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.listen(1)
            return s.getsockname()[1]

    def _spawn_server(self) -> None:
        """Spawn FastAPI server as subprocess."""
        # Find emdash-core module
        core_module = self._find_core_module()

        cmd = [
            sys.executable,
            "-m", "emdash_core.server",
            "--port", str(self.port),
            "--host", "127.0.0.1",
        ]

        if self.repo_root:
            cmd.extend(["--repo-root", str(self.repo_root)])

        # Set environment to include core package
        env = os.environ.copy()
        if core_module:
            python_path = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = f"{core_module}:{python_path}" if python_path else str(core_module)

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        self._started_by_us = True

        # Write port, PID, and repo files
        self._port_file.write_text(str(self.port))
        self._pid_file.write_text(str(self.process.pid))
        self._repo_file.write_text(str(self.repo_root))

        # Register cleanup for normal exit
        atexit.register(self.shutdown)

        # Register signal handlers for Ctrl+C and termination
        self._register_signal_handlers()

        # Wait for server ready
        self._wait_for_ready()

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        def signal_handler(_signum, _frame):
            self.shutdown()
            sys.exit(0)

        # Handle SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _find_core_module(self) -> Optional[Path]:
        """Find the emdash-core package directory."""
        # Check relative to this file (for development)
        cli_dir = Path(__file__).parent.parent
        core_dir = cli_dir.parent / "core"
        if (core_dir / "emdash_core").exists():
            return core_dir
        return None

    def _check_health(self, port: int) -> bool:
        """Check if server is healthy.

        Args:
            port: Port to check

        Returns:
            True if server responds to health check
        """
        try:
            response = httpx.get(
                f"http://localhost:{port}/api/health",
                timeout=self.HEALTH_TIMEOUT,
            )
            return response.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    def _wait_for_ready(self) -> None:
        """Wait for server to become ready.

        Raises:
            RuntimeError: If server fails to start within timeout
        """
        assert self.port is not None, "Port must be set before waiting for ready"
        start = time.time()
        while time.time() - start < self.STARTUP_TIMEOUT:
            if self._check_health(self.port):
                return

            # Check if process died
            if self.process and self.process.poll() is not None:
                stderr = self.process.stderr.read().decode() if self.process.stderr else ""
                raise RuntimeError(f"Server process died: {stderr}")

            time.sleep(0.1)

        raise RuntimeError(
            f"Server failed to start within {self.STARTUP_TIMEOUT}s"
        )

    def _cleanup_files(self) -> None:
        """Clean up port, PID, and repo files for this repo."""
        for file in [self._port_file, self._pid_file, self._repo_file]:
            try:
                if file.exists():
                    file.unlink()
            except IOError:
                pass

    def _cleanup_stale_servers(self) -> None:
        """Clean up stale server files where process no longer exists."""
        if not self.SERVERS_DIR.exists():
            return

        for pid_file in self.SERVERS_DIR.glob("*.pid"):
            try:
                pid = int(pid_file.read_text().strip())
                # Check if process exists
                try:
                    os.kill(pid, 0)  # Signal 0 checks if process exists
                except OSError:
                    # Process doesn't exist, clean up files
                    hash_prefix = pid_file.stem
                    for ext in [".port", ".pid", ".repo"]:
                        stale_file = self.SERVERS_DIR / f"{hash_prefix}{ext}"
                        if stale_file.exists():
                            stale_file.unlink()
            except (ValueError, IOError):
                # Invalid PID file, remove it
                try:
                    pid_file.unlink()
                except IOError:
                    pass


# Global singleton for CLI commands
_server_manager: Optional[ServerManager] = None


def get_server_manager(repo_root: Optional[Path] = None) -> ServerManager:
    """Get or create the global server manager.

    Args:
        repo_root: Repository root (only used on first call)

    Returns:
        The server manager instance
    """
    global _server_manager
    if _server_manager is None:
        _server_manager = ServerManager(repo_root)
    return _server_manager

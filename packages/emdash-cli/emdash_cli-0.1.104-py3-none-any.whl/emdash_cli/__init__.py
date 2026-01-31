"""EmDash CLI - Command-line interface for code intelligence."""

from importlib.metadata import version, PackageNotFoundError
import os
from pathlib import Path

# Load .env files early so env vars are available for server subprocess
# Load order: global (~/.emdash/.env) first, then project .env (overrides global)
try:
    from dotenv import load_dotenv

    # 1. Load global .env first (user defaults - API keys, preferences)
    # Support XDG_CONFIG_HOME on Linux, fallback to ~/.emdash
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        global_env_paths = [
            Path(xdg_config) / "emdash" / ".env",
            Path.home() / ".emdash" / ".env",
        ]
    else:
        global_env_paths = [Path.home() / ".emdash" / ".env"]

    for global_env in global_env_paths:
        if global_env.exists():
            load_dotenv(global_env, override=False)  # Don't override existing env vars
            break

    # 2. Load project .env (overrides global settings)
    # Try to find .env in current dir or parent dirs
    current = Path.cwd()
    for _ in range(5):
        env_path = current / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)  # Override global with project-specific
            break
        current = current.parent
except ImportError:
    pass  # dotenv not installed

try:
    __version__ = version("emdash-cli")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

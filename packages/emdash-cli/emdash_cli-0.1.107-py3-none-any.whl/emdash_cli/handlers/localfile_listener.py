"""Local file listener — watches for file changes and syncs to core.

Polls the local JSON files for changes made by other processes
(e.g. another CLI instance on the same machine). When a change
is detected, syncs the updated data to the local core server.

This is the file-based equivalent of FirebaseListener:

    Other CLI process → writes JSON files → this listener → local core sync

Watches directories: projects/, tasks/, sessions/, teams/, registries/

Change detection:
    Uses a `.last_change` marker file written by LocalFileWebhookHandler.
    The listener polls this marker and reloads when the timestamp changes.

Echo loop prevention:
    Each write includes an `_origin` field in the JSON data.
    This listener skips changes where `_origin` matches the local user.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

import httpx

log = logging.getLogger(__name__)

# Map directory names to sync endpoint paths
_SYNC_ENDPOINTS = {
    "projects": "/api/multiuser/sync/projects",
    "tasks": "/api/multiuser/sync/tasks",
    "sessions": "/api/multiuser/sync/sessions",
    "teams": "/api/multiuser/sync/teams",
    "registries": "/api/multiuser/sync/registries",
}


class LocalFileListener:
    """Watches local files for changes and syncs to core.

    Usage:
        listener = LocalFileListener(
            storage_root=Path("~/.emdash/projects"),
            core_url="http://localhost:8000",
            my_user_id="user_123",
        )
        await listener.start(team_id="team_abc")
        # ... runs until stopped
        await listener.stop()
    """

    def __init__(
        self,
        storage_root: Path,
        core_url: str,
        my_user_id: str,
        poll_interval: float = 1.0,
    ):
        self._root = storage_root
        self._core_url = core_url.rstrip("/")
        self._my_user_id = my_user_id
        self._poll_interval = poll_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._client: Optional[httpx.AsyncClient] = None
        self._last_marker: Optional[str] = None
        # Track file mtimes to detect which files changed
        self._known_mtimes: dict[str, float] = {}

        # Entity directories
        self._entity_dirs = {
            "projects": self._root / "projects",
            "tasks": self._root / "tasks",
            "sessions": self._root / "sessions",
            "teams": self._root / "teams",
            "registries": self._root / "registries",
        }

    async def start(self, team_id: str) -> None:
        """Start watching files for changes."""
        self._running = True
        self._client = httpx.AsyncClient(timeout=15.0)
        self._team_id = team_id

        # Snapshot current state so we don't sync everything on start
        self._snapshot_mtimes()

        self._task = asyncio.create_task(
            self._poll_loop(),
            name=f"file-listener-{team_id}",
        )
        log.info(f"Local file listener started for {self._root}")

    async def stop(self) -> None:
        """Stop watching."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._client:
            await self._client.aclose()
            self._client = None
        log.info("Local file listener stopped")

    def _snapshot_mtimes(self) -> None:
        """Record current mtimes for all entity files."""
        self._known_mtimes.clear()
        for dir_path in self._entity_dirs.values():
            if dir_path.exists():
                for path in dir_path.glob("*.json"):
                    self._known_mtimes[str(path)] = path.stat().st_mtime

    async def _poll_loop(self) -> None:
        """Poll for file changes."""
        while self._running:
            try:
                await asyncio.sleep(self._poll_interval)
                if not self._running:
                    break

                # Check marker file for quick change detection
                marker = self._root / ".last_change"
                if marker.exists():
                    current = marker.read_text().strip()
                    if current == self._last_marker:
                        continue  # No changes
                    self._last_marker = current
                else:
                    # No marker — check mtimes directly (slower)
                    pass

                await self._check_for_changes()

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._running:
                    log.warning(f"File listener error: {e}")

    async def _check_for_changes(self) -> None:
        """Check for new/modified/deleted files and sync to core."""
        all_current_files = set()

        for entity_type, dir_path in self._entity_dirs.items():
            if not dir_path.exists():
                continue

            changed_items = []
            for path in dir_path.glob("*.json"):
                path_str = str(path)
                all_current_files.add(path_str)
                mtime = path.stat().st_mtime
                prev_mtime = self._known_mtimes.get(path_str)

                if prev_mtime is None or mtime > prev_mtime:
                    # New or modified
                    self._known_mtimes[path_str] = mtime
                    data = self._read_json(path)
                    if data and not self._is_own_write(data):
                        changed_items.append(data)

            if changed_items:
                await self._sync_to_core(entity_type, changed_items)

        # Clean up mtimes for deleted files
        for path_str in list(self._known_mtimes):
            if path_str not in all_current_files:
                del self._known_mtimes[path_str]

    async def _sync_to_core(
        self, entity_type: str, items: list[dict[str, Any]]
    ) -> None:
        """Sync changed items to core via the appropriate sync endpoint."""
        endpoint = _SYNC_ENDPOINTS.get(entity_type)
        if not endpoint:
            log.warning(f"Unknown entity type: {entity_type}")
            return

        try:
            resp = await self._client.post(
                f"{self._core_url}{endpoint}",
                json={entity_type: items},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(items)} {entity_type} from files to core")
        except Exception as e:
            log.error(f"Failed to sync {entity_type} to core: {e}")

    def _read_json(self, path: Path) -> Optional[dict[str, Any]]:
        """Read and parse a JSON file, returning None on failure."""
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as e:
            log.warning(f"Failed to read {path}: {e}")
            return None

    def _is_own_write(self, data: dict[str, Any]) -> bool:
        """Check if this data was written by us (echo loop prevention)."""
        origin = data.get("_origin", "")
        return origin == self._my_user_id

"""Sync manager — orchestrates bidirectional store ↔ core sync.

This is the top-level coordinator that wires together:
    - WebhookReceiver: receives events from core
    - A webhook handler: writes to a durable store (Firebase, local files, etc.)
    - A store listener: watches for remote/external changes and syncs to core

The manager is backend-agnostic. It accepts any handler/listener pair
via factory methods, so Firebase, local file, or any other backend
can be plugged in.

Synced entity types: projects, tasks, sessions, teams, registries, events.

Startup sequence:
    1. Start webhook receiver (local HTTP server)
    2. Register webhook with core (subscribes to ALL events)
    3. Load existing data from store and sync to core
    4. Start store listener for external changes
    5. Ready — bidirectional sync active

Shutdown:
    1. Stop store listener
    2. Unregister webhook from core
    3. Stop webhook receiver
    4. Close connections
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional, Protocol

import httpx

from .webhook_receiver import WebhookReceiver

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# Protocols — handler and listener contracts
# ─────────────────────────────────────────────────────────


class WebhookHandler(Protocol):
    """Contract for webhook event handlers (Firebase, local file, etc.)."""

    async def handle(self, event_name: str, payload: dict[str, Any]) -> None: ...
    async def close(self) -> None: ...


class StoreListener(Protocol):
    """Contract for store change listeners (Firebase SSE, file watcher, etc.)."""

    async def start(self, team_id: str) -> None: ...
    async def stop(self) -> None: ...


class StoreLoader(Protocol):
    """Contract for loading initial data from a store."""

    def load_all_projects(self) -> list[dict[str, Any]]: ...
    def load_all_tasks(self) -> list[dict[str, Any]]: ...
    def load_all_sessions(self) -> list[dict[str, Any]]: ...
    def load_all_teams(self) -> list[dict[str, Any]]: ...
    def load_all_registries(self) -> list[dict[str, Any]]: ...


# ─────────────────────────────────────────────────────────
# Factory functions — create backend components
# ─────────────────────────────────────────────────────────


def create_firebase_backend(
    database_url: str,
    auth_params: dict[str, str],
    core_url: str,
    user_id: str,
    http_client: httpx.AsyncClient,
) -> tuple[WebhookHandler, StoreListener, None]:
    """Create Firebase handler + listener.

    Returns (handler, listener, loader).
    Loader is None because Firebase initial sync uses HTTP reads
    handled internally by the sync manager.
    """
    from .firebase_webhook_handler import FirebaseWebhookHandler
    from .firebase_listener import FirebaseListener

    handler = FirebaseWebhookHandler(
        database_url=database_url,
        auth_params=auth_params,
        client=http_client,
    )
    listener = FirebaseListener(
        database_url=database_url,
        auth_params=auth_params,
        core_url=core_url,
        my_user_id=user_id,
    )
    return handler, listener, None


def create_localfile_backend(
    storage_root: Path,
    core_url: str,
    user_id: str,
) -> tuple[WebhookHandler, StoreListener, StoreLoader]:
    """Create local file handler + listener + loader.

    Returns (handler, listener, loader).
    The handler also implements StoreLoader for reading initial state.
    """
    from .localfile_webhook_handler import LocalFileWebhookHandler
    from .localfile_listener import LocalFileListener

    handler = LocalFileWebhookHandler(storage_root=storage_root)
    listener = LocalFileListener(
        storage_root=storage_root,
        core_url=core_url,
        my_user_id=user_id,
    )
    return handler, listener, handler


# ─────────────────────────────────────────────────────────
# SyncManager — backend-agnostic orchestrator
# ─────────────────────────────────────────────────────────


class SyncManager:
    """Orchestrates bidirectional sync between core and a durable store.

    Usage with Firebase:
        sync = SyncManager.create_firebase(
            core_url="http://localhost:8000",
            database_url="https://project.firebaseio.com",
            auth_params={"auth": "<token>"},
            user_id="user_123",
            team_id="team_abc",
        )
        await sync.start()

    Usage with local files:
        sync = SyncManager.create_localfile(
            core_url="http://localhost:8000",
            storage_root=Path("~/.emdash/projects"),
            user_id="user_123",
            team_id="team_abc",
        )
        await sync.start()
    """

    def __init__(
        self,
        core_url: str,
        user_id: str,
        team_id: str,
        handler: WebhookHandler,
        listener: StoreListener,
        loader: Optional[StoreLoader] = None,
        # Firebase-specific (for HTTP-based initial sync)
        database_url: Optional[str] = None,
        auth_params: Optional[dict[str, str]] = None,
    ):
        self._core_url = core_url.rstrip("/")
        self._user_id = user_id
        self._team_id = team_id
        self._handler = handler
        self._listener = listener
        self._loader = loader
        self._database_url = database_url
        self._auth_params = auth_params or {}

        self._hook_id: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._receiver: Optional[WebhookReceiver] = None

    # ── Factory methods ───────────────────────────────────────

    @classmethod
    def create_firebase(
        cls,
        core_url: str,
        database_url: str,
        auth_params: dict[str, str],
        user_id: str,
        team_id: str,
    ) -> "SyncManager":
        """Create a sync manager backed by Firebase."""
        http_client = httpx.AsyncClient(timeout=15.0)
        handler, listener, loader = create_firebase_backend(
            database_url=database_url,
            auth_params=auth_params,
            core_url=core_url,
            user_id=user_id,
            http_client=http_client,
        )
        mgr = cls(
            core_url=core_url,
            user_id=user_id,
            team_id=team_id,
            handler=handler,
            listener=listener,
            loader=loader,
            database_url=database_url,
            auth_params=auth_params,
        )
        mgr._http_client = http_client
        return mgr

    @classmethod
    def create_localfile(
        cls,
        core_url: str,
        storage_root: Path,
        user_id: str,
        team_id: str,
    ) -> "SyncManager":
        """Create a sync manager backed by local JSON files."""
        handler, listener, loader = create_localfile_backend(
            storage_root=storage_root,
            core_url=core_url,
            user_id=user_id,
        )
        return cls(
            core_url=core_url,
            user_id=user_id,
            team_id=team_id,
            handler=handler,
            listener=listener,
            loader=loader,
        )

    # ── Lifecycle ─────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._receiver is not None and self._receiver.port is not None

    async def start(self) -> None:
        """Start bidirectional sync.

        Raises on failure so the caller can decide what to do.
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=15.0)

        # 1. Start webhook receiver
        self._receiver = WebhookReceiver(handler=self._handler.handle)
        port = await self._receiver.start()
        log.info(f"Webhook receiver started on port {port}")

        # 2. Register webhook with core
        resp = await self._http_client.post(
            f"{self._core_url}/api/multiuser/webhooks/register",
            json={
                "url": self._receiver.url,
                "events": ["*"],
                "metadata": {"user_id": self._user_id, "team_id": self._team_id},
            },
        )
        resp.raise_for_status()
        self._hook_id = resp.json().get("hook_id")
        log.info(f"Webhook registered with core: hook_id={self._hook_id}")

        # 3. Load existing data and sync to core
        await self._initial_sync()

        # 4. Start listener for external changes
        await self._listener.start(self._team_id)
        log.info("Bidirectional sync active")

    async def stop(self) -> None:
        """Stop all sync components."""
        # Stop listener
        if self._listener:
            await self._listener.stop()

        # Unregister webhook from core
        if self._hook_id and self._http_client:
            try:
                resp = await self._http_client.delete(
                    f"{self._core_url}/api/multiuser/webhooks/{self._hook_id}",
                )
                if resp.status_code < 400:
                    log.info(f"Webhook {self._hook_id} unregistered from core")
            except Exception as e:
                log.warning(f"Failed to unregister webhook: {e}")
            self._hook_id = None

        # Stop webhook receiver
        if self._receiver:
            await self._receiver.stop()
            self._receiver = None

        # Close handler
        if self._handler:
            await self._handler.close()

        # Close HTTP client
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        log.info("Sync manager stopped")

    # ── Initial sync ──────────────────────────────────────────

    async def _initial_sync(self) -> None:
        """Load data from store and push to core's in-memory state."""
        log.info(f"Loading data for team {self._team_id}...")

        if self._loader:
            # Local loader (file-based, in-process)
            projects = self._loader.load_all_projects()
            tasks = self._loader.load_all_tasks()
            sessions = self._loader.load_all_sessions()
            teams = self._loader.load_all_teams()
            registries = self._loader.load_all_registries()
        elif self._database_url:
            # Firebase (HTTP-based load)
            projects = await self._load_projects_from_firebase()
            tasks = await self._load_tasks_from_firebase(projects)
            sessions = await self._load_sessions_from_firebase()
            teams = await self._load_teams_from_firebase()
            registries = await self._load_registries_from_firebase()
        else:
            projects = []
            tasks = []
            sessions = []
            teams = []
            registries = []

        synced_any = False

        if projects:
            resp = await self._http_client.post(
                f"{self._core_url}/api/multiuser/sync/projects",
                json={"projects": projects},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(projects)} projects to core")
            synced_any = True

        if tasks:
            resp = await self._http_client.post(
                f"{self._core_url}/api/multiuser/sync/tasks",
                json={"tasks": tasks},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(tasks)} tasks to core")
            synced_any = True

        if sessions:
            resp = await self._http_client.post(
                f"{self._core_url}/api/multiuser/sync/sessions",
                json={"sessions": sessions},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(sessions)} sessions to core")
            synced_any = True

        if teams:
            resp = await self._http_client.post(
                f"{self._core_url}/api/multiuser/sync/teams",
                json={"teams": teams},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(teams)} teams to core")
            synced_any = True

        if registries:
            resp = await self._http_client.post(
                f"{self._core_url}/api/multiuser/sync/registries",
                json={"registries": registries},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(registries)} registries to core")
            synced_any = True

        if not synced_any:
            log.info("No existing data in store (fresh start)")

    async def _load_projects_from_firebase(self) -> list[dict[str, Any]]:
        """Load all projects for this team from Firebase."""
        url = f"{self._database_url}/teams/{self._team_id}/projects.json"
        try:
            resp = await self._http_client.get(url, params=self._auth_params)
            resp.raise_for_status()
            data = resp.json()
            if not data or not isinstance(data, dict):
                return []

            projects = []
            for project_id, project_data in data.items():
                if isinstance(project_data, dict):
                    state = project_data.get("state")
                    if state and isinstance(state, dict):
                        projects.append(state)
            return projects

        except Exception as e:
            log.warning(f"Failed to load projects from Firebase: {e}")
            return []

    async def _load_tasks_from_firebase(
        self, projects: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Load all tasks from Firebase, filtered to this team's projects."""
        url = f"{self._database_url}/tasks.json"
        try:
            resp = await self._http_client.get(url, params=self._auth_params)
            resp.raise_for_status()
            data = resp.json()
            if not data or not isinstance(data, dict):
                return []

            project_ids = {p.get("project_id") for p in projects if p.get("project_id")}

            tasks = []
            for task_id, task_data in data.items():
                if isinstance(task_data, dict) and "task_id" in task_data:
                    if not project_ids or task_data.get("project_id") in project_ids:
                        tasks.append(task_data)
            return tasks

        except Exception as e:
            log.warning(f"Failed to load tasks from Firebase: {e}")
            return []

    async def _load_sessions_from_firebase(self) -> list[dict[str, Any]]:
        """Load all sessions from Firebase."""
        url = f"{self._database_url}/sessions.json"
        try:
            resp = await self._http_client.get(url, params=self._auth_params)
            resp.raise_for_status()
            data = resp.json()
            if not data or not isinstance(data, dict):
                return []

            sessions = []
            for sid, session_data in data.items():
                if isinstance(session_data, dict):
                    state = session_data.get("state")
                    if state and isinstance(state, dict):
                        sessions.append(state)
            return sessions

        except Exception as e:
            log.warning(f"Failed to load sessions from Firebase: {e}")
            return []

    async def _load_teams_from_firebase(self) -> list[dict[str, Any]]:
        """Load all teams from Firebase."""
        url = f"{self._database_url}/teams.json"
        try:
            resp = await self._http_client.get(url, params=self._auth_params)
            resp.raise_for_status()
            data = resp.json()
            if not data or not isinstance(data, dict):
                return []

            teams = []
            for tid, team_data in data.items():
                if isinstance(team_data, dict) and "team_id" in team_data:
                    teams.append(team_data)
            return teams

        except Exception as e:
            log.warning(f"Failed to load teams from Firebase: {e}")
            return []

    async def _load_registries_from_firebase(self) -> list[dict[str, Any]]:
        """Load all registries from Firebase."""
        url = f"{self._database_url}/registries.json"
        try:
            resp = await self._http_client.get(url, params=self._auth_params)
            resp.raise_for_status()
            data = resp.json()
            if not data or not isinstance(data, dict):
                return []

            registries = []
            for tid, reg_data in data.items():
                if isinstance(reg_data, dict):
                    reg_data["team_id"] = tid
                    registries.append(reg_data)
            return registries

        except Exception as e:
            log.warning(f"Failed to load registries from Firebase: {e}")
            return []


# ─────────────────────────────────────────────────────────
# Convenience: auto-detect backend from environment
# ─────────────────────────────────────────────────────────


def create_sync(
    core_url: str,
    user_id: str,
    team_id: str,
) -> Optional[SyncManager]:
    """Create a SyncManager using env-var config.

    Checks EMDASH_MULTIUSER_PROVIDER to pick the backend:
        - "firebase": uses Firebase (requires FIREBASE_DATABASE_URL)
        - "local": uses local JSON files (~/.emdash/store)
        - unset: tries Firebase first, falls back to local

    Returns None if no backend can be configured.
    """
    provider = os.environ.get("EMDASH_MULTIUSER_PROVIDER", "").lower()
    log.info(f"create_sync: EMDASH_MULTIUSER_PROVIDER={provider!r}")

    if provider == "firebase" or (not provider and os.environ.get("FIREBASE_DATABASE_URL")):
        database_url = os.environ.get("FIREBASE_DATABASE_URL")
        if not database_url:
            log.warning("FIREBASE_DATABASE_URL not set, cannot create Firebase sync")
            return None

        auth_params: dict[str, str] = {}
        api_key = os.environ.get("FIREBASE_API_KEY")
        if api_key:
            auth_params["key"] = api_key

        log.info(f"create_sync: using Firebase backend (database_url={database_url[:50]}...)")
        return SyncManager.create_firebase(
            core_url=core_url,
            database_url=database_url,
            auth_params=auth_params,
            user_id=user_id,
            team_id=team_id,
        )

    # Local file backend (default fallback)
    storage_root = Path(
        os.environ.get("EMDASH_STORAGE_ROOT", str(Path.home() / ".emdash" / "projects"))
    )
    log.info(f"create_sync: using local file backend (storage_root={storage_root})")
    return SyncManager.create_localfile(
        core_url=core_url,
        storage_root=storage_root,
        user_id=user_id,
        team_id=team_id,
    )

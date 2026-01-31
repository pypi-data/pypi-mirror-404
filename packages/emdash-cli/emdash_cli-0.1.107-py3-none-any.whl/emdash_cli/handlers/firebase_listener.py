"""Firebase listener — watches for remote changes and syncs to core.

Listens to Firebase Realtime Database via SSE (Server-Sent Events)
streaming REST API. When another user's CLI writes to Firebase,
this listener detects the change and syncs it into the local core
server's in-memory state.

This is the "read path" of the bidirectional sync:

    Other user's CLI → Firebase → this listener → local core sync endpoint

Echo loop prevention:
    Each write to Firebase includes an `_origin` field with the user_id
    of the writer. This listener skips changes where `_origin` matches
    the local user, preventing infinite loops.
"""

import asyncio
import json
import logging
from typing import Any, Optional

import httpx

log = logging.getLogger(__name__)


class FirebaseListener:
    """Listens to Firebase changes and syncs them to the local core server.

    Uses Firebase REST SSE streaming:
        GET https://project.firebaseio.com/path.json?auth=TOKEN
        Accept: text/event-stream

    Watches paths for: sessions, teams, projects, tasks, registries.
    """

    def __init__(
        self,
        database_url: str,
        auth_params: dict[str, str],
        core_url: str,
        my_user_id: str,
    ):
        self._database_url = database_url.rstrip("/")
        self._auth_params = auth_params
        self._core_url = core_url.rstrip("/")
        self._my_user_id = my_user_id
        self._tasks: list[asyncio.Task] = []
        self._running = False
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self, team_id: str) -> None:
        """Start listening to Firebase changes for a team.

        Spawns background tasks that stream Firebase SSE events
        for all entity types under this team.
        """
        self._running = True
        self._client = httpx.AsyncClient(timeout=None)

        # Listen to project changes
        self._tasks.append(asyncio.create_task(
            self._stream_path(
                path=f"teams/{team_id}/projects",
                sync_type="projects",
            ),
            name=f"fb-listener-projects-{team_id}",
        ))

        # Listen to task changes (flat index)
        self._tasks.append(asyncio.create_task(
            self._stream_path(
                path="tasks",
                sync_type="tasks",
            ),
            name=f"fb-listener-tasks-{team_id}",
        ))

        # Listen to session changes
        self._tasks.append(asyncio.create_task(
            self._stream_path(
                path="sessions",
                sync_type="sessions",
            ),
            name=f"fb-listener-sessions-{team_id}",
        ))

        # Listen to team changes
        self._tasks.append(asyncio.create_task(
            self._stream_path(
                path="teams",
                sync_type="teams",
            ),
            name=f"fb-listener-teams-{team_id}",
        ))

        # Listen to registry changes
        self._tasks.append(asyncio.create_task(
            self._stream_path(
                path="registries",
                sync_type="registries",
            ),
            name=f"fb-listener-registries-{team_id}",
        ))

        log.info(f"Firebase listener started for team {team_id}")

    async def stop(self) -> None:
        """Stop all listeners."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        if self._client:
            await self._client.aclose()
            self._client = None
        log.info("Firebase listener stopped")

    async def _stream_path(self, path: str, sync_type: str) -> None:
        """Stream SSE events from a Firebase path.

        Firebase REST streaming format:
            event: put
            data: {"path":"/id/state","data":{...}}

            event: patch
            data: {"path":"/id/state","data":{...}}

            event: keep-alive
            data: null
        """
        url = f"{self._database_url}/{path}.json"
        params = {**self._auth_params}

        backoff = 1
        while self._running:
            try:
                log.debug(f"Connecting to Firebase stream: {path}")
                async with self._client.stream(
                    "GET",
                    url,
                    params=params,
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    response.raise_for_status()
                    backoff = 1  # Reset on successful connection

                    event_type = None
                    async for line in response.aiter_lines():
                        if not self._running:
                            break

                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                            if event_type in ("put", "patch") and data_str != "null":
                                try:
                                    payload = json.loads(data_str)
                                    await self._handle_change(
                                        sync_type, event_type, payload
                                    )
                                except json.JSONDecodeError:
                                    log.warning(f"Invalid JSON from Firebase: {data_str[:100]}")
                            event_type = None

            except asyncio.CancelledError:
                break
            except Exception as e:
                if not self._running:
                    break
                log.warning(
                    f"Firebase stream {path} disconnected: {e}. "
                    f"Reconnecting in {backoff}s..."
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    async def _handle_change(
        self, sync_type: str, event_type: str, payload: dict[str, Any]
    ) -> None:
        """Process a Firebase SSE change event."""
        data = payload.get("data")
        path = payload.get("path", "/")

        if data is None:
            log.debug(f"Firebase deletion at {sync_type}{path}")
            return

        # Check origin — skip our own writes
        origin = None
        if isinstance(data, dict):
            origin = data.get("_origin") or data.get("state", {}).get("_origin")

        if origin == self._my_user_id:
            log.debug(f"Skipping own write at {sync_type}{path}")
            return

        # Sync to local core
        try:
            if sync_type == "projects":
                await self._sync_project_change(path, data)
            elif sync_type == "tasks":
                await self._sync_task_change(path, data)
            elif sync_type == "sessions":
                await self._sync_session_change(path, data)
            elif sync_type == "teams":
                await self._sync_team_change(path, data)
            elif sync_type == "registries":
                await self._sync_registry_change(path, data)
        except Exception as e:
            log.error(f"Failed to sync {sync_type} change to core: {e}")

    async def _sync_project_change(
        self, path: str, data: dict[str, Any]
    ) -> None:
        """Sync a project change from Firebase to core."""
        projects = []

        if path == "/":
            if isinstance(data, dict):
                for pid, project_data in data.items():
                    state = project_data.get("state") if isinstance(project_data, dict) else None
                    if state and isinstance(state, dict):
                        projects.append(state)
        else:
            parts = path.strip("/").split("/")
            if len(parts) >= 2 and parts[1] == "state" and isinstance(data, dict):
                projects.append(data)
            elif len(parts) == 1 and isinstance(data, dict):
                state = data.get("state")
                if state and isinstance(state, dict):
                    projects.append(state)

        if projects:
            resp = await self._client.post(
                f"{self._core_url}/api/multiuser/sync/projects",
                json={"projects": projects},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(projects)} project(s) from Firebase to core")

    async def _sync_task_change(
        self, path: str, data: dict[str, Any]
    ) -> None:
        """Sync a task change from Firebase to core."""
        tasks = []

        if path == "/":
            if isinstance(data, dict):
                for tid, task_data in data.items():
                    if isinstance(task_data, dict) and "task_id" in task_data:
                        tasks.append(task_data)
        else:
            parts = path.strip("/").split("/")
            if len(parts) == 1 and isinstance(data, dict) and "task_id" in data:
                tasks.append(data)

        if tasks:
            resp = await self._client.post(
                f"{self._core_url}/api/multiuser/sync/tasks",
                json={"tasks": tasks},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(tasks)} task(s) from Firebase to core")

    async def _sync_session_change(
        self, path: str, data: dict[str, Any]
    ) -> None:
        """Sync a session change from Firebase to core."""
        sessions = []

        if path == "/":
            # Full tree: data = { session_id: { state: {...} }, ... }
            if isinstance(data, dict):
                for sid, session_data in data.items():
                    state = session_data.get("state") if isinstance(session_data, dict) else None
                    if state and isinstance(state, dict):
                        sessions.append(state)
        else:
            parts = path.strip("/").split("/")
            if len(parts) >= 2 and parts[1] == "state" and isinstance(data, dict):
                sessions.append(data)
            elif len(parts) == 1 and isinstance(data, dict):
                state = data.get("state")
                if state and isinstance(state, dict):
                    sessions.append(state)

        if sessions:
            resp = await self._client.post(
                f"{self._core_url}/api/multiuser/sync/sessions",
                json={"sessions": sessions},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(sessions)} session(s) from Firebase to core")

    async def _sync_team_change(
        self, path: str, data: dict[str, Any]
    ) -> None:
        """Sync a team change from Firebase to core."""
        teams = []

        if path == "/":
            # Full tree: data = { team_id: {...}, ... }
            if isinstance(data, dict):
                for tid, team_data in data.items():
                    if isinstance(team_data, dict) and "team_id" in team_data:
                        teams.append(team_data)
        else:
            parts = path.strip("/").split("/")
            if len(parts) == 1 and isinstance(data, dict) and "team_id" in data:
                teams.append(data)

        if teams:
            resp = await self._client.post(
                f"{self._core_url}/api/multiuser/sync/teams",
                json={"teams": teams},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(teams)} team(s) from Firebase to core")

    async def _sync_registry_change(
        self, path: str, data: dict[str, Any]
    ) -> None:
        """Sync a registry change from Firebase to core."""
        registries = []

        if path == "/":
            # Full tree: data = { team_id: {...}, ... }
            if isinstance(data, dict):
                for tid, reg_data in data.items():
                    if isinstance(reg_data, dict):
                        reg_data["team_id"] = tid
                        registries.append(reg_data)
        else:
            parts = path.strip("/").split("/")
            if len(parts) == 1 and isinstance(data, dict):
                data["team_id"] = parts[0]
                registries.append(data)

        if registries:
            resp = await self._client.post(
                f"{self._core_url}/api/multiuser/sync/registries",
                json={"registries": registries},
            )
            resp.raise_for_status()
            log.info(f"Synced {len(registries)} registry(ies) from Firebase to core")

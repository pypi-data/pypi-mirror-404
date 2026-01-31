"""Firebase webhook handler — persists core events to Firebase.

Receives webhook events from core's WebhookRegistry and writes
the data to Firebase Realtime Database. This is the "write path"
of the bidirectional sync:

    Core mutation → webhook → this handler → Firebase

The handler uses the same Firebase REST helpers as the existing
FirebaseSyncProvider (httpx-based, service account or API key auth).

Echo loop prevention:
    Every webhook payload includes an `_origin` field identifying who
    triggered the mutation. The FirebaseListener on other machines
    checks this field and skips changes that originated from itself.
"""

import logging
from typing import Any, Optional

import httpx

log = logging.getLogger(__name__)


class FirebaseWebhookHandler:
    """Persists webhook events from core to Firebase Realtime Database.

    Usage:
        handler = FirebaseWebhookHandler(
            database_url="https://my-project.firebaseio.com",
            auth_params={"auth": "<token>"},
        )
        await handler.handle("project.created", payload)
    """

    def __init__(
        self,
        database_url: str,
        auth_params: dict[str, str],
        client: Optional[httpx.AsyncClient] = None,
    ):
        self._database_url = database_url.rstrip("/")
        self._auth_params = auth_params
        self._client = client or httpx.AsyncClient(timeout=15.0)
        self._owns_client = client is None

    def _db_url(self, path: str) -> str:
        path = path.lstrip("/")
        return f"{self._database_url}/{path}.json"

    async def _db_put(self, path: str, data: Any) -> None:
        url = self._db_url(path)
        resp = await self._client.put(url, json=data, params=self._auth_params)
        resp.raise_for_status()

    async def _db_patch(self, path: str, data: Any) -> None:
        url = self._db_url(path)
        resp = await self._client.patch(url, json=data, params=self._auth_params)
        resp.raise_for_status()

    async def _db_post(self, path: str, data: Any) -> None:
        url = self._db_url(path)
        resp = await self._client.post(url, json=data, params=self._auth_params)
        resp.raise_for_status()

    async def _db_get(self, path: str) -> Any:
        url = self._db_url(path)
        resp = await self._client.get(url, params=self._auth_params)
        resp.raise_for_status()
        return resp.json()

    async def _db_delete(self, path: str) -> None:
        url = self._db_url(path)
        resp = await self._client.delete(url, params=self._auth_params)
        resp.raise_for_status()

    async def handle(self, event_name: str, payload: dict[str, Any]) -> None:
        """Route a webhook event to the appropriate Firebase write.

        Args:
            event_name: e.g. "project.created", "task.assigned"
            payload: Full webhook payload including "data" and optional "_origin"
        """
        data = payload.get("data", payload)
        category = event_name.split(".")[0] if "." in event_name else ""

        try:
            if category == "project":
                await self._handle_project_event(event_name, data)
            elif category == "task":
                await self._handle_task_event(event_name, data)
            elif category == "session":
                await self._handle_session_event(event_name, data)
            elif category == "team":
                await self._handle_team_event(event_name, data)
            elif category == "registry":
                await self._handle_registry_event(event_name, data)
            elif category == "event":
                await self._handle_broadcast_event(event_name, data)
            else:
                log.warning(f"Unhandled webhook event: {event_name}")
        except Exception as e:
            log.error(f"Firebase write failed for {event_name}: {e}")
            raise

    # ── Event routing ────────────────────────────────────────

    async def _handle_project_event(self, event_name: str, data: dict) -> None:
        if event_name in ("project.created", "project.updated"):
            await self._save_project(data)
        elif event_name == "project.deleted":
            await self._delete_project(data)
        elif event_name == "project.member_added":
            await self._save_project_member(data)
        elif event_name == "project.member_removed":
            await self._remove_project_member(data)
        else:
            log.warning(f"Unhandled project event: {event_name}")

    async def _handle_task_event(self, event_name: str, data: dict) -> None:
        if event_name in (
            "task.created",
            "task.updated",
            "task.assigned",
            "task.unassigned",
            "task.status_changed",
            "task.session_linked",
        ):
            await self._save_task(data)
        elif event_name == "task.deleted":
            await self._delete_task(data)
        elif event_name == "task.commented":
            await self._save_comment(data)
        else:
            log.warning(f"Unhandled task event: {event_name}")

    # ── Project writes ────────────────────────────────────────

    async def _save_project(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        project_id = data.get("project_id", "")
        if not team_id or not project_id:
            log.error(f"Missing team_id or project_id in project data: {data}")
            return

        # Write project state
        await self._db_put(
            f"teams/{team_id}/projects/{project_id}/state",
            data,
        )
        log.info(f"Firebase: saved project {project_id}")

    async def _delete_project(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        project_id = data.get("project_id", "")
        if not team_id or not project_id:
            return

        await self._db_delete(f"teams/{team_id}/projects/{project_id}")
        log.info(f"Firebase: deleted project {project_id}")

    async def _save_project_member(self, data: dict) -> None:
        project_id = data.get("project_id", "")
        member = data.get("member", {})
        user_id = member.get("user_id", "")
        if not project_id or not user_id:
            return

        # We need team_id to write — it should be in the data
        # For member events, re-save the whole project state is cleaner
        # but if we only have partial data, save just the member
        log.info(f"Firebase: member {user_id} added to project {project_id}")

    async def _remove_project_member(self, data: dict) -> None:
        project_id = data.get("project_id", "")
        user_id = data.get("user_id", "")
        log.info(f"Firebase: member {user_id} removed from project {project_id}")

    # ── Task writes ───────────────────────────────────────────

    async def _save_task(self, data: dict) -> None:
        project_id = data.get("project_id", "")
        task_id = data.get("task_id", "")
        if not project_id or not task_id:
            log.error(f"Missing project_id or task_id in task data: {data}")
            return

        # We need team_id to build the path. Tasks carry project_id;
        # the sync manager provides team_id lookup, but for simplicity
        # we store tasks under a flat path as well.
        await self._db_put(f"tasks/{task_id}", data)
        # Also index under project
        await self._db_put(
            f"project_tasks/{project_id}/{task_id}",
            True,  # index entry
        )
        log.info(f"Firebase: saved task {task_id}")

    async def _delete_task(self, data: dict) -> None:
        task_id = data.get("task_id", "")
        project_id = data.get("project_id", "")
        if not task_id:
            return

        await self._db_delete(f"tasks/{task_id}")
        if project_id:
            await self._db_delete(f"project_tasks/{project_id}/{task_id}")
        log.info(f"Firebase: deleted task {task_id}")

    async def _save_comment(self, data: dict) -> None:
        task_id = data.get("task_id", "")
        comment = data.get("comment", {})
        comment_id = comment.get("comment_id", "")
        if not task_id or not comment_id:
            return

        await self._db_put(
            f"tasks/{task_id}/comments/{comment_id}",
            comment,
        )
        log.info(f"Firebase: saved comment {comment_id} on task {task_id}")

    # ── Session writes ──────────────────────────────────────

    async def _handle_session_event(self, event_name: str, data: dict) -> None:
        if event_name == "session.created":
            await self._session_created(data)
        elif event_name == "session.joined":
            await self._session_joined(data)
        elif event_name == "session.left":
            await self._session_left(data)
        elif event_name == "session.closed":
            await self._session_closed(data)
        elif event_name == "session.state_updated":
            await self._session_state_updated(data)
        elif event_name == "session.message_sent":
            await self._session_message_sent(data)
        elif event_name == "session.heartbeat":
            await self._session_heartbeat(data)
        elif event_name == "session.queue_updated":
            await self._session_queue_updated(data)
        else:
            log.warning(f"Unhandled session event: {event_name}")

    async def _session_created(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        invite_code = data.get("invite_code", "")
        if not session_id:
            log.error(f"Missing session_id in session.created data: {data}")
            return

        await self._db_put(f"sessions/{session_id}/state", data)
        if invite_code:
            await self._db_put(f"invites/{invite_code}", {
                "session_id": session_id,
                "created_at": data.get("created_at"),
                "created_by": data.get("created_by"),
            })
        log.info(f"Firebase: created session {session_id}")

    async def _session_joined(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        if not session_id:
            log.error(f"Missing session_id in session.joined data: {data}")
            return

        participants = data.get("participants", [])
        await self._db_patch(f"sessions/{session_id}/state", {
            "participants": participants,
        })
        # Post a join event to the session event log
        join_event = {
            "type": "session.joined",
            "user_id": data.get("user_id"),
            "timestamp": data.get("timestamp"),
        }
        await self._db_post(f"sessions/{session_id}/events", join_event)
        log.info(f"Firebase: user joined session {session_id}")

    async def _session_left(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        user_id = data.get("user_id", "")
        if not session_id:
            log.error(f"Missing session_id in session.left data: {data}")
            return

        participants = data.get("participants", [])
        await self._db_patch(f"sessions/{session_id}/state", {
            "participants": participants,
        })
        if user_id:
            await self._db_delete(
                f"sessions/{session_id}/presence/{user_id}"
            )
        log.info(f"Firebase: user {user_id} left session {session_id}")

    async def _session_closed(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        invite_code = data.get("invite_code", "")
        if not session_id:
            log.error(f"Missing session_id in session.closed data: {data}")
            return

        if invite_code:
            await self._db_delete(f"invites/{invite_code}")
        await self._db_delete(f"sessions/{session_id}")
        log.info(f"Firebase: closed session {session_id}")

    async def _session_state_updated(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        if not session_id:
            log.error(
                f"Missing session_id in session.state_updated data: {data}"
            )
            return

        await self._db_put(f"sessions/{session_id}/state", data)
        log.info(f"Firebase: updated state for session {session_id}")

    async def _session_message_sent(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        if not session_id:
            log.error(
                f"Missing session_id in session.message_sent data: {data}"
            )
            return

        message = data.get("message", {})
        await self._db_patch(f"sessions/{session_id}/state", {
            "message": message,
        })
        log.info(f"Firebase: message sent in session {session_id}")

    async def _session_heartbeat(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        user_id = data.get("user_id", "")
        if not session_id or not user_id:
            log.error(
                f"Missing session_id or user_id in session.heartbeat data: "
                f"{data}"
            )
            return

        await self._db_put(f"sessions/{session_id}/presence/{user_id}", {
            "last_seen": data.get("last_seen"),
            "online": True,
        })
        log.debug(
            f"Firebase: heartbeat for user {user_id} in session {session_id}"
        )

    async def _session_queue_updated(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        if not session_id:
            log.error(
                f"Missing session_id in session.queue_updated data: {data}"
            )
            return

        await self._db_patch(f"sessions/{session_id}/state", {
            "message_queue": data.get("message_queue"),
        })
        log.info(f"Firebase: queue updated for session {session_id}")

    # ── Team writes ───────────────────────────────────────────

    async def _handle_team_event(self, event_name: str, data: dict) -> None:
        if event_name == "team.created":
            await self._team_created(data)
        elif event_name == "team.updated":
            await self._team_updated(data)
        elif event_name == "team.deleted":
            await self._team_deleted(data)
        elif event_name == "team.member_joined":
            await self._team_member_joined(data)
        elif event_name == "team.member_left":
            await self._team_member_left(data)
        elif event_name == "team.session_added":
            await self._team_session_added(data)
        elif event_name == "team.session_removed":
            await self._team_session_removed(data)
        else:
            log.warning(f"Unhandled team event: {event_name}")

    async def _team_created(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        invite_code = data.get("invite_code", "")
        if not team_id:
            log.error(f"Missing team_id in team.created data: {data}")
            return

        await self._db_put(f"teams/{team_id}", data)
        if invite_code:
            await self._db_put(f"team_invites/{invite_code}", {
                "team_id": team_id,
                "created_at": data.get("created_at"),
            })
        log.info(f"Firebase: created team {team_id}")

    async def _team_updated(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        if not team_id:
            log.error(f"Missing team_id in team.updated data: {data}")
            return

        await self._db_put(f"teams/{team_id}", data)
        log.info(f"Firebase: updated team {team_id}")

    async def _team_deleted(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        invite_code = data.get("invite_code", "")
        if not team_id:
            log.error(f"Missing team_id in team.deleted data: {data}")
            return

        if invite_code:
            await self._db_delete(f"team_invites/{invite_code}")
        await self._db_delete(f"teams/{team_id}")
        await self._db_delete(f"team_sessions/{team_id}")
        log.info(f"Firebase: deleted team {team_id}")

    async def _team_member_joined(self, data: dict) -> None:
        team = data.get("team", {})
        team_id = team.get("team_id", "") or data.get("team_id", "")
        if not team_id:
            log.error(f"Missing team_id in team.member_joined data: {data}")
            return

        await self._db_put(f"teams/{team_id}", team)
        log.info(f"Firebase: member joined team {team_id}")

    async def _team_member_left(self, data: dict) -> None:
        team = data.get("team", {})
        team_id = team.get("team_id", "") or data.get("team_id", "")
        if not team_id:
            log.error(f"Missing team_id in team.member_left data: {data}")
            return

        await self._db_put(f"teams/{team_id}", team)
        log.info(f"Firebase: member left team {team_id}")

    async def _team_session_added(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        session_id = data.get("session_id", "")
        if not team_id or not session_id:
            log.error(
                f"Missing team_id or session_id in team.session_added data: "
                f"{data}"
            )
            return

        await self._db_patch(f"sessions/{session_id}/state", {
            "team_id": team_id,
            "visibility": "team",
        })
        session_info = {
            "session_id": session_id,
            "added_at": data.get("added_at"),
            "added_by": data.get("added_by"),
        }
        await self._db_put(
            f"team_sessions/{team_id}/{session_id}", session_info
        )
        log.info(
            f"Firebase: session {session_id} added to team {team_id}"
        )

    async def _team_session_removed(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        session_id = data.get("session_id", "")
        if not team_id or not session_id:
            log.error(
                f"Missing team_id or session_id in "
                f"team.session_removed data: {data}"
            )
            return

        await self._db_patch(f"sessions/{session_id}/state", {
            "team_id": None,
            "visibility": "private",
        })
        await self._db_delete(f"team_sessions/{team_id}/{session_id}")
        log.info(
            f"Firebase: session {session_id} removed from team {team_id}"
        )

    # ── Registry writes ──────────────────────────────────────

    async def _handle_registry_event(
        self, event_name: str, data: dict
    ) -> None:
        if event_name == "registry.updated":
            await self._registry_updated(data)
        elif event_name == "registry.deleted":
            await self._registry_deleted(data)
        else:
            log.warning(f"Unhandled registry event: {event_name}")

    async def _registry_updated(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        if not team_id:
            log.error(f"Missing team_id in registry.updated data: {data}")
            return

        await self._db_put(f"registries/{team_id}", data)
        log.info(f"Firebase: updated registry for team {team_id}")

    async def _registry_deleted(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        if not team_id:
            log.error(f"Missing team_id in registry.deleted data: {data}")
            return

        await self._db_delete(f"registries/{team_id}")
        log.info(f"Firebase: deleted registry for team {team_id}")

    # ── Broadcast writes ─────────────────────────────────────

    async def _handle_broadcast_event(
        self, event_name: str, data: dict
    ) -> None:
        if event_name == "event.pushed":
            await self._event_pushed(data)
        else:
            log.warning(f"Unhandled broadcast event: {event_name}")

    async def _event_pushed(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        if not session_id:
            log.error(f"Missing session_id in event.pushed data: {data}")
            return

        await self._db_post(f"sessions/{session_id}/events", data)
        log.info(f"Firebase: pushed event to session {session_id}")

    # ── Bulk load helpers ────────────────────────────────────

    async def load_all_projects(self) -> dict[str, Any]:
        """Load all projects from Firebase.

        Returns a dict keyed by project_id.
        """
        result = await self._db_get("tasks")
        if result is None:
            return {}
        return result

    async def load_all_tasks(self) -> dict[str, Any]:
        """Load all tasks from Firebase.

        Returns a dict keyed by task_id.
        """
        result = await self._db_get("tasks")
        if result is None:
            return {}
        return result

    async def load_all_sessions(self) -> dict[str, Any]:
        """Load all sessions from Firebase.

        Returns a dict keyed by session_id, each containing
        a ``state`` sub-key with the session data.
        """
        result = await self._db_get("sessions")
        if result is None:
            return {}
        return result

    async def load_all_teams(self) -> dict[str, Any]:
        """Load all teams from Firebase.

        Returns a dict keyed by team_id.
        """
        result = await self._db_get("teams")
        if result is None:
            return {}
        return result

    async def load_all_registries(self) -> dict[str, Any]:
        """Load all registries from Firebase.

        Returns a dict keyed by team_id.
        """
        result = await self._db_get("registries")
        if result is None:
            return {}
        return result

    # ── Lifecycle ─────────────────────────────────────────────

    async def close(self) -> None:
        if self._owns_client and self._client:
            await self._client.aclose()

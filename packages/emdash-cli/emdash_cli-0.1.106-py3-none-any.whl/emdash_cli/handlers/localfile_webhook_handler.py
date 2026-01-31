"""Local file webhook handler — persists core events to JSON files.

Receives webhook events from core's WebhookRegistry and writes
the data to local JSON files. This is the file-based equivalent
of FirebaseWebhookHandler.

    Core mutation → webhook → this handler → local JSON files

Directory structure:
    {storage_root}/
        projects/
            {project_id}.json
        tasks/
            {task_id}.json
        sessions/
            {session_id}.json
        teams/
            {team_id}.json
        registries/
            {team_id}.json
        events/
            {session_id}.jsonl

Each write also updates a `.last_change` marker file so the
LocalFileListener can detect changes efficiently.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class LocalFileWebhookHandler:
    """Persists webhook events from core to local JSON files.

    Usage:
        handler = LocalFileWebhookHandler(
            storage_root=Path("~/.emdash/projects"),
        )
        await handler.handle("project.created", payload)
    """

    def __init__(self, storage_root: Path):
        self._root = storage_root
        self._projects_dir = self._root / "projects"
        self._tasks_dir = self._root / "tasks"
        self._sessions_dir = self._root / "sessions"
        self._teams_dir = self._root / "teams"
        self._registries_dir = self._root / "registries"
        self._events_dir = self._root / "events"
        self._projects_dir.mkdir(parents=True, exist_ok=True)
        self._tasks_dir.mkdir(parents=True, exist_ok=True)
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        self._teams_dir.mkdir(parents=True, exist_ok=True)
        self._registries_dir.mkdir(parents=True, exist_ok=True)
        self._events_dir.mkdir(parents=True, exist_ok=True)

    def _write_json(self, path: Path, data: Any) -> None:
        """Write data as JSON and touch the change marker."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        # Touch marker so the listener can detect changes
        marker = self._root / ".last_change"
        marker.write_text(str(time.time()))

    def _delete_file(self, path: Path) -> None:
        """Delete a file and touch the change marker."""
        if path.exists():
            path.unlink()
            marker = self._root / ".last_change"
            marker.write_text(str(time.time()))

    async def handle(self, event_name: str, payload: dict[str, Any]) -> None:
        """Route a webhook event to the appropriate file write.

        Same signature as FirebaseWebhookHandler.handle().
        """
        data = payload.get("data", payload)

        try:
            if event_name in ("project.created", "project.updated"):
                self._save_project(data)
            elif event_name == "project.deleted":
                self._delete_project(data)
            elif event_name == "project.member_added":
                self._save_project_member(data)
            elif event_name == "project.member_removed":
                self._remove_project_member(data)
            elif event_name in (
                "task.created",
                "task.updated",
                "task.assigned",
                "task.unassigned",
                "task.status_changed",
                "task.session_linked",
            ):
                self._save_task(data)
            elif event_name == "task.deleted":
                self._delete_task(data)
            elif event_name == "task.commented":
                self._save_task_with_comment(data)

            # ── Session events ────────────────────────────────
            elif event_name in (
                "session.created",
                "session.joined",
                "session.left",
                "session.state_updated",
                "session.message_sent",
                "session.queue_updated",
                "session.linked_to_project",
            ):
                self._save_session(data)
            elif event_name == "session.closed":
                self._delete_session(data)
            elif event_name == "session.heartbeat":
                self._save_session_heartbeat(data)

            # ── Team events ───────────────────────────────────
            elif event_name in ("team.created", "team.updated"):
                self._save_team(data)
            elif event_name == "team.deleted":
                self._delete_team(data)
            elif event_name in (
                "team.member_joined",
                "team.member_left",
            ):
                self._save_team_from_nested(data)
            elif event_name in (
                "team.session_added",
                "team.session_removed",
            ):
                self._save_team_from_nested(data)

            # ── Registry events ───────────────────────────────
            elif event_name == "registry.updated":
                self._save_registry(data)
            elif event_name == "registry.deleted":
                self._delete_registry(data)

            # ── Broadcast events ──────────────────────────────
            elif event_name == "event.pushed":
                self._append_event(data)

            else:
                log.warning(f"Unhandled webhook event: {event_name}")
        except Exception as e:
            log.error(f"File write failed for {event_name}: {e}")
            raise

    # ── Project writes ────────────────────────────────────────

    def _save_project(self, data: dict) -> None:
        project_id = data.get("project_id", "")
        if not project_id:
            log.error(f"Missing project_id in project data: {data}")
            return

        path = self._projects_dir / f"{project_id}.json"
        self._write_json(path, data)
        log.info(f"File: saved project {project_id}")

    def _delete_project(self, data: dict) -> None:
        project_id = data.get("project_id", "")
        if not project_id:
            return

        path = self._projects_dir / f"{project_id}.json"
        self._delete_file(path)

        # Also delete tasks belonging to this project
        for task_file in self._tasks_dir.glob("*.json"):
            try:
                task_data = json.loads(task_file.read_text())
                if task_data.get("project_id") == project_id:
                    task_file.unlink()
            except (json.JSONDecodeError, OSError):
                pass

        log.info(f"File: deleted project {project_id}")

    def _save_project_member(self, data: dict) -> None:
        # Member changes are reflected in the full project state.
        # The project.updated event fires alongside member events,
        # so the project file gets the updated members list.
        project_id = data.get("project_id", "")
        member = data.get("member", {})
        user_id = member.get("user_id", "")
        log.info(f"File: member {user_id} added to project {project_id}")

    def _remove_project_member(self, data: dict) -> None:
        project_id = data.get("project_id", "")
        user_id = data.get("user_id", "")
        log.info(f"File: member {user_id} removed from project {project_id}")

    # ── Task writes ───────────────────────────────────────────

    def _save_task(self, data: dict) -> None:
        task_id = data.get("task_id", "")
        if not task_id:
            log.error(f"Missing task_id in task data: {data}")
            return

        path = self._tasks_dir / f"{task_id}.json"
        self._write_json(path, data)
        log.info(f"File: saved task {task_id}")

    def _delete_task(self, data: dict) -> None:
        task_id = data.get("task_id", "")
        if not task_id:
            return

        path = self._tasks_dir / f"{task_id}.json"
        self._delete_file(path)
        log.info(f"File: deleted task {task_id}")

    def _save_task_with_comment(self, data: dict) -> None:
        # For comments, the task file already has the full task state
        # (the task.updated webhook fires alongside task.commented).
        # Log for visibility.
        task_id = data.get("task_id", "")
        comment = data.get("comment", {})
        comment_id = comment.get("comment_id", "")
        log.info(f"File: comment {comment_id} on task {task_id}")

    # ── Session writes ─────────────────────────────────────────

    def _save_session(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        if not session_id:
            log.error(f"Missing session_id in session data: {data}")
            return

        path = self._sessions_dir / f"{session_id}.json"
        self._write_json(path, data)
        log.info(f"File: saved session {session_id}")

    def _delete_session(self, data: dict) -> None:
        session_id = data.get("session_id", "")
        if not session_id:
            return

        path = self._sessions_dir / f"{session_id}.json"
        self._delete_file(path)
        log.info(f"File: deleted session {session_id}")

    def _save_session_heartbeat(self, data: dict) -> None:
        """Update presence info in the session file.

        The heartbeat payload typically contains session_id and
        presence metadata (user_id, timestamp, status). We merge
        the heartbeat into the existing session file or write a
        dedicated presence entry.
        """
        session_id = data.get("session_id", "")
        if not session_id:
            log.error(f"Missing session_id in heartbeat data: {data}")
            return

        path = self._sessions_dir / f"{session_id}.json"

        # Merge heartbeat into existing session data if available
        existing: dict = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        user_id = data.get("user_id", "unknown")
        presence = existing.get("presence", {})
        presence[user_id] = {
            "last_heartbeat": data.get("timestamp", time.time()),
            "status": data.get("status", "active"),
        }
        existing["presence"] = presence
        # Preserve the session_id in case the file was empty
        existing.setdefault("session_id", session_id)

        self._write_json(path, existing)
        log.info(f"File: heartbeat for session {session_id} user {user_id}")

    # ── Team writes ──────────────────────────────────────────

    def _save_team(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        if not team_id:
            log.error(f"Missing team_id in team data: {data}")
            return

        path = self._teams_dir / f"{team_id}.json"
        self._write_json(path, data)
        log.info(f"File: saved team {team_id}")

    def _delete_team(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        if not team_id:
            return

        path = self._teams_dir / f"{team_id}.json"
        self._delete_file(path)
        log.info(f"File: deleted team {team_id}")

    def _save_team_from_nested(self, data: dict) -> None:
        """Save team data from events that nest the team under data['team'].

        Used for member_joined, member_left, session_added,
        session_removed events where the full team dict is in
        data["team"].
        """
        team_data = data.get("team", {})
        team_id = team_data.get("team_id", "") or data.get("team_id", "")
        if not team_id:
            log.error(f"Missing team_id in nested team data: {data}")
            return

        # Use the nested team dict if present, otherwise the top-level data
        to_write = team_data if team_data else data
        path = self._teams_dir / f"{team_id}.json"
        self._write_json(path, to_write)
        log.info(f"File: saved team {team_id} (nested update)")

    # ── Registry writes ──────────────────────────────────────

    def _save_registry(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        if not team_id:
            log.error(f"Missing team_id in registry data: {data}")
            return

        path = self._registries_dir / f"{team_id}.json"
        self._write_json(path, data)
        log.info(f"File: saved registry for team {team_id}")

    def _delete_registry(self, data: dict) -> None:
        team_id = data.get("team_id", "")
        if not team_id:
            return

        path = self._registries_dir / f"{team_id}.json"
        self._delete_file(path)
        log.info(f"File: deleted registry for team {team_id}")

    # ── Broadcast event writes ───────────────────────────────

    def _append_event(self, data: dict) -> None:
        """Append a broadcast event as a JSON line.

        Events are stored per-session in JSONL format so consumers
        can tail/stream them.
        """
        session_id = data.get("session_id", "")
        if not session_id:
            log.error(f"Missing session_id in broadcast event: {data}")
            return

        path = self._events_dir / f"{session_id}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps(data) + "\n")

        # Touch marker so the listener can detect changes
        marker = self._root / ".last_change"
        marker.write_text(str(time.time()))
        log.info(f"File: appended event for session {session_id}")

    # ── Read helpers (used by sync manager for initial load) ──

    def load_all_projects(self) -> list[dict[str, Any]]:
        """Load all projects from disk."""
        projects = []
        for path in self._projects_dir.glob("*.json"):
            try:
                projects.append(json.loads(path.read_text()))
            except (json.JSONDecodeError, OSError) as e:
                log.warning(f"Failed to load {path}: {e}")
        return projects

    def load_all_tasks(self) -> list[dict[str, Any]]:
        """Load all tasks from disk."""
        tasks = []
        for path in self._tasks_dir.glob("*.json"):
            try:
                tasks.append(json.loads(path.read_text()))
            except (json.JSONDecodeError, OSError) as e:
                log.warning(f"Failed to load {path}: {e}")
        return tasks

    def load_all_sessions(self) -> list[dict[str, Any]]:
        """Load all sessions from disk."""
        sessions = []
        for path in self._sessions_dir.glob("*.json"):
            try:
                sessions.append(json.loads(path.read_text()))
            except (json.JSONDecodeError, OSError) as e:
                log.warning(f"Failed to load {path}: {e}")
        return sessions

    def load_all_teams(self) -> list[dict[str, Any]]:
        """Load all teams from disk."""
        teams = []
        for path in self._teams_dir.glob("*.json"):
            try:
                teams.append(json.loads(path.read_text()))
            except (json.JSONDecodeError, OSError) as e:
                log.warning(f"Failed to load {path}: {e}")
        return teams

    def load_all_registries(self) -> list[dict[str, Any]]:
        """Load all registries from disk."""
        registries = []
        for path in self._registries_dir.glob("*.json"):
            try:
                registries.append(json.loads(path.read_text()))
            except (json.JSONDecodeError, OSError) as e:
                log.warning(f"Failed to load {path}: {e}")
        return registries

    async def close(self) -> None:
        """No-op — file handles are opened and closed per write."""
        pass

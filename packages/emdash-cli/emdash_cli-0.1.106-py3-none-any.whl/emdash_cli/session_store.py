"""Session persistence for CLI conversations.

Manages saving and loading of conversation sessions to .emdash/sessions/.
Each session preserves messages, mode, and other state for later restoration.
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


MAX_SESSIONS = 5
MAX_MESSAGES = 10
SESSION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,49}$")


@dataclass
class SessionMetadata:
    """Metadata for a saved session."""
    name: str
    created_at: str
    updated_at: str
    message_count: int
    model: Optional[str] = None
    mode: str = "code"
    summary: Optional[str] = None


@dataclass
class SessionData:
    """Full session data including messages."""
    name: str
    messages: list[dict]
    mode: str
    model: Optional[str] = None
    spec: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        return cls(
            name=data.get("name", ""),
            messages=data.get("messages", []),
            mode=data.get("mode", "code"),
            model=data.get("model"),
            spec=data.get("spec"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


class SessionStore:
    """File-based session storage.

    Sessions are stored in .emdash/sessions/ with:
    - index.json: metadata for all sessions
    - {name}.json: individual session data

    Example:
        store = SessionStore()
        store.save_session("my-feature", messages, "code", None, "gpt-4")
        session = store.load_session("my-feature")
    """

    def __init__(self, repo_root: Optional[Path] = None):
        """Initialize session store.

        Args:
            repo_root: Repository root (defaults to cwd)
        """
        self.repo_root = repo_root or Path.cwd()
        self.sessions_dir = self.repo_root / ".emdash" / "sessions"

    def _ensure_dir(self) -> None:
        """Ensure sessions directory exists."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _index_path(self) -> Path:
        """Get path to index file."""
        return self.sessions_dir / "index.json"

    def _session_path(self, name: str) -> Path:
        """Get path to session file."""
        return self.sessions_dir / f"{name}.json"

    def _load_index(self) -> dict:
        """Load session index."""
        index_path = self._index_path()
        if index_path.exists():
            try:
                return json.loads(index_path.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return {"sessions": [], "active": None}

    def _save_index(self, index: dict) -> None:
        """Save session index."""
        self._ensure_dir()
        self._index_path().write_text(json.dumps(index, indent=2))

    def _validate_name(self, name: str) -> bool:
        """Validate session name.

        Args:
            name: Session name to validate

        Returns:
            True if valid
        """
        return bool(SESSION_NAME_PATTERN.match(name))

    def _generate_summary(self, messages: list[dict]) -> str:
        """Generate a brief summary from messages.

        Args:
            messages: List of message dicts

        Returns:
            Summary string (first user message truncated)
        """
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str) and content:
                    return content[:100] + ("..." if len(content) > 100 else "")
        return "No description"

    def list_sessions(self) -> list[SessionMetadata]:
        """List all saved sessions.

        Returns:
            List of session metadata, sorted by updated_at (newest first)
        """
        index = self._load_index()
        sessions = []
        for s in index.get("sessions", []):
            sessions.append(SessionMetadata(
                name=s.get("name", ""),
                created_at=s.get("created_at", ""),
                updated_at=s.get("updated_at", ""),
                message_count=s.get("message_count", 0),
                model=s.get("model"),
                mode=s.get("mode", "code"),
                summary=s.get("summary"),
            ))
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        return sessions

    def save_session(
        self,
        name: str,
        messages: list[dict],
        mode: str,
        spec: Optional[str] = None,
        model: Optional[str] = None,
    ) -> tuple[bool, str]:
        """Save a session.

        Args:
            name: Session name (alphanumeric, hyphens, underscores)
            messages: Conversation messages
            mode: Current mode (plan/code)
            spec: Current spec if any
            model: Model being used

        Returns:
            Tuple of (success, message)
        """
        # Validate name
        if not self._validate_name(name):
            return False, "Invalid session name. Use letters, numbers, hyphens, underscores (max 50 chars)"

        # Load index
        index = self._load_index()
        sessions = index.get("sessions", [])

        # Check if updating existing session
        existing_idx = None
        for i, s in enumerate(sessions):
            if s.get("name") == name:
                existing_idx = i
                break

        # Check limit for new sessions
        if existing_idx is None and len(sessions) >= MAX_SESSIONS:
            return False, f"Maximum {MAX_SESSIONS} sessions reached. Delete one first with /session delete <name>"

        now = datetime.utcnow().isoformat() + "Z"

        # Trim messages to most recent N
        trimmed_messages = messages[-MAX_MESSAGES:] if len(messages) > MAX_MESSAGES else messages

        # Create session data
        session_data = SessionData(
            name=name,
            messages=trimmed_messages,
            mode=mode,
            model=model,
            spec=spec,
            created_at=sessions[existing_idx]["created_at"] if existing_idx is not None else now,
            updated_at=now,
        )

        # Save session file
        self._ensure_dir()
        self._session_path(name).write_text(json.dumps(session_data.to_dict(), indent=2))

        # Update index
        metadata = {
            "name": name,
            "created_at": session_data.created_at,
            "updated_at": session_data.updated_at,
            "message_count": len(trimmed_messages),
            "model": model,
            "mode": mode,
            "summary": self._generate_summary(messages),
        }

        if existing_idx is not None:
            sessions[existing_idx] = metadata
        else:
            sessions.append(metadata)

        index["sessions"] = sessions
        self._save_index(index)

        return True, f"Session '{name}' saved ({len(trimmed_messages)} messages)"

    def load_session(self, name: str) -> Optional[SessionData]:
        """Load a session by name.

        Args:
            name: Session name

        Returns:
            SessionData or None if not found
        """
        session_path = self._session_path(name)
        if not session_path.exists():
            return None

        try:
            data = json.loads(session_path.read_text())
            return SessionData.from_dict(data)
        except (json.JSONDecodeError, IOError):
            return None

    def delete_session(self, name: str) -> tuple[bool, str]:
        """Delete a session.

        Args:
            name: Session name

        Returns:
            Tuple of (success, message)
        """
        index = self._load_index()
        sessions = index.get("sessions", [])

        # Find and remove from index
        found = False
        for i, s in enumerate(sessions):
            if s.get("name") == name:
                sessions.pop(i)
                found = True
                break

        if not found:
            return False, f"Session '{name}' not found"

        # Delete session file
        session_path = self._session_path(name)
        if session_path.exists():
            session_path.unlink()

        # Clear active if it was this session
        if index.get("active") == name:
            index["active"] = None

        index["sessions"] = sessions
        self._save_index(index)

        return True, f"Session '{name}' deleted"

    def get_active_session(self) -> Optional[str]:
        """Get the name of the active session.

        Returns:
            Session name or None
        """
        index = self._load_index()
        return index.get("active")

    def set_active_session(self, name: Optional[str]) -> None:
        """Set the active session.

        Args:
            name: Session name or None to clear
        """
        index = self._load_index()
        index["active"] = name
        self._save_index(index)

    def session_exists(self, name: str) -> bool:
        """Check if a session exists.

        Args:
            name: Session name

        Returns:
            True if session exists
        """
        return self._session_path(name).exists()

"""HTTP client for emdash-core API."""

import os
from typing import Any, Iterator, Optional

import httpx


def _get_max_iterations() -> int:
    """Get max iterations from env var with default."""
    return int(os.getenv("EMDASH_MAX_ITERATIONS", "100"))


class EmdashClient:
    """HTTP client for interacting with emdash-core API.

    This client handles:
    - Regular JSON API calls
    - SSE streaming for agent chat
    - Health checks
    """

    def __init__(self, base_url: str):
        """Initialize the client.

        Args:
            base_url: Base URL of emdash-core server
        """
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=None)  # No timeout for streaming

    def health(self) -> dict:
        """Check server health.

        Returns:
            Health status dict

        Raises:
            httpx.HTTPError: If request fails
        """
        response = self._client.get(
            f"{self.base_url}/api/health",
            timeout=5.0,
        )
        response.raise_for_status()
        return response.json()

    def agent_chat_stream(
        self,
        message: str,
        model: Optional[str] = None,
        session_id: Optional[str] = None,
        max_iterations: int = _get_max_iterations(),
        options: Optional[dict] = None,
        images: Optional[list[dict]] = None,
        history: Optional[list[dict]] = None,
    ) -> Iterator[str]:
        """Stream agent chat response via SSE.

        Args:
            message: User message/task
            model: Model to use (optional)
            session_id: Session ID for continuity (optional)
            max_iterations: Max agent iterations
            options: Additional options (mode, save, no_graph_tools, etc.)
            images: List of images [{"data": base64_str, "format": "png"}]
            history: Pre-loaded conversation history from saved session

        Yields:
            SSE lines from the response

        Raises:
            httpx.HTTPError: If request fails
        """
        # Build options with defaults
        request_options = {
            "max_iterations": max_iterations,
            "verbose": True,
        }

        # Merge additional options
        if options:
            request_options.update(options)

        payload = {
            "message": message,
            "options": request_options,
        }

        if model:
            payload["model"] = model
        if session_id:
            payload["session_id"] = session_id
        if images:
            payload["images"] = images
        if history:
            payload["history"] = history

        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/api/agent/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    yield line
        except GeneratorExit:
            # Stream was closed early (interrupted)
            pass

    def agent_continue_stream(
        self,
        session_id: str,
        message: str,
        images: Optional[list[dict]] = None,
    ) -> Iterator[str]:
        """Continue an existing agent session.

        Args:
            session_id: Existing session ID
            message: Continuation message
            images: List of images [{"data": base64_str, "format": "png"}]

        Yields:
            SSE lines from the response
        """
        payload = {"message": message}
        if images:
            payload["images"] = images

        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/api/agent/chat/{session_id}/continue",
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    yield line
        except GeneratorExit:
            # Stream was closed early (interrupted)
            pass

    def plan_approve_stream(self, session_id: str) -> Iterator[str]:
        """Approve a pending plan and start implementation.

        Args:
            session_id: Session ID with pending plan

        Yields:
            SSE lines from the response
        """
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/api/agent/chat/{session_id}/plan/approve",
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    yield line
        except GeneratorExit:
            pass

    def plan_reject_stream(self, session_id: str, feedback: str = "") -> Iterator[str]:
        """Reject a pending plan with feedback.

        Args:
            session_id: Session ID with pending plan
            feedback: Feedback explaining rejection

        Yields:
            SSE lines from the response
        """
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/api/agent/chat/{session_id}/plan/reject",
                params={"feedback": feedback},
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    yield line
        except GeneratorExit:
            pass

    def planmode_approve_stream(self, session_id: str) -> Iterator[str]:
        """Approve entering plan mode.

        Args:
            session_id: Session ID requesting plan mode

        Yields:
            SSE lines from the response
        """
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/api/agent/chat/{session_id}/planmode/approve",
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    yield line
        except GeneratorExit:
            pass

    def planmode_reject_stream(self, session_id: str, feedback: str = "") -> Iterator[str]:
        """Reject entering plan mode.

        Args:
            session_id: Session ID requesting plan mode
            feedback: Feedback explaining rejection

        Yields:
            SSE lines from the response
        """
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/api/agent/chat/{session_id}/planmode/reject",
                params={"feedback": feedback},
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    yield line
        except GeneratorExit:
            pass

    def clarification_answer_stream(self, session_id: str, answer: str) -> Iterator[str]:
        """Answer a pending clarification question.

        Args:
            session_id: Session ID with pending clarification
            answer: User's answer to the clarification question

        Yields:
            SSE lines from the response
        """
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/api/agent/chat/{session_id}/clarification/answer",
                params={"answer": answer},
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    yield line
        except GeneratorExit:
            pass

    def choice_questions_answer_stream(
        self, session_id: str, responses: list[dict]
    ) -> Iterator[str]:
        """Answer pending choice questions.

        Args:
            session_id: Session ID with pending choice questions
            responses: List of dicts with question and answer

        Yields:
            SSE lines from the response
        """
        import json
        try:
            with self._client.stream(
                "POST",
                f"{self.base_url}/api/agent/chat/{session_id}/choices/answer",
                json={"responses": responses},
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    yield line
        except GeneratorExit:
            pass

    def get(self, path: str) -> "httpx.Response":
        """Make a GET request to the API.

        Args:
            path: API path (e.g., "/api/agent/sessions")

        Returns:
            HTTP response
        """
        return self._client.get(f"{self.base_url}{path}")

    def post(self, path: str, json: dict | None = None) -> "httpx.Response":
        """Make a POST request to the API.

        Args:
            path: API path (e.g., "/api/agent/chat/123/compact")
            json: Optional JSON body

        Returns:
            HTTP response
        """
        return self._client.post(f"{self.base_url}{path}", json=json)

    def list_sessions(self) -> list[dict]:
        """List active agent sessions.

        Returns:
            List of session info dicts
        """
        response = self._client.get(f"{self.base_url}/api/agent/sessions")
        response.raise_for_status()
        return response.json().get("sessions", [])

    def delete_session(self, session_id: str) -> bool:
        """Delete an agent session.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted
        """
        response = self._client.delete(
            f"{self.base_url}/api/agent/sessions/{session_id}"
        )
        return response.status_code == 200

    def abort_chat(self, session_id: str) -> dict:
        """Abort a running chat session.

        Signals the agent to stop by marking the SSE handler as cancelled.
        The agent checks this flag at regular intervals and stops execution.

        Args:
            session_id: Session to abort

        Returns:
            Dict with session_id, aborted (bool), and optional reason
        """
        response = self._client.post(
            f"{self.base_url}/api/agent/chat/{session_id}/abort"
        )
        response.raise_for_status()
        return response.json()

    def search(
        self,
        query: str,
        search_type: str = "semantic",
        limit: int = 20,
    ) -> dict:
        """Search the codebase.

        Args:
            query: Search query
            search_type: Type of search (semantic, text, grep)
            limit: Maximum results

        Returns:
            Search response dict
        """
        response = self._client.post(
            f"{self.base_url}/api/query/search",
            json={
                "query": query,
                "type": search_type,
                "filters": {"limit": limit},
            },
        )
        response.raise_for_status()
        return response.json()

    def index_status(self, repo_path: str) -> dict:
        """Get indexing status for a repository.

        Args:
            repo_path: Path to repository

        Returns:
            Index status dict
        """
        response = self._client.get(
            f"{self.base_url}/api/index/status",
            params={"repo_path": repo_path}
        )
        response.raise_for_status()
        return response.json()

    def index_start_stream(
        self,
        repo_path: str,
        incremental: bool = False,
    ) -> Iterator[str]:
        """Start indexing with SSE streaming progress.

        Args:
            repo_path: Path to repository
            incremental: Only index changed files

        Yields:
            SSE lines from the response
        """
        payload = {
            "repo_path": repo_path,
            "options": {"incremental": incremental},
        }

        with self._client.stream(
            "POST",
            f"{self.base_url}/api/index/start",
            json=payload,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                yield line

    # ==================== Auth ====================

    def auth_login(self) -> dict:
        """Start GitHub OAuth device flow.

        Returns:
            Dict with user_code, verification_uri, expires_in, interval
        """
        response = self._client.post(f"{self.base_url}/api/auth/login")
        response.raise_for_status()
        return response.json()

    def auth_poll(self, user_code: str) -> dict:
        """Poll for login completion.

        Args:
            user_code: The user code from auth_login

        Returns:
            Dict with status (pending/success/expired/error), username, error
        """
        response = self._client.post(
            f"{self.base_url}/api/auth/login/poll/{user_code}"
        )
        response.raise_for_status()
        return response.json()

    def auth_logout(self) -> dict:
        """Sign out by removing stored credentials."""
        response = self._client.post(f"{self.base_url}/api/auth/logout")
        response.raise_for_status()
        return response.json()

    def auth_status(self) -> dict:
        """Get current authentication status.

        Returns:
            Dict with authenticated, username, scope
        """
        response = self._client.get(f"{self.base_url}/api/auth/status")
        response.raise_for_status()
        return response.json()

    # ==================== Database ====================

    def db_init(self) -> dict:
        """Initialize the database schema."""
        response = self._client.post(f"{self.base_url}/api/db/init")
        response.raise_for_status()
        return response.json()

    def db_clear(self, confirm: bool = True) -> dict:
        """Clear all data from the database."""
        response = self._client.post(
            f"{self.base_url}/api/db/clear",
            params={"confirm": confirm},
        )
        response.raise_for_status()
        return response.json()

    def db_stats(self) -> dict:
        """Get database statistics."""
        response = self._client.get(f"{self.base_url}/api/db/stats")
        response.raise_for_status()
        return response.json()

    def db_test(self) -> dict:
        """Test database connection."""
        response = self._client.get(f"{self.base_url}/api/db/test")
        response.raise_for_status()
        return response.json()

    # ==================== Statistics ====================

    def get_user_stats(self) -> dict:
        """Get aggregated user statistics.

        Returns:
            Dict with total_sessions, token counts, first_seen, last_active
        """
        response = self._client.get(f"{self.base_url}/api/stats")
        response.raise_for_status()
        return response.json()

    def get_session_stats(self, limit: int = 20) -> list:
        """Get list of sessions with statistics.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries with activity data
        """
        response = self._client.get(
            f"{self.base_url}/api/stats/sessions",
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json()

    def get_token_breakdown(self) -> dict:
        """Get detailed token usage breakdown.

        Returns:
            Dict with input_tokens, output_tokens, thinking_tokens, percentages
        """
        response = self._client.get(f"{self.base_url}/api/stats/tokens")
        response.raise_for_status()
        return response.json()

    def get_session_stats_realtime(self, session_id: str) -> dict:
        """Get real-time token usage and cost for a session.

        Args:
            session_id: Session ID to get stats for

        Returns:
            Dict with input_tokens, output_tokens, thinking_tokens,
            total_tokens, estimated_cost, cost_formatted, model
        """
        response = self._client.get(
            f"{self.base_url}/api/agent/chat/{session_id}/stats"
        )
        response.raise_for_status()
        return response.json()

    # ==================== Analytics ====================

    def analyze_pagerank(self, top: int = 20, damping: float = 0.85) -> dict:
        """Compute PageRank scores."""
        response = self._client.post(
            f"{self.base_url}/api/analyze/pagerank",
            json={"top": top, "damping": damping},
        )
        response.raise_for_status()
        return response.json()

    def analyze_communities(
        self,
        resolution: float = 1.0,
        min_size: int = 3,
        top: int = 20,
    ) -> dict:
        """Detect code communities."""
        response = self._client.post(
            f"{self.base_url}/api/analyze/communities",
            json={"resolution": resolution, "min_size": min_size, "top": top},
        )
        response.raise_for_status()
        return response.json()

    def analyze_areas(
        self,
        depth: int = 2,
        days: int = 30,
        top: int = 20,
        sort: str = "focus",
        files: bool = False,
    ) -> dict:
        """Get importance metrics by directory or file."""
        response = self._client.post(
            f"{self.base_url}/api/analyze/areas",
            json={
                "depth": depth,
                "days": days,
                "top": top,
                "sort": sort,
                "files": files,
            },
        )
        response.raise_for_status()
        return response.json()

    # ==================== Embeddings ====================

    def embed_status(self) -> dict:
        """Get embedding coverage statistics."""
        response = self._client.get(f"{self.base_url}/api/embed/status")
        response.raise_for_status()
        return response.json()

    def embed_models(self) -> list:
        """List available embedding models."""
        response = self._client.get(f"{self.base_url}/api/embed/models")
        response.raise_for_status()
        return response.json().get("models", [])

    def embed_index(
        self,
        include_prs: bool = True,
        include_functions: bool = True,
        include_classes: bool = True,
        reindex: bool = False,
    ) -> dict:
        """Generate embeddings for graph entities."""
        response = self._client.post(
            f"{self.base_url}/api/embed/index",
            json={
                "include_prs": include_prs,
                "include_functions": include_functions,
                "include_classes": include_classes,
                "reindex": reindex,
            },
        )
        response.raise_for_status()
        return response.json()

    # ==================== Rules/Templates ====================

    def rules_list(self) -> list:
        """List all templates."""
        response = self._client.get(f"{self.base_url}/api/rules/list")
        response.raise_for_status()
        return response.json().get("templates", [])

    def rules_get(self, template_name: str) -> dict:
        """Get a template's content."""
        response = self._client.get(f"{self.base_url}/api/rules/{template_name}")
        response.raise_for_status()
        return response.json()

    def rules_init(self, global_templates: bool = False, force: bool = False) -> dict:
        """Initialize custom templates."""
        response = self._client.post(
            f"{self.base_url}/api/rules/init",
            params={"global_templates": global_templates, "force": force},
        )
        response.raise_for_status()
        return response.json()

    # ==================== Project MD ====================

    def projectmd_generate_stream(
        self,
        output: str = "PROJECT.md",
        save: bool = True,
        model: Optional[str] = None,
    ) -> Iterator[str]:
        """Generate PROJECT.md with SSE streaming.

        Args:
            output: Output file path
            save: Whether to save to file
            model: Model to use

        Yields:
            SSE lines from the response
        """
        payload = {"output": output, "save": save}
        if model:
            payload["model"] = model

        with self._client.stream(
            "POST",
            f"{self.base_url}/api/projectmd/generate",
            json=payload,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                yield line

    # ==================== Spec & Tasks ====================

    def spec_generate_stream(
        self,
        feature: str,
        model: Optional[str] = None,
        save: bool = False,
    ) -> Iterator[str]:
        """Generate feature specification with SSE streaming."""
        payload = {"feature": feature, "save": save}
        if model:
            payload["model"] = model

        with self._client.stream(
            "POST",
            f"{self.base_url}/api/spec/generate",
            json=payload,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                yield line

    def tasks_generate_stream(
        self,
        spec_name: Optional[str] = None,
        model: Optional[str] = None,
        save: bool = False,
    ) -> Iterator[str]:
        """Generate implementation tasks with SSE streaming."""
        payload = {"save": save}
        if spec_name:
            payload["spec_name"] = spec_name
        if model:
            payload["model"] = model

        with self._client.stream(
            "POST",
            f"{self.base_url}/api/tasks/generate",
            json=payload,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                yield line

    def plan_context(self, description: str, similar_prs: int = 5) -> dict:
        """Get planning context for a feature."""
        response = self._client.post(
            f"{self.base_url}/api/plan/context",
            json={"description": description, "similar_prs": similar_prs},
        )
        response.raise_for_status()
        return response.json()

    # ==================== Research ====================

    def research_stream(
        self,
        goal: str,
        max_iterations: int = _get_max_iterations(),
        budget: int = 50,
        model: Optional[str] = None,
    ) -> Iterator[str]:
        """Deep research with SSE streaming."""
        payload = {
            "goal": goal,
            "max_iterations": max_iterations,
            "budget": budget,
        }
        if model:
            payload["model"] = model

        with self._client.stream(
            "POST",
            f"{self.base_url}/api/research/run",
            json=payload,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                yield line

    # ==================== Team ====================

    def team_focus(
        self,
        days: int = 14,
        model: Optional[str] = None,
    ) -> dict:
        """Get team's recent focus analysis."""
        payload = {"days": days}
        if model:
            payload["model"] = model

        response = self._client.post(
            f"{self.base_url}/api/team/focus",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    # ==================== Messages ====================

    def get_session_messages(self, session_id: str, limit: int = 100) -> dict:
        """Get the current messages for a session.

        Args:
            session_id: Session ID
            limit: Maximum number of messages to return

        Returns:
            Dict with messages list
        """
        response = self._client.get(
            f"{self.base_url}/api/agent/chat/{session_id}/export",
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json()

    # ==================== Todos ====================

    def get_todos(self, session_id: str) -> dict:
        """Get the current todo list for a session.

        Args:
            session_id: Session ID

        Returns:
            Dict with todos list and summary
        """
        response = self._client.get(
            f"{self.base_url}/api/agent/chat/{session_id}/todos"
        )
        response.raise_for_status()
        return response.json()

    def add_todo(self, session_id: str, title: str, description: str = "") -> dict:
        """Add a new todo item to the agent's task list.

        Args:
            session_id: Session ID
            title: Todo title
            description: Optional description

        Returns:
            Dict with created task info
        """
        response = self._client.post(
            f"{self.base_url}/api/agent/chat/{session_id}/todos",
            params={"title": title, "description": description},
        )
        response.raise_for_status()
        return response.json()

    # ==================== Stats ====================

    def get_user_stats(self) -> dict:
        """Get aggregated user statistics.

        Returns:
            Dict with total_sessions, total_tokens, input/output/thinking tokens,
            first_seen, last_active, and model_usage breakdown
        """
        response = self._client.get(f"{self.base_url}/api/stats")
        response.raise_for_status()
        return response.json()

    def get_session_stats(self, limit: int = 20, offset: int = 0) -> dict:
        """Get list of sessions with metadata.

        Args:
            limit: Maximum number of sessions to return
            offset: Pagination offset

        Returns:
            Dict with sessions list and total count
        """
        response = self._client.get(
            f"{self.base_url}/api/stats/sessions",
            params={"limit": limit, "offset": offset},
        )
        response.raise_for_status()
        return response.json()

    def get_token_breakdown(self) -> dict:
        """Get detailed token usage breakdown.

        Returns:
            Dict with total, input, output, and thinking token counts
        """
        response = self._client.get(f"{self.base_url}/api/stats/tokens")
        response.raise_for_status()
        return response.json()

    def get_session_stats_realtime(self, session_id: str) -> dict:
        """Get real-time token usage and cost for a session.

        Args:
            session_id: Session ID to get stats for

        Returns:
            Dict with input_tokens, output_tokens, thinking_tokens,
            total_tokens, estimated_cost, cost_formatted, model
        """
        response = self._client.get(
            f"{self.base_url}/api/agent/chat/{session_id}/stats"
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "EmdashClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

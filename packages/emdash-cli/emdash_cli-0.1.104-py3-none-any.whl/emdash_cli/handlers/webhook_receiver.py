"""Local HTTP server that receives webhook events from core.

Core's WebhookRegistry fires POST requests to registered consumer URLs.
This receiver listens on a local port and routes events to the
FirebaseWebhookHandler for persistence.

Architecture:
    Core Server (FastAPI)
        ↓ POST /hooks  { event, data, timestamp }
    WebhookReceiver (this file, aiohttp)
        ↓ dispatches
    FirebaseWebhookHandler
        ↓ writes
    Firebase Realtime DB
"""

import asyncio
import logging
import socket
from typing import Any, Callable, Awaitable, Optional

from aiohttp import web

log = logging.getLogger(__name__)

# Type for the handler callback
WebhookHandlerFn = Callable[[str, dict[str, Any]], Awaitable[None]]


class WebhookReceiver:
    """Local HTTP server that receives webhook POSTs from core.

    Usage:
        async def handle(event_name, payload):
            print(f"Got {event_name}")

        receiver = WebhookReceiver(handler=handle)
        port = await receiver.start()  # picks a free port
        print(f"Listening on http://localhost:{port}/hooks")
        # ... later
        await receiver.stop()
    """

    def __init__(self, handler: WebhookHandlerFn, host: str = "127.0.0.1"):
        self._handler = handler
        self._host = host
        self._port: Optional[int] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None

    @property
    def port(self) -> Optional[int]:
        return self._port

    @property
    def url(self) -> Optional[str]:
        if self._port:
            return f"http://{self._host}:{self._port}/hooks"
        return None

    async def start(self, port: int = 0) -> int:
        """Start the webhook receiver server.

        Args:
            port: Port to listen on. 0 = auto-pick a free port.

        Returns:
            The actual port the server is listening on.
        """
        app = web.Application()
        app.router.add_post("/hooks", self._on_webhook)
        app.router.add_get("/health", self._on_health)

        self._runner = web.AppRunner(app)
        await self._runner.setup()

        if port == 0:
            port = _find_free_port()

        self._site = web.TCPSite(self._runner, self._host, port)
        await self._site.start()
        self._port = port

        log.info(f"Webhook receiver listening on {self.url}")
        return port

    async def stop(self) -> None:
        """Stop the webhook receiver server."""
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
            self._site = None
        self._port = None
        log.info("Webhook receiver stopped")

    async def _on_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming webhook POST from core."""
        try:
            payload = await request.json()
        except Exception:
            return web.json_response(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )

        event_name = payload.get("event", "unknown")
        event_id = payload.get("event_id", "?")

        log.debug(f"Received webhook: {event_name} (id={event_id})")

        try:
            await self._handler(event_name, payload)
            return web.json_response({"status": "ok"})
        except Exception as e:
            log.error(f"Webhook handler error for {event_name}: {e}")
            return web.json_response(
                {"status": "error", "message": str(e)}, status=500
            )

    async def _on_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({"status": "ok", "port": self._port})


def _find_free_port() -> int:
    """Find an available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

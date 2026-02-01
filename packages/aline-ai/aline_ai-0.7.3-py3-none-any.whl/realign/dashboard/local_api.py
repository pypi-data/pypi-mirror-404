"""Local HTTP API server for one-click agent import from browser."""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from ..logging_config import setup_logger

logger = setup_logger("realign.dashboard.local_api", "local_api.log")

ALLOWED_ORIGINS = [
    "https://realign-server.vercel.app",
    "http://localhost:3000",
]


class LocalAPIHandler(BaseHTTPRequestHandler):
    """Handle local API requests from the browser."""

    def _set_cors_headers(self) -> bool:
        """Set CORS headers. Returns True if origin is allowed."""
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            return True
        return False

    def _send_json(self, status: int, data: dict) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight."""
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/api/import-agent":
            self._handle_import_agent()
        else:
            self._send_json(404, {"error": "not found"})

    def _handle_import_agent(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except (json.JSONDecodeError, ValueError):
            self._send_json(400, {"error": "invalid JSON body"})
            return

        share_url = body.get("share_url")
        if not share_url:
            self._send_json(400, {"error": "share_url is required"})
            return

        password = body.get("password")

        logger.info(f"Import agent request: {share_url}")

        try:
            from ..commands.import_shares import import_agent_from_share

            result = import_agent_from_share(share_url, password=password)
            if result.get("success"):
                logger.info(
                    f"Agent imported: {result.get('agent_name')} "
                    f"({result.get('sessions_imported')} sessions)"
                )
                self._send_json(200, result)
            else:
                logger.warning(f"Import failed: {result.get('error')}")
                self._send_json(422, result)
        except Exception as e:
            logger.error(f"Import agent error: {e}", exc_info=True)
            self._send_json(500, {"success": False, "error": str(e)})

    def log_message(self, format: str, *args) -> None:
        """Suppress default stderr logging; use our logger instead."""
        logger.debug(f"HTTP {args[0] if args else ''}")


class LocalAPIServer:
    """Manages the local HTTP API server in a daemon thread."""

    def __init__(self, port: int = 17280):
        self.port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        """Start the server. Returns True on success."""
        try:
            self._server = HTTPServer(("127.0.0.1", self.port), LocalAPIHandler)
            self._thread = threading.Thread(
                target=self._server.serve_forever, daemon=True
            )
            self._thread.start()
            logger.info(f"Local API server started on http://127.0.0.1:{self.port}")
            return True
        except OSError as e:
            logger.warning(f"Failed to start local API server on port {self.port}: {e}")
            return False

    def stop(self) -> None:
        """Stop the server."""
        if self._server:
            self._server.shutdown()
            self._server = None
            self._thread = None
            logger.info("Local API server stopped")

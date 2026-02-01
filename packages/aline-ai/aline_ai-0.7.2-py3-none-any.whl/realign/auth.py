#!/usr/bin/env python3
"""
Authentication module for Aline CLI.

Handles Supabase authentication via web login flow:
1. User runs `aline login`
2. CLI starts a local HTTP server and opens browser to web login page
3. User logs in on web
4. Web redirects to local server with CLI token
5. CLI validates token and stores credentials automatically

Credentials are stored in ~/.aline/auth.yaml with 0600 permissions.
"""

import os
import sys
import socket
import threading
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .logging_config import setup_logger
from .config import ReAlignConfig

logger = setup_logger("realign.auth", "auth.log")

# Hardcoded Supabase/backend configuration
DEFAULT_AUTH_URL = "https://realign-server.vercel.app"
CLI_LOGIN_PATH = "/cli-login"
CLI_LOGOUT_PATH = "/cli-logout"
CLI_VALIDATE_PATH = "/api/auth/cli/validate"
CLI_REFRESH_PATH = "/api/auth/cli/refresh"

# Token refresh buffer (refresh 5 minutes before expiry)
REFRESH_BUFFER_SECONDS = 300


@dataclass
class AuthCredentials:
    """Stored authentication credentials."""
    access_token: str
    refresh_token: str
    expires_at: datetime
    user_id: str
    email: str
    provider: str  # email, github, google

    def is_expired(self) -> bool:
        """Check if access token is expired or will expire soon."""
        now = datetime.now(timezone.utc)
        buffer = REFRESH_BUFFER_SECONDS
        return (self.expires_at - now).total_seconds() < buffer

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat(),
            "user_id": self.user_id,
            "email": self.email,
            "provider": self.provider,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuthCredentials":
        """Create from dictionary (YAML load)."""
        expires_at = data.get("expires_at", "")
        if isinstance(expires_at, str):
            # Parse ISO format datetime
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        elif isinstance(expires_at, datetime):
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            expires_at=expires_at,
            user_id=data.get("user_id", ""),
            email=data.get("email", ""),
            provider=data.get("provider", ""),
        )


def get_auth_file_path() -> Path:
    """Get path to auth credentials file."""
    return Path.home() / ".aline" / "auth.yaml"


def load_credentials() -> Optional[AuthCredentials]:
    """
    Load stored credentials from ~/.aline/auth.yaml.

    Returns:
        AuthCredentials if found and valid, None otherwise
    """
    if not YAML_AVAILABLE:
        logger.warning("PyYAML not available, cannot load credentials")
        return None

    auth_file = get_auth_file_path()
    if not auth_file.exists():
        return None

    try:
        with open(auth_file, "r") as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        return AuthCredentials.from_dict(data)

    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        return None


def save_credentials(credentials: AuthCredentials) -> bool:
    """
    Save credentials to ~/.aline/auth.yaml with secure permissions.

    Args:
        credentials: AuthCredentials to save

    Returns:
        True if saved successfully, False otherwise
    """
    if not YAML_AVAILABLE:
        logger.error("PyYAML not available, cannot save credentials")
        return False

    auth_file = get_auth_file_path()

    try:
        # Ensure directory exists
        auth_file.parent.mkdir(parents=True, exist_ok=True)

        # Write credentials
        with open(auth_file, "w") as f:
            yaml.dump(credentials.to_dict(), f, default_flow_style=False)

        # Set secure permissions (owner read/write only)
        os.chmod(auth_file, 0o600)

        logger.info(f"Saved credentials for {credentials.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to save credentials: {e}")
        return False


def clear_credentials() -> bool:
    """
    Clear stored credentials (logout).

    Returns:
        True if cleared successfully, False otherwise
    """
    auth_file = get_auth_file_path()

    try:
        if auth_file.exists():
            auth_file.unlink()
            logger.info("Cleared credentials")
        return True

    except Exception as e:
        logger.error(f"Failed to clear credentials: {e}")
        return False


def is_logged_in() -> bool:
    """
    Check if user is logged in with valid credentials.

    This checks both:
    1. Credentials exist
    2. Either access_token is valid OR refresh_token can refresh it

    Returns:
        True if logged in, False otherwise
    """
    credentials = load_credentials()
    if not credentials:
        return False

    # If access token is not expired, we're good
    if not credentials.is_expired():
        return True

    # If expired, check if we can refresh
    if credentials.refresh_token:
        return True  # Can attempt refresh

    return False


def get_current_user() -> Optional[AuthCredentials]:
    """
    Get current user credentials, refreshing if needed.

    Returns:
        AuthCredentials if logged in (with refreshed token if needed), None otherwise
    """
    credentials = load_credentials()
    if not credentials:
        return None

    # If access token is expired, try to refresh
    if credentials.is_expired():
        refreshed = refresh_token(credentials)
        if refreshed:
            return refreshed
        else:
            # Refresh failed, credentials invalid
            return None

    return credentials


def get_access_token() -> Optional[str]:
    """
    Get current access token, refreshing if needed.

    This is the main function to call before making authenticated requests.

    Returns:
        Access token string if logged in, None otherwise
    """
    credentials = get_current_user()
    if credentials:
        return credentials.access_token
    return None


def refresh_token(credentials: AuthCredentials) -> Optional[AuthCredentials]:
    """
    Refresh access token using refresh token.

    Args:
        credentials: Current credentials with refresh_token

    Returns:
        New AuthCredentials if refresh succeeded, None otherwise
    """
    if not HTTPX_AVAILABLE:
        logger.error("httpx not available for token refresh")
        return None

    if not credentials.refresh_token:
        logger.warning("No refresh token available")
        return None

    config = ReAlignConfig.load()
    backend_url = config.share_backend_url or DEFAULT_AUTH_URL

    try:
        response = httpx.post(
            f"{backend_url}{CLI_REFRESH_PATH}",
            json={"refresh_token": credentials.refresh_token},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            logger.error(f"Token refresh failed: {data.get('error')}")
            return None

        # Create new credentials with refreshed tokens
        new_credentials = AuthCredentials(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", credentials.refresh_token),
            expires_at=datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")),
            user_id=credentials.user_id,
            email=credentials.email,
            provider=credentials.provider,
        )

        # Save refreshed credentials
        save_credentials(new_credentials)
        logger.info("Token refreshed successfully")

        return new_credentials

    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        return None


def validate_cli_token(cli_token: str) -> Optional[AuthCredentials]:
    """
    Validate a one-time CLI token and exchange for credentials.

    Args:
        cli_token: One-time token from web login page

    Returns:
        AuthCredentials if valid, None otherwise
    """
    if not HTTPX_AVAILABLE:
        logger.error("httpx not available for token validation")
        return None

    config = ReAlignConfig.load()
    backend_url = config.share_backend_url or DEFAULT_AUTH_URL

    try:
        response = httpx.post(
            f"{backend_url}{CLI_VALIDATE_PATH}",
            json={"cli_token": cli_token},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            logger.error(f"Token validation failed: {data.get('error')}")
            return None

        # Create credentials from response
        credentials = AuthCredentials(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")),
            user_id=data["user_id"],
            email=data["email"],
            provider=data.get("provider", "unknown"),
        )

        logger.info(f"Token validated for user: {credentials.email}")
        return credentials

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            try:
                error_data = e.response.json()
                logger.error(f"Token validation failed: {error_data.get('error')}")
            except Exception:
                logger.error(f"Token validation failed: {e}")
        else:
            logger.error(f"Token validation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return None


def open_login_page(callback_port: Optional[int] = None) -> str:
    """
    Open the web login page in browser.

    Args:
        callback_port: If provided, include callback URL for automatic token receipt

    Returns:
        The URL that was opened
    """
    config = ReAlignConfig.load()
    backend_url = config.share_backend_url or DEFAULT_AUTH_URL

    if callback_port:
        # Include callback URL for automatic flow
        callback_url = f"http://localhost:{callback_port}/callback"
        login_url = f"{backend_url}{CLI_LOGIN_PATH}?callback={callback_url}"
    else:
        login_url = f"{backend_url}{CLI_LOGIN_PATH}"

    try:
        webbrowser.open(login_url)
        logger.info(f"Opened login page: {login_url}")
    except Exception as e:
        logger.warning(f"Failed to open browser: {e}")

    return login_url


def open_logout_page() -> str:
    """
    Open the web logout page in browser to sign out from web session.

    Returns:
        The URL that was opened
    """
    config = ReAlignConfig.load()
    backend_url = config.share_backend_url or DEFAULT_AUTH_URL
    logout_url = f"{backend_url}{CLI_LOGOUT_PATH}"

    try:
        webbrowser.open(logout_url)
        logger.info(f"Opened logout page: {logout_url}")
    except Exception as e:
        logger.warning(f"Failed to open browser: {e}")

    return logout_url


# Local callback server for automatic token receipt
_received_token: Optional[str] = None
_server_error: Optional[str] = None


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for receiving CLI token callback."""

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_GET(self):
        global _received_token, _server_error

        parsed = urlparse(self.path)

        if parsed.path == "/callback":
            params = parse_qs(parsed.query)

            if "token" in params:
                _received_token = params["token"][0]
                self._send_success_page()
            elif "error" in params:
                _server_error = params.get("error", ["Unknown error"])[0]
                self._send_error_page(_server_error)
            else:
                _server_error = "No token received"
                self._send_error_page(_server_error)
        else:
            self.send_response(404)
            self.end_headers()

    def _send_success_page(self):
        """Send success HTML page."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Aline CLI Login</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       display: flex; justify-content: center; align-items: center;
                       min-height: 100vh; margin: 0; background: #f5f5f5; }
                .container { text-align: center; padding: 40px; background: white;
                            border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .success { color: #22c55e; font-size: 48px; margin-bottom: 20px; }
                h1 { color: #333; margin-bottom: 10px; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">&#10003;</div>
                <h1>Login Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def _send_error_page(self, error: str):
        """Send error HTML page."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Aline CLI Login - Error</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       display: flex; justify-content: center; align-items: center;
                       min-height: 100vh; margin: 0; background: #f5f5f5; }}
                .container {{ text-align: center; padding: 40px; background: white;
                            border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .error {{ color: #ef4444; font-size: 48px; margin-bottom: 20px; }}
                h1 {{ color: #333; margin-bottom: 10px; }}
                p {{ color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">&#10007;</div>
                <h1>Login Failed</h1>
                <p>{error}</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())


def find_free_port() -> int:
    """Find a free port for the local callback server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def start_callback_server(port: int, timeout: int = 300) -> Tuple[Optional[str], Optional[str]]:
    """
    Start a local HTTP server to receive the CLI token callback.

    Args:
        port: Port to listen on
        timeout: Maximum time to wait for callback (seconds)

    Returns:
        Tuple of (token, error) - one will be None
    """
    global _received_token, _server_error
    _received_token = None
    _server_error = None

    server = HTTPServer(('localhost', port), CallbackHandler)
    server.timeout = timeout

    # Handle one request (the callback)
    server.handle_request()
    server.server_close()

    return _received_token, _server_error


def get_auth_headers() -> dict:
    """
    Get HTTP headers for authenticated requests.

    Returns:
        Dict with Authorization header if logged in, empty dict otherwise
    """
    token = get_access_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

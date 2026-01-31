#!/usr/bin/env python3
"""
Authentication commands for Aline CLI.

Commands:
- aline login   - Login via web browser
- aline logout  - Clear local credentials
- aline whoami  - Show current login status
"""

import sys
from typing import Optional

try:
    from rich.console import Console
    from rich.prompt import Prompt
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ..auth import (
    is_logged_in,
    get_current_user,
    load_credentials,
    save_credentials,
    clear_credentials,
    open_login_page,
    open_logout_page,
    validate_cli_token,
    find_free_port,
    start_callback_server,
    HTTPX_AVAILABLE,
)
from ..config import ReAlignConfig
from ..logging_config import setup_logger

logger = setup_logger("realign.commands.auth", "auth.log")

if RICH_AVAILABLE:
    console = Console()
else:
    console = None


def login_command() -> int:
    """
    Login to Aline via web browser.

    Opens the web login page with automatic callback - no manual token copy needed.

    Returns:
        0 on success, 1 on error
    """
    # Check dependencies
    if not HTTPX_AVAILABLE:
        print("Error: httpx package not installed", file=sys.stderr)
        print("Install it with: pip install httpx", file=sys.stderr)
        return 1

    # Check if already logged in
    credentials = load_credentials()
    if credentials and is_logged_in():
        if console:
            console.print(f"[yellow]Already logged in as {credentials.email}[/yellow]")
            console.print("Run 'aline logout' first if you want to switch accounts.")
        else:
            print(f"Already logged in as {credentials.email}")
            print("Run 'aline logout' first if you want to switch accounts.")
        return 0

    # Start local callback server
    port = find_free_port()

    if console:
        console.print("[cyan]Opening browser for login...[/cyan]")
        console.print("[dim]Waiting for authentication...[/dim]\n")
    else:
        print("Opening browser for login...")
        print("Waiting for authentication...\n")

    # Open browser with callback URL
    login_url = open_login_page(callback_port=port)

    if console:
        console.print(f"[dim]If browser doesn't open, visit:[/dim]")
        console.print(f"[link={login_url}]{login_url}[/link]\n")
    else:
        print(f"If browser doesn't open, visit:")
        print(f"{login_url}\n")

    # Wait for callback with token
    cli_token, error = start_callback_server(port, timeout=300)

    if error:
        if console:
            console.print(f"[red]Error: {error}[/red]")
        else:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    if not cli_token:
        if console:
            console.print("[red]Error: No token received[/red]")
            console.print("Please try again with 'aline login'")
        else:
            print("Error: No token received", file=sys.stderr)
            print("Please try again with 'aline login'")
        return 1

    # Validate token
    if console:
        console.print("[cyan]Validating token...[/cyan]")
    else:
        print("Validating token...")

    credentials = validate_cli_token(cli_token)

    if not credentials:
        if console:
            console.print("[red]Error: Invalid or expired token[/red]")
            console.print("Please try again with 'aline login'")
        else:
            print("Error: Invalid or expired token", file=sys.stderr)
            print("Please try again with 'aline login'")
        return 1

    # Save credentials
    if not save_credentials(credentials):
        if console:
            console.print("[red]Error: Failed to save credentials[/red]")
        else:
            print("Error: Failed to save credentials", file=sys.stderr)
        return 1

    # Sync Supabase uid to local config
    # This ensures all new Events/Sessions/Turns use the same uid as shares
    try:
        config = ReAlignConfig.load()
        old_uid = config.uid
        config.uid = credentials.user_id
        # Use email as user_name if not already set
        if not config.user_name:
            config.user_name = credentials.email.split("@")[0]  # Use email prefix as username
        config.save()
        logger.info(f"Synced Supabase uid to config: {credentials.user_id[:8]}... (was: {old_uid[:8] if old_uid else 'not set'}...)")

        # V18: Upsert user info to users table
        try:
            from ..db import get_database
            db = get_database()
            db.upsert_user(config.uid, config.user_name)
        except Exception as e:
            logger.debug(f"Failed to upsert user to users table: {e}")
    except Exception as e:
        # Non-fatal: continue even if config sync fails
        logger.warning(f"Failed to sync uid to config: {e}")

    # Success
    if console:
        console.print(f"\n[green]Login successful![/green]")
        console.print(f"Logged in as: [bold]{credentials.email}[/bold]")
        if credentials.provider and credentials.provider != "email":
            console.print(f"Provider: {credentials.provider}")
        console.print(f"[dim]User ID synced to local config[/dim]")
    else:
        print(f"\nLogin successful!")
        print(f"Logged in as: {credentials.email}")
        if credentials.provider and credentials.provider != "email":
            print(f"Provider: {credentials.provider}")
        print("User ID synced to local config")

    logger.info(f"Login successful for {credentials.email}")
    return 0


def logout_command() -> int:
    """
    Logout from Aline and clear local credentials.

    Also stops watcher and worker daemons since they require authentication.

    Returns:
        0 on success, 1 on error
    """
    credentials = load_credentials()

    if not credentials:
        if console:
            console.print("[yellow]Not currently logged in.[/yellow]")
        else:
            print("Not currently logged in.")
        return 0

    email = credentials.email

    # Stop watcher and worker daemons before logout
    if console:
        console.print("[dim]Stopping daemons...[/dim]")
    else:
        print("Stopping daemons...")

    _stop_daemons()

    if not clear_credentials():
        if console:
            console.print("[red]Error: Failed to clear credentials[/red]")
        else:
            print("Error: Failed to clear credentials", file=sys.stderr)
        return 1

    # Open browser to sign out from web session
    if console:
        console.print("[dim]Signing out from web session...[/dim]")
    else:
        print("Signing out from web session...")

    open_logout_page()

    if console:
        console.print(f"[green]Logged out successfully.[/green]")
        console.print(f"Cleared credentials for: {email}")
    else:
        print("Logged out successfully.")
        print(f"Cleared credentials for: {email}")

    logger.info(f"Logout successful for {email}")
    return 0


def _stop_daemons() -> None:
    """Stop watcher and worker daemons."""
    import os
    import signal
    import time
    from pathlib import Path

    def stop_daemon(name: str, pid_file: Path) -> None:
        """Stop a daemon by PID file, wait for it to terminate."""
        if not pid_file.exists():
            return

        try:
            pid = int(pid_file.read_text().strip())
        except Exception:
            return

        # Check if process is running
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            # Process already gone, clean up PID file
            try:
                pid_file.unlink(missing_ok=True)
            except Exception:
                pass
            return
        except PermissionError:
            pass  # Can't check, try to stop anyway

        # Send SIGTERM
        try:
            os.kill(pid, signal.SIGTERM)
            if console:
                console.print(f"  [dim]Stopping {name} daemon (PID {pid})...[/dim]")
            logger.info(f"Sent SIGTERM to {name} daemon (PID {pid})")
        except ProcessLookupError:
            try:
                pid_file.unlink(missing_ok=True)
            except Exception:
                pass
            return
        except Exception as e:
            logger.debug(f"Error sending SIGTERM to {name}: {e}")
            return

        # Wait for process to terminate (up to 5 seconds)
        for _ in range(50):  # 50 * 0.1s = 5 seconds
            time.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                # Process terminated
                if console:
                    console.print(f"  [dim]{name.capitalize()} daemon stopped[/dim]")
                logger.info(f"{name.capitalize()} daemon (PID {pid}) stopped")
                try:
                    pid_file.unlink(missing_ok=True)
                except Exception:
                    pass
                return
            except PermissionError:
                break  # Can't check anymore

        # Process still running, try SIGKILL
        try:
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)
            if console:
                console.print(f"  [dim]{name.capitalize()} daemon force killed[/dim]")
            logger.info(f"{name.capitalize()} daemon (PID {pid}) force killed")
        except ProcessLookupError:
            pass
        except Exception as e:
            logger.debug(f"Error sending SIGKILL to {name}: {e}")

        # Clean up PID file
        try:
            pid_file.unlink(missing_ok=True)
        except Exception:
            pass

    # Stop watcher daemon
    watcher_pid_file = Path.home() / ".aline" / ".logs" / "watcher.pid"
    stop_daemon("watcher", watcher_pid_file)

    # Stop worker daemon
    worker_pid_file = Path.home() / ".aline" / ".logs" / "worker.pid"
    stop_daemon("worker", worker_pid_file)


def whoami_command() -> int:
    """
    Display current login status.

    Returns:
        0 if logged in, 1 if not logged in
    """
    credentials = get_current_user()

    if not credentials:
        if console:
            console.print("[yellow]Not logged in.[/yellow]")
            console.print("Run 'aline login' to authenticate.")
        else:
            print("Not logged in.")
            print("Run 'aline login' to authenticate.")
        return 1

    if console:
        console.print(f"[green]Logged in as:[/green] [bold]{credentials.email}[/bold]")
        console.print(f"[dim]User ID:[/dim] {credentials.user_id}")
        if credentials.provider:
            console.print(f"[dim]Provider:[/dim] {credentials.provider}")
        console.print(f"[dim]Token expires:[/dim] {credentials.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    else:
        print(f"Logged in as: {credentials.email}")
        print(f"User ID: {credentials.user_id}")
        if credentials.provider:
            print(f"Provider: {credentials.provider}")
        print(f"Token expires: {credentials.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    return 0

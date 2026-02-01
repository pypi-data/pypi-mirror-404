"""Config Panel Widget for viewing and editing configuration."""

import threading

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, RadioButton, RadioSet, Static

from ..tmux_manager import _run_outer_tmux
from ...auth import (
    load_credentials,
    save_credentials,
    clear_credentials,
    open_login_page,
    get_current_user,
    find_free_port,
    start_callback_server,
    validate_cli_token,
)
from ...config import ReAlignConfig
from ...logging_config import setup_logger

logger = setup_logger("realign.dashboard.widgets.config_panel", "dashboard.log")


class ConfigPanel(Static):
    """Panel for viewing and editing Aline configuration."""

    DEFAULT_CSS = """
    ConfigPanel {
        height: 100%;
        padding: 1;
    }

    ConfigPanel .section-title {
        text-style: bold;
        margin-bottom: 1;
    }

    ConfigPanel .button-row {
        height: 3;
        margin-top: 1;
    }

    ConfigPanel .button-row Button {
        margin-right: 1;
    }

    ConfigPanel .account-section {
        height: 3;
        align: left middle;
    }

    ConfigPanel .account-section .account-label {
        width: auto;
        margin-right: 1;
    }

    ConfigPanel .account-section .account-email {
        width: auto;
        margin-right: 1;
    }

    ConfigPanel .tmux-settings {
        height: auto;
        margin-top: 2;
    }

    ConfigPanel .tmux-settings .setting-row {
        height: auto;
    }

    ConfigPanel .tmux-settings .setting-label {
        width: auto;
    }

    ConfigPanel .tmux-settings RadioSet {
        width: auto;
        height: auto;
        layout: horizontal;
    }

    ConfigPanel .tmux-settings RadioButton {
        width: auto;
        margin-right: 2;
    }

    ConfigPanel .tools-section {
        height: auto;
        margin-top: 2;
    }

    ConfigPanel .terminal-settings {
        height: auto;
        margin-top: 2;
    }

    ConfigPanel .terminal-settings .setting-row {
        height: auto;
    }

    ConfigPanel .terminal-settings .setting-label {
        width: auto;
    }

    ConfigPanel .terminal-settings RadioSet {
        width: auto;
        height: auto;
        layout: horizontal;
    }

    ConfigPanel .terminal-settings RadioButton {
        width: auto;
        margin-right: 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._border_resize_enabled: bool = True  # Track tmux border resize state
        self._syncing_radio: bool = False  # Flag to prevent recursive radio updates
        self._login_in_progress: bool = False  # Track login state
        self._refresh_timer = None  # Timer for auto-refresh
        self._auto_close_stale_enabled: bool = False  # Track auto-close setting

    def compose(self) -> ComposeResult:
        """Compose the config panel layout."""
        # Account section
        with Horizontal(classes="account-section"):
            yield Static("[bold]Account:[/bold]", classes="account-label")
            yield Static(id="account-email", classes="account-email")
            yield Button("Login", id="auth-btn", variant="primary")

        # Tmux settings section
        with Static(classes="tmux-settings"):
            yield Static("[bold]Tmux Settings[/bold]", classes="section-title")
            with Horizontal(classes="setting-row"):
                yield Static("Border resize:", classes="setting-label")
                with RadioSet(id="border-resize-radio"):
                    yield RadioButton("Enabled", id="border-resize-enabled", value=True)
                    yield RadioButton("Disabled", id="border-resize-disabled")

        # Terminal settings section
        with Static(classes="terminal-settings"):
            yield Static("[bold]Terminal Settings[/bold]", classes="section-title")
            with Horizontal(classes="setting-row"):
                yield Static("Auto-close stale terminals (24h):", classes="setting-label")
                with RadioSet(id="auto-close-stale-radio"):
                    yield RadioButton("Enabled", id="auto-close-stale-enabled")
                    yield RadioButton("Disabled", id="auto-close-stale-disabled", value=True)

        # Tools section
        with Static(classes="tools-section"):
            yield Static("[bold]Tools[/bold]", classes="section-title")
            with Horizontal(classes="button-row"):
                yield Button("Aline Doctor", id="doctor-btn", variant="default")

    def on_mount(self) -> None:
        """Set up the panel on mount."""
        # Update account status display
        self._update_account_status()

        # Query and set the actual tmux border resize state
        self._sync_border_resize_radio()

        # Sync auto-close stale terminals setting from config
        self._sync_auto_close_stale_radio()

        # Start timer to periodically refresh account status (every 5 seconds)
        self._refresh_timer = self.set_interval(5.0, self._update_account_status)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "auth-btn":
            credentials = get_current_user()
            if credentials:
                self._handle_logout()
            else:
                self._handle_login()
        elif event.button.id == "doctor-btn":
            self._handle_doctor()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle radio set change events."""
        if self._syncing_radio:
            return  # Ignore events during sync
        if event.radio_set.id == "border-resize-radio":
            # Check which radio button is selected
            enabled = event.pressed.id == "border-resize-enabled"
            self._toggle_border_resize(enabled)
        elif event.radio_set.id == "auto-close-stale-radio":
            enabled = event.pressed.id == "auto-close-stale-enabled"
            self._toggle_auto_close_stale(enabled)

    def _update_account_status(self) -> None:
        """Update the account status display."""
        try:
            email_widget = self.query_one("#account-email", Static)
            auth_btn = self.query_one("#auth-btn", Button)
        except Exception:
            # Widget not ready yet
            return

        # Don't update if login is in progress
        if self._login_in_progress:
            return

        credentials = get_current_user()
        if credentials:
            email_widget.update(f"[bold]{credentials.email}[/bold]")
            auth_btn.label = "Logout"
            auth_btn.variant = "warning"
        else:
            email_widget.update("[dim]Not logged in[/dim]")
            auth_btn.label = "Login"
            auth_btn.variant = "primary"
        auth_btn.disabled = False

    def _handle_login(self) -> None:
        """Handle login button click - start login flow in background."""
        if self._login_in_progress:
            self.app.notify("Login already in progress...", title="Login")
            return

        self._login_in_progress = True

        # Update UI to show login in progress
        auth_btn = self.query_one("#auth-btn", Button)
        auth_btn.disabled = True
        email_widget = self.query_one("#account-email", Static)
        email_widget.update("[cyan]Opening browser...[/cyan]")

        # Start login flow in background thread
        def do_login():
            try:
                port = find_free_port()
                open_login_page(callback_port=port)

                # Wait for callback (up to 5 minutes)
                cli_token, error = start_callback_server(port, timeout=300)

                if error:
                    self.app.call_from_thread(
                        self.app.notify, f"Login failed: {error}", title="Login", severity="error"
                    )
                    self.app.call_from_thread(self._update_account_status)
                    return

                if not cli_token:
                    self.app.call_from_thread(
                        self.app.notify, "No token received", title="Login", severity="error"
                    )
                    self.app.call_from_thread(self._update_account_status)
                    return

                # Validate token
                credentials = validate_cli_token(cli_token)
                if not credentials:
                    self.app.call_from_thread(
                        self.app.notify, "Invalid token", title="Login", severity="error"
                    )
                    self.app.call_from_thread(self._update_account_status)
                    return

                # Save credentials
                if save_credentials(credentials):
                    # Sync Supabase uid to local config
                    try:
                        config = ReAlignConfig.load()
                        old_uid = config.uid
                        config.uid = credentials.user_id
                        if not config.user_name:
                            config.user_name = credentials.email.split("@")[0]
                        config.save()
                        logger.info(f"Synced Supabase uid to config: {credentials.user_id[:8]}...")

                        # V18: Upsert user info to users table
                        try:
                            from ...db import get_database
                            db = get_database()
                            db.upsert_user(config.uid, config.user_name)
                        except Exception as e:
                            logger.debug(f"Failed to upsert user to users table: {e}")
                    except Exception as e:
                        logger.warning(f"Failed to sync uid to config: {e}")

                    self.app.call_from_thread(
                        self.app.notify, f"Logged in as {credentials.email}", title="Login"
                    )
                else:
                    self.app.call_from_thread(
                        self.app.notify, "Failed to save credentials", title="Login", severity="error"
                    )

                self.app.call_from_thread(self._update_account_status)

            finally:
                self._login_in_progress = False

        thread = threading.Thread(target=do_login, daemon=True)
        thread.start()

        self.app.notify("Complete login in browser...", title="Login")

    def _handle_logout(self) -> None:
        """Handle logout button click - clear credentials."""
        credentials = load_credentials()
        email = credentials.email if credentials else "user"

        if clear_credentials():
            self._update_account_status()
            self.app.notify(f"Logged out: {email}", title="Account")
        else:
            self.app.notify("Failed to logout", title="Account", severity="error")

    def _sync_border_resize_radio(self) -> None:
        """Query tmux state and sync the radio buttons to match."""
        try:
            # Check if MouseDrag1Border is bound by listing keys
            result = _run_outer_tmux(["list-keys", "-T", "root"], capture=True)
            output = result.stdout or ""

            # If MouseDrag1Border is in the output, resize is enabled
            is_enabled = "MouseDrag1Border" in output
            self._border_resize_enabled = is_enabled

            # Update radio buttons without triggering the toggle action
            self._syncing_radio = True
            try:
                if is_enabled:
                    radio = self.query_one("#border-resize-enabled", RadioButton)
                else:
                    radio = self.query_one("#border-resize-disabled", RadioButton)
                radio.value = True
            finally:
                self._syncing_radio = False
        except Exception:
            # If we can't query, assume enabled (default tmux behavior)
            pass

    def _toggle_border_resize(self, enabled: bool) -> None:
        """Enable or disable tmux border resize functionality."""
        try:
            if enabled:
                # Re-enable border resize by binding MouseDrag1Border to default resize behavior
                _run_outer_tmux([
                    "bind", "-n", "MouseDrag1Border", "resize-pane", "-M"
                ])
                self._border_resize_enabled = True
                self.app.notify("Border resize enabled", title="Tmux")
            else:
                # Disable border resize by unbinding MouseDrag1Border
                _run_outer_tmux([
                    "unbind", "-n", "MouseDrag1Border"
                ])
                self._border_resize_enabled = False
                self.app.notify("Border resize disabled", title="Tmux")
        except Exception as e:
            self.app.notify(f"Error toggling border resize: {e}", title="Tmux", severity="error")

    def _sync_auto_close_stale_radio(self) -> None:
        """Sync radio buttons with config file setting."""
        try:
            config = ReAlignConfig.load()
            is_enabled = config.auto_close_stale_terminals
            self._auto_close_stale_enabled = is_enabled

            # Update radio buttons without triggering the toggle action
            self._syncing_radio = True
            try:
                if is_enabled:
                    radio = self.query_one("#auto-close-stale-enabled", RadioButton)
                else:
                    radio = self.query_one("#auto-close-stale-disabled", RadioButton)
                radio.value = True
            finally:
                self._syncing_radio = False
        except Exception:
            pass

    def _toggle_auto_close_stale(self, enabled: bool) -> None:
        """Enable or disable auto-close stale terminals setting."""
        try:
            config = ReAlignConfig.load()
            config.auto_close_stale_terminals = enabled
            config.save()
            self._auto_close_stale_enabled = enabled
            if enabled:
                self.app.notify("Auto-close stale terminals enabled", title="Terminal")
            else:
                self.app.notify("Auto-close stale terminals disabled", title="Terminal")
        except Exception as e:
            self.app.notify(f"Error saving setting: {e}", title="Config", severity="error")

    def _handle_doctor(self) -> None:
        """Run aline doctor directly in background thread."""
        self.app.notify("Running Aline Doctor...", title="Doctor")

        def do_doctor():
            try:
                import contextlib
                import io
                from ...commands.doctor import run_doctor

                # Suppress Rich console output (would corrupt TUI)
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    exit_code = run_doctor(
                        restart_daemons=True,
                        start_if_not_running=False,
                        verbose=False,
                        clear_cache=True,
                        auto_fix=True,
                    )

                if exit_code == 0:
                    self.app.call_from_thread(
                        self.app.notify, "Doctor completed successfully", title="Doctor"
                    )
                else:
                    self.app.call_from_thread(
                        self.app.notify, "Doctor completed with errors", title="Doctor", severity="error"
                    )
            except Exception as e:
                self.app.call_from_thread(
                    self.app.notify, f"Doctor error: {e}", title="Doctor", severity="error"
                )

        thread = threading.Thread(target=do_doctor, daemon=True)
        thread.start()

    def refresh_data(self) -> None:
        """Refresh account status (called by app refresh action)."""
        self._update_account_status()

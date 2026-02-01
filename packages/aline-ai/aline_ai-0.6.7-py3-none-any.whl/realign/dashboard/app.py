"""Aline Dashboard - Main Application."""

import os
import subprocess
import sys
import time
import traceback

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, TabbedContent, TabPane

from ..logging_config import setup_logger
from .widgets import (
    AlineHeader,
    WatcherPanel,
    WorkerPanel,
    ConfigPanel,
    AgentsPanel,
)

# Environment variable to control terminal mode
ENV_TERMINAL_MODE = "ALINE_TERMINAL_MODE"

# Set up dashboard logger - logs to ~/.aline/.logs/dashboard.log
logger = setup_logger("realign.dashboard", "dashboard.log")


def _detect_system_dark_mode() -> bool:
    """Detect if the system is in dark mode.

    On macOS, checks AppleInterfaceStyle via defaults command.
    Returns True for dark mode, False for light mode.
    """
    if sys.platform != "darwin":
        return True  # Default to dark on non-macOS

    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        return result.stdout.strip().lower() == "dark"
    except Exception:
        return True  # Default to dark on error


def _monotonic() -> float:
    """Small wrapper so tests can patch without affecting global time.monotonic()."""
    return time.monotonic()


class AlineDashboard(App):
    """Aline Interactive Dashboard - TUI for monitoring and managing Aline."""

    CSS_PATH = "styles/dashboard.tcss"
    TITLE = "Aline Dashboard"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=False),
        Binding("?", "help", "Help"),
        Binding("tab", "next_tab", "Next Tab", priority=True, show=False),
        Binding("shift+tab", "prev_tab", "Prev Tab", priority=True, show=False),
        Binding("n", "page_next", "Next Page", show=False),
        Binding("p", "page_prev", "Prev Page", show=False),
        Binding("s", "switch_view", "Switch View", show=False),
        Binding("ctrl+c", "quit_confirm", "Quit", priority=True),
    ]

    _quit_confirm_window_s: float = 1.2

    def __init__(self, dev_mode: bool = False, use_native_terminal: bool | None = None):
        """Initialize the dashboard.

        Args:
            dev_mode: If True, shows developer tabs (Watcher, Worker).
            use_native_terminal: If True, use native terminal backend (iTerm2/Kitty).
                                 If False, use tmux.
                                 If None (default), auto-detect from ALINE_TERMINAL_MODE env var.
        """
        super().__init__()
        self.dev_mode = dev_mode
        self.use_native_terminal = use_native_terminal
        self._native_terminal_mode = self._detect_native_mode()
        logger.info(
            f"AlineDashboard initialized (dev_mode={dev_mode}, "
            f"native_terminal={self._native_terminal_mode})"
        )

    def _detect_native_mode(self) -> bool:
        """Detect if native terminal mode should be used."""
        if self.use_native_terminal is not None:
            return self.use_native_terminal

        mode = os.environ.get(ENV_TERMINAL_MODE, "").strip().lower()
        return mode in {"native", "iterm2", "iterm", "kitty"}

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        logger.debug("compose() started")
        try:
            yield AlineHeader()
            tab_ids = self._tab_ids()
            with TabbedContent(initial=tab_ids[0] if tab_ids else "agents"):
                with TabPane("Agents", id="agents"):
                    yield AgentsPanel()
                if self.dev_mode:
                    with TabPane("Watcher", id="watcher"):
                        yield WatcherPanel()
                    with TabPane("Worker", id="worker"):
                        yield WorkerPanel()
                with TabPane("Config", id="config"):
                    yield ConfigPanel()
            yield Footer()
            logger.debug("compose() completed successfully")
        except Exception as e:
            logger.error(f"compose() failed: {e}\n{traceback.format_exc()}")
            raise

    def _tab_ids(self) -> list[str]:
        if self.dev_mode:
            return ["agents", "watcher", "worker", "config"]
        return ["agents", "config"]

    def on_mount(self) -> None:
        """Apply theme based on system settings and watch for changes."""
        logger.info("on_mount() started")
        try:
            self._sync_theme()
            # Check for system theme changes every 2 seconds
            self.set_interval(2, self._sync_theme)
            self._quit_confirm_deadline: float | None = None

            # Set up side-by-side layout for native terminal mode
            if self._native_terminal_mode:
                self._setup_native_terminal_layout()

            logger.info("on_mount() completed successfully")
        except Exception as e:
            logger.error(f"on_mount() failed: {e}\n{traceback.format_exc()}")
            raise

    def _setup_native_terminal_layout(self) -> None:
        """Set up side-by-side layout for Dashboard and native terminal."""
        # Skip if using iTerm2 split pane mode (already set up by CLI)
        if os.environ.get("ALINE_ITERM2_RIGHT_PANE"):
            logger.info("Using iTerm2 split pane mode, skipping window layout")
            return

        try:
            from .layout import setup_side_by_side_layout

            # Determine the target terminal app
            mode = os.environ.get(ENV_TERMINAL_MODE, "").strip().lower()
            if mode == "kitty":
                terminal_app = "Kitty"
            else:
                terminal_app = "iTerm2"

            # Set up side-by-side layout (Dashboard on left, terminal on right)
            success = setup_side_by_side_layout(
                terminal_app=terminal_app,
                dashboard_on_left=True,
                dashboard_width_percent=40,  # Dashboard takes 40%, terminal takes 60%
            )

            if success:
                logger.info(f"Set up side-by-side layout with {terminal_app}")
            else:
                logger.warning("Failed to set up side-by-side layout")
        except Exception as e:
            logger.warning(f"Could not set up native terminal layout: {e}")

    def _sync_theme(self) -> None:
        """Sync app theme with system theme."""
        target_theme = "textual-dark" if _detect_system_dark_mode() else "textual-light"
        if self.theme != target_theme:
            self.theme = target_theme

    def action_next_tab(self) -> None:
        """Switch to next tab."""
        tabbed_content = self.query_one(TabbedContent)
        tabs = self._tab_ids()
        current = tabbed_content.active
        if current in tabs:
            idx = tabs.index(current)
            next_idx = (idx + 1) % len(tabs)
            tabbed_content.active = tabs[next_idx]

    def action_prev_tab(self) -> None:
        """Switch to previous tab."""
        tabbed_content = self.query_one(TabbedContent)
        tabs = self._tab_ids()
        current = tabbed_content.active
        if current in tabs:
            idx = tabs.index(current)
            prev_idx = (idx - 1) % len(tabs)
            tabbed_content.active = tabs[prev_idx]

    async def action_refresh(self) -> None:
        """Refresh the current tab."""
        tabbed_content = self.query_one(TabbedContent)
        active_tab_id = tabbed_content.active

        if active_tab_id == "agents":
            self.query_one(AgentsPanel).refresh_data()
        elif active_tab_id == "watcher":
            self.query_one(WatcherPanel).refresh_data()
        elif active_tab_id == "worker":
            self.query_one(WorkerPanel).refresh_data()
        elif active_tab_id == "config":
            self.query_one(ConfigPanel).refresh_data()

    def action_page_next(self) -> None:
        """Go to next page in current panel."""
        tabbed_content = self.query_one(TabbedContent)
        active_tab_id = tabbed_content.active

        if active_tab_id == "watcher":
            self.query_one(WatcherPanel).action_next_page()
        elif active_tab_id == "worker":
            self.query_one(WorkerPanel).action_next_page()

    def action_page_prev(self) -> None:
        """Go to previous page in current panel."""
        tabbed_content = self.query_one(TabbedContent)
        active_tab_id = tabbed_content.active

        if active_tab_id == "watcher":
            self.query_one(WatcherPanel).action_prev_page()
        elif active_tab_id == "worker":
            self.query_one(WorkerPanel).action_prev_page()

    def action_switch_view(self) -> None:
        """Switch view in current panel (if supported)."""
        tabbed_content = self.query_one(TabbedContent)
        active_tab_id = tabbed_content.active

        if active_tab_id == "watcher":
            self.query_one(WatcherPanel).action_switch_view()
        elif active_tab_id == "worker":
            self.query_one(WorkerPanel).action_switch_view()

    def action_help(self) -> None:
        """Show help information."""
        from .screens import HelpScreen

        self.push_screen(HelpScreen())

    def action_quit_confirm(self) -> None:
        """Quit only when Ctrl+C is pressed twice quickly."""
        now = _monotonic()
        deadline = self._quit_confirm_deadline
        if deadline is not None and now <= deadline:
            self.exit()
            return

        self._quit_confirm_deadline = now + self._quit_confirm_window_s
        self.notify("Press Ctrl+C again to quit", title="Quit", timeout=2)

def run_dashboard(use_native_terminal: bool | None = None) -> None:
    """Run the Aline Dashboard.

    Args:
        use_native_terminal: If True, use native terminal backend (iTerm2/Kitty).
                             If False, use tmux.
                             If None (default), auto-detect from ALINE_TERMINAL_MODE env var.
    """
    logger.info("Starting Aline Dashboard")
    try:
        app = AlineDashboard(use_native_terminal=use_native_terminal)
        app.run()
        logger.info("Aline Dashboard exited normally")
    except Exception as e:
        logger.error(f"Dashboard crashed: {e}\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    run_dashboard()

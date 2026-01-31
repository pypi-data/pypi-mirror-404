"""Terminal controls panel with native terminal and tmux support.

This panel controls terminal tabs in either:
1. Native terminals (iTerm2/Kitty) - for better performance with high-frequency updates
2. tmux - the traditional approach with embedded terminal rendering

The mode is determined by the ALINE_TERMINAL_MODE environment variable:
- "native" or "iterm2" or "kitty": Use native terminal backend
- "tmux" or unset: Use tmux backend (default)
"""

from __future__ import annotations

import asyncio
import os
import re
import shlex
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Union

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Static
from rich.text import Text

from .. import tmux_manager
from ..terminal_backend import TerminalBackend, TerminalInfo
from ...logging_config import setup_logger

logger = setup_logger("realign.dashboard.terminal", "dashboard.log")


# Signal directory for permission request notifications
PERMISSION_SIGNAL_DIR = Path.home() / ".aline" / ".signals" / "permission_request"

# Environment variable to control terminal mode
ENV_TERMINAL_MODE = "ALINE_TERMINAL_MODE"

# Terminal mode constants
MODE_TMUX = "tmux"
MODE_NATIVE = "native"
MODE_ITERM2 = "iterm2"
MODE_KITTY = "kitty"


# Type for window data (either tmux InnerWindow or native TerminalInfo)
WindowData = Union[tmux_manager.InnerWindow, TerminalInfo]


class _SignalFileWatcher:
    """Watches for new signal files in the permission_request directory.

    Uses OS-native file watching via asyncio when available,
    otherwise falls back to checking directory mtime.
    """

    def __init__(self, callback: Callable[[], None]) -> None:
        self._callback = callback
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_mtime: float = 0
        self._seen_files: set[str] = set()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        # Initialize seen files
        self._scan_existing_files()
        self._task = asyncio.create_task(self._watch_loop())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def _scan_existing_files(self) -> None:
        """Record existing signal files so we only react to new ones."""
        try:
            if PERMISSION_SIGNAL_DIR.exists():
                self._seen_files = {
                    f.name for f in PERMISSION_SIGNAL_DIR.iterdir() if f.suffix == ".signal"
                }
        except Exception:
            self._seen_files = set()

    async def _watch_loop(self) -> None:
        """Watch for new signal files using directory mtime checks."""
        try:
            while self._running:
                # Wait a bit before checking (reduces CPU usage)
                await asyncio.sleep(0.5)

                if not self._running:
                    break

                try:
                    if not PERMISSION_SIGNAL_DIR.exists():
                        continue

                    # Check if directory was modified
                    current_mtime = PERMISSION_SIGNAL_DIR.stat().st_mtime
                    if current_mtime <= self._last_mtime:
                        continue
                    self._last_mtime = current_mtime

                    # Check for new signal files
                    current_files = {
                        f.name for f in PERMISSION_SIGNAL_DIR.iterdir() if f.suffix == ".signal"
                    }
                    new_files = current_files - self._seen_files

                    if new_files:
                        self._seen_files = current_files
                        # New signal file detected - trigger callback
                        self._callback()
                        # Clean up old signal files (keep last 10)
                        self._cleanup_old_signals()

                except Exception:
                    pass  # Ignore errors, keep watching

        except asyncio.CancelledError:
            pass

    def _cleanup_old_signals(self) -> None:
        """Remove old signal files to prevent directory from growing."""
        try:
            if not PERMISSION_SIGNAL_DIR.exists():
                return
            files = sorted(
                PERMISSION_SIGNAL_DIR.glob("*.signal"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            # Keep only the 10 most recent
            for f in files[10:]:
                try:
                    f.unlink()
                except Exception:
                    pass
        except Exception:
            pass


def _detect_terminal_mode() -> str:
    """Detect which terminal mode to use.

    Returns:
        Terminal mode string (MODE_TMUX, MODE_ITERM2, or MODE_KITTY)
    """
    mode = os.environ.get(ENV_TERMINAL_MODE, "").strip().lower()

    if mode in {MODE_ITERM2, "iterm"}:
        return MODE_ITERM2
    if mode == MODE_KITTY:
        return MODE_KITTY
    if mode == MODE_NATIVE:
        # Auto-detect best native terminal
        term_program = os.environ.get("TERM_PROGRAM", "").strip()
        if term_program in {"iTerm.app", "iTerm2"} or term_program.startswith("iTerm"):
            return MODE_ITERM2
        if term_program == "kitty":
            return MODE_KITTY
        # Default to iTerm2 on macOS
        import sys
        if sys.platform == "darwin":
            return MODE_ITERM2
        return MODE_TMUX

    # Default to tmux
    return MODE_TMUX


async def _get_native_backend(mode: str) -> TerminalBackend | None:
    """Get the appropriate native terminal backend.

    Args:
        mode: Terminal mode (MODE_ITERM2 or MODE_KITTY)

    Returns:
        Backend instance if available, None otherwise
    """
    if mode == MODE_ITERM2:
        try:
            from ..backends.iterm2 import ITermBackend

            # Check for split pane session ID from environment
            right_pane_session_id = os.environ.get("ALINE_ITERM2_RIGHT_PANE")
            if right_pane_session_id:
                logger.debug(f"Using split pane mode with right pane: {right_pane_session_id}")

            backend = ITermBackend(right_pane_session_id=right_pane_session_id)
            if await backend.is_available():
                return backend
        except Exception as e:
            logger.debug(f"iTerm2 backend not available: {e}")
    elif mode == MODE_KITTY:
        try:
            from ..backends.kitty import KittyBackend
            backend = KittyBackend()
            if await backend.is_available():
                return backend
        except Exception as e:
            logger.debug(f"Kitty backend not available: {e}")

    return None


class TerminalPanel(Container, can_focus=True):
    """Terminal controls panel with permission request notifications.

    Supports both native terminal backends (iTerm2/Kitty) and tmux.
    """

    class PermissionRequestDetected(Message):
        """Posted when a new permission request signal file is detected."""

        pass

    DEFAULT_CSS = """
    TerminalPanel {
        height: 100%;
        padding: 0 1;
        overflow: hidden;
    }

    TerminalPanel:focus {
        border: none;
    }

    TerminalPanel .summary {
        height: auto;
        margin: 0 0 1 0;
        padding: 0;
        background: transparent;
        border: none;
    }

    /* Override global dashboard button borders for a compact "list" look. */
    TerminalPanel Button {
        min-width: 0;
        padding: 0 1;
        background: transparent;
        border: none;
    }

    TerminalPanel Button:hover {
        background: $surface-lighten-1;
    }

    TerminalPanel .summary Button {
        width: auto;
        margin-right: 1;
    }

    TerminalPanel .status {
        width: 1fr;
        height: auto;
        color: $text-muted;
        content-align: right middle;
    }

    TerminalPanel .list {
        height: 1fr;
        padding: 0;
        overflow-y: auto;
        border: none;
        background: transparent;
    }

    TerminalPanel .terminal-row {
        height: auto;
        min-height: 2;
        margin: 0 0 1 0;
    }

    TerminalPanel .terminal-row Button.terminal-switch {
        width: 1fr;
        height: 2;
        margin: 0;
        padding: 0 1;
        text-align: left;
        content-align: left top;
    }

    TerminalPanel .terminal-row Button.terminal-close {
        width: 3;
        min-width: 3;
        height: 2;
        margin-left: 1;
        padding: 0;
        content-align: center middle;
    }

    TerminalPanel .terminal-row .attention-dot {
        width: 2;
        min-width: 2;
        height: 2;
        color: $error;
        content-align: center middle;
        margin-right: 0;
    }

    TerminalPanel .terminal-row Button.terminal-toggle {
        width: 3;
        min-width: 3;
        height: 2;
        margin-left: 1;
        padding: 0;
        content-align: center middle;
    }

    TerminalPanel .context-sessions {
        height: 8;
        margin: -1 0 1 2;
        color: $text-muted;
        padding: 0;
        border: none;
        overflow-y: auto;
    }

    TerminalPanel Button.context-session {
        width: 1fr;
        height: auto;
        margin: 0 0 0 0;
        padding: 0 0;
        background: transparent;
        border: none;
        text-style: none;
        text-align: left;
        content-align: left middle;
    }

    TerminalPanel .context-sessions Static {
        text-align: left;
        content-align: left middle;
    }
    """

    @staticmethod
    def supported() -> bool:
        """Check if terminal controls are supported.

        Supports both native terminal mode and tmux mode.
        """
        mode = _detect_terminal_mode()

        if mode == MODE_TMUX:
            return (
                tmux_manager.tmux_available()
                and tmux_manager.in_tmux()
                and tmux_manager.managed_env_enabled()
            )

        # For native mode, we check availability asynchronously in refresh_data
        # Here we just return True if native mode is requested
        return mode in {MODE_ITERM2, MODE_KITTY}

    @staticmethod
    def _support_message() -> str:
        mode = _detect_terminal_mode()

        if mode == MODE_TMUX:
            if not tmux_manager.tmux_available():
                return "tmux not installed. Run `aline add tmux`, then restart `aline`."
            if not tmux_manager.in_tmux():
                return "Not running inside tmux. Restart with `aline` to enable terminal controls."
            if not tmux_manager.managed_env_enabled():
                return "Not in an Aline-managed tmux session. Start via `aline` to enable terminal controls."
        elif mode == MODE_ITERM2:
            return "iTerm2 Python API not available. Install with: pip install iterm2"
        elif mode == MODE_KITTY:
            return "Kitty remote control not available. Configure listen_on in kitty.conf"

        return ""

    @staticmethod
    def _is_claude_window(w: WindowData) -> bool:
        """Check if a window is a Claude terminal."""
        if isinstance(w, TerminalInfo):
            # Native terminal: check provider
            return w.provider == "claude"

        window_name = (w.window_name or "").strip().lower()
        if re.fullmatch(r"codex(?:-\d+)?", window_name or ""):
            return False

        # tmux: prefer explicit provider/session_type tags
        if (w.provider or w.session_type):
            return (w.provider == "claude") or (w.session_type == "claude")

        # tmux: fallback to window name heuristic
        if re.fullmatch(r"cc(?:-\d+)?", window_name or ""):
            return True
        return False

    @staticmethod
    def _is_codex_window(w: WindowData) -> bool:
        """Check if a window is a Codex terminal."""
        if isinstance(w, TerminalInfo):
            return w.provider == "codex"

        # tmux: prefer explicit provider/session_type tags
        if (w.provider or w.session_type):
            return (w.provider == "codex") or (w.session_type == "codex")

        window_name = (w.window_name or "").strip().lower()
        if re.fullmatch(r"codex(?:-\d+)?", window_name or ""):
            return True

        return False

    @classmethod
    def _supports_context(cls, w: WindowData) -> bool:
        return cls._is_claude_window(w) or cls._is_codex_window(w)

    @staticmethod
    def _is_internal_tmux_window(w: tmux_manager.InnerWindow) -> bool:
        """Hide internal tmux windows (e.g., the reserved 'home' window)."""
        if not w.no_track:
            return False
        if (w.window_name or "").strip().lower() != "home":
            return False
        return not any(
            (
                (w.terminal_id or "").strip(),
                (w.provider or "").strip(),
                (w.session_type or "").strip(),
                (w.session_id or "").strip(),
                (w.context_id or "").strip(),
                (w.transcript_path or "").strip(),
                (w.attention or "").strip(),
            )
        )

    def _maybe_link_codex_session_for_terminal(
        self, *, terminal_id: str, created_at: float | None
    ) -> None:
        """Best-effort: bind a Codex session file to a dashboard terminal (no watcher required)."""
        terminal_id = (terminal_id or "").strip()
        if not terminal_id:
            return

        now = time.time()
        last = self._codex_link_last_attempt.get(terminal_id, 0.0)
        if now - last < 2.0:
            return
        self._codex_link_last_attempt[terminal_id] = now

        try:
            from ...codex_terminal_linker import read_codex_session_meta
            from ...db import get_database
            from ...codex_home import codex_sessions_dir_for_terminal_or_agent
        except Exception:
            return

        try:
            db = get_database(read_only=False)
            agent = db.get_agent_by_id(terminal_id)
            if not agent or agent.provider != "codex" or agent.status != "active":
                return
            if agent.session_id:
                return
            cwd = (agent.cwd or "").strip()
            if not cwd:
                return
        except Exception:
            return

        candidates: list[Path] = []
        agent_info_id: str | None = None
        if (agent.source or "").startswith("agent:"):
            agent_info_id = agent.source[6:]
        sessions_root = codex_sessions_dir_for_terminal_or_agent(terminal_id, agent_info_id)
        if sessions_root.exists():
            # Deterministic: isolated per-terminal/per-agent CODEX_HOME.
            try:
                candidates = list(sessions_root.rglob("rollout-*.jsonl"))
            except Exception:
                candidates = []
        else:
            # Fallback for legacy terminals not launched with isolated CODEX_HOME.
            try:
                from ...codex_detector import find_codex_sessions_for_project

                candidates = find_codex_sessions_for_project(Path(cwd), days_back=3)
            except Exception:
                candidates = []
        if not candidates:
            return

        created_dt: datetime | None = None
        if created_at is not None:
            try:
                created_dt = datetime.fromtimestamp(float(created_at), tz=timezone.utc)
            except Exception:
                created_dt = None

        best: Path | None = None
        best_score: float | None = None
        candidates.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        for session_file in candidates[:200]:
            meta = read_codex_session_meta(session_file)
            if meta is None or (meta.cwd or "").strip() != cwd:
                continue

            started_dt: datetime | None = meta.started_at
            if started_dt is None:
                try:
                    started_dt = datetime.fromtimestamp(
                        session_file.stat().st_mtime, tz=timezone.utc
                    )
                except Exception:
                    started_dt = None
            if started_dt is None:
                continue

            if created_dt is not None:
                delta = abs((started_dt - created_dt).total_seconds())
            else:
                try:
                    delta = abs(time.time() - session_file.stat().st_mtime)
                except Exception:
                    continue

            penalty = 0.0
            origin = (meta.originator or "").lower()
            if "vscode" in origin:
                penalty += 3600.0
            score = float(delta) + penalty

            if best_score is None or score < best_score:
                best_score = score
                best = session_file

        if not best:
            return

        # Avoid binding wildly unrelated sessions.
        if best_score is not None and best_score > 6 * 60 * 60:
            return

        try:
            source = "dashboard:auto-link"
            if (agent.source or "").startswith("agent:"):
                source = agent.source or source
            db.update_agent(
                terminal_id,
                provider="codex",
                session_type="codex",
                session_id=best.stem,
                transcript_path=str(best),
                cwd=cwd,
                project_dir=cwd,
                source=source,
            )
            if agent_info_id:
                try:
                    db.update_session_agent_id(best.stem, agent_info_id)
                except Exception:
                    pass
        except Exception:
            return

    def __init__(self, use_native_terminal: bool | None = None) -> None:
        """Initialize the terminal panel.

        Args:
            use_native_terminal: If True, use native terminal backend.
                                 If False, use tmux.
                                 If None (default), auto-detect from environment.
        """
        super().__init__()
        self._refresh_lock = asyncio.Lock()
        self._expanded_window_id: str | None = None
        self._signal_watcher: _SignalFileWatcher | None = None

        # Determine terminal mode
        if use_native_terminal is True:
            self._mode = _detect_terminal_mode()
            if self._mode == MODE_TMUX:
                self._mode = MODE_ITERM2  # Default to iTerm2 if native requested
        elif use_native_terminal is False:
            self._mode = MODE_TMUX
        else:
            self._mode = _detect_terminal_mode()

        # Native backend (initialized lazily)
        self._native_backend: TerminalBackend | None = None
        self._native_backend_checked = False

        # Best-effort Codex session binding without requiring the watcher process.
        self._codex_link_last_attempt: dict[str, float] = {}

    def compose(self) -> ComposeResult:
        logger.debug("TerminalPanel.compose() started")
        try:
            controls_enabled = self.supported()
            with Horizontal(classes="summary"):
                yield Button(
                    "＋ New Agent",
                    id="quick-new-agent",
                    variant="primary",
                    disabled=not controls_enabled,
                )
                yield Button(
                    "＋ Create",
                    id="new-agent",
                    variant="default",
                    disabled=not controls_enabled,
                )
            with Vertical(id="terminals", classes="list"):
                if controls_enabled:
                    yield Static(
                        "No terminals yet. Click 'Create' to open a new agent terminal."
                    )
                else:
                    yield Static(self._support_message())
            logger.debug("TerminalPanel.compose() completed")
        except Exception as e:
            logger.error(f"TerminalPanel.compose() failed: {e}\n{traceback.format_exc()}")
            raise

    def on_show(self) -> None:
        self.call_after_refresh(
            lambda: self.run_worker(
                self.refresh_data(),
                group="terminal-panel-refresh",
                exclusive=True,
            )
        )
        self._start_signal_watcher()

    def on_hide(self) -> None:
        self._stop_signal_watcher()

    def _start_signal_watcher(self) -> None:
        """Start watching for permission request signal files."""
        if self._signal_watcher is not None:
            return
        self._signal_watcher = _SignalFileWatcher(self._on_permission_signal)
        self._signal_watcher.start()

    def _stop_signal_watcher(self) -> None:
        """Stop watching for permission request signal files."""
        if self._signal_watcher is not None:
            self._signal_watcher.stop()
            self._signal_watcher = None

    def _on_permission_signal(self) -> None:
        """Called when a new permission request signal is detected."""
        self.post_message(self.PermissionRequestDetected())

    def on_terminal_panel_permission_request_detected(
        self, event: PermissionRequestDetected
    ) -> None:
        """Handle permission request detection - refresh the terminal list."""
        self.run_worker(
            self.refresh_data(),
            group="terminal-panel-refresh",
            exclusive=True,
        )

    async def _ensure_native_backend(self) -> TerminalBackend | None:
        """Ensure native backend is initialized."""
        if self._native_backend_checked:
            return self._native_backend

        self._native_backend_checked = True

        if self._mode in {MODE_ITERM2, MODE_KITTY}:
            self._native_backend = await _get_native_backend(self._mode)

        return self._native_backend

    def _is_native_mode(self) -> bool:
        """Check if we're using native terminal mode."""
        return self._mode in {MODE_ITERM2, MODE_KITTY}

    async def refresh_data(self) -> None:
        async with self._refresh_lock:
            t_start = time.time()
            # Check and close stale terminals if enabled
            await self._close_stale_terminals_if_enabled()
            logger.debug(f"[PERF] _close_stale_terminals_if_enabled: {time.time() - t_start:.3f}s")

            t_refresh = time.time()
            if self._is_native_mode():
                await self._refresh_native_data()
            else:
                await self._refresh_tmux_data()
            logger.debug(f"[PERF] total refresh: {time.time() - t_start:.3f}s")

    async def _close_stale_terminals_if_enabled(self) -> None:
        """Close terminals that haven't been updated for the configured hours."""
        try:
            from ...config import ReAlignConfig

            config = ReAlignConfig.load()
            if not config.auto_close_stale_terminals:
                return

            stale_hours = config.stale_terminal_hours or 24
            cutoff_time = datetime.now() - timedelta(hours=stale_hours)

            # Get stale agents from database
            from ...db import get_database

            db = get_database(read_only=True)
            all_agents = db.list_agents(status="active", limit=1000)

            stale_agent_ids = set()
            for agent in all_agents:
                if agent.updated_at and agent.updated_at < cutoff_time:
                    stale_agent_ids.add(agent.id)

            if not stale_agent_ids:
                return

            # Get current windows
            if self._is_native_mode():
                backend = await self._ensure_native_backend()
                if not backend:
                    return
                windows = await backend.list_tabs()
                for w in windows:
                    if w.terminal_id in stale_agent_ids:
                        logger.info(f"Auto-closing stale terminal: {w.terminal_id}")
                        await backend.close_tab(w.session_id)
            else:
                windows = tmux_manager.list_inner_windows()
                for w in windows:
                    if w.terminal_id in stale_agent_ids:
                        logger.info(f"Auto-closing stale terminal: {w.terminal_id}")
                        tmux_manager.kill_inner_window(w.window_id)

        except Exception as e:
            logger.debug(f"Error checking stale terminals: {e}")

    async def _refresh_native_data(self) -> None:
        """Refresh data using native terminal backend."""
        backend = await self._ensure_native_backend()
        if not backend:
            # Fall back to showing error message
            try:
                container = self.query_one("#terminals", Vertical)
                await container.remove_children()
                await container.mount(Static(self._support_message()))
            except Exception:
                pass
            return

        try:
            windows = await backend.list_tabs()
        except Exception as e:
            logger.error(f"Failed to list native terminals: {e}")
            return

        # Yield to event loop to keep UI responsive
        await asyncio.sleep(0)

        # NOTE: _maybe_link_codex_session_for_terminal is intentionally skipped here
        # because it performs expensive file system scans (find_codex_sessions_for_project)
        # that can take minutes with many session files. Codex session linking is handled
        # by the watcher process instead.

        active_window_id = next(
            (w.session_id for w in windows if w.active), None
        )
        if self._expanded_window_id and self._expanded_window_id != active_window_id:
            self._expanded_window_id = None

        # Titles (best-effort; native terminals only expose Claude session ids today)
        claude_ids = [
            w.claude_session_id
            for w in windows
            if self._is_claude_window(w) and w.claude_session_id
        ]
        titles = self._fetch_claude_session_titles(claude_ids)

        # Yield to event loop after DB query
        await asyncio.sleep(0)

        # Get context info
        context_info_by_context_id: dict[str, tuple[list[str], int, int]] = {}
        all_context_session_ids: set[str] = set()
        for w in windows:
            if not self._supports_context(w) or not w.context_id:
                continue
            session_ids, session_count, event_count = self._get_loaded_context_info(
                w.context_id
            )
            if not session_ids and session_count == 0 and event_count == 0:
                continue
            context_info_by_context_id[w.context_id] = (
                session_ids,
                session_count,
                event_count,
            )
            all_context_session_ids.update(session_ids)

        if all_context_session_ids:
            titles.update(self._fetch_claude_session_titles(sorted(all_context_session_ids)))

        try:
            await self._render_terminals_native(windows, titles, context_info_by_context_id)
        except Exception:
            return

    async def _refresh_tmux_data(self) -> None:
        """Refresh data using tmux backend."""
        t0 = time.time()
        try:
            supported = self.supported()
        except Exception:
            return

        if not supported:
            return

        try:
            windows = tmux_manager.list_inner_windows()
        except Exception:
            return
        windows = [w for w in windows if not self._is_internal_tmux_window(w)]
        logger.debug(f"[PERF] list_inner_windows: {time.time() - t0:.3f}s")

        # Yield to event loop to keep UI responsive
        await asyncio.sleep(0)

        # NOTE: _maybe_link_codex_session_for_terminal is intentionally skipped here
        # because it performs expensive file system scans (find_codex_sessions_for_project)
        # that can take minutes with many session files. Codex session linking is handled
        # by the watcher process instead.

        active_window_id = next((w.window_id for w in windows if w.active), None)
        if self._expanded_window_id and self._expanded_window_id != active_window_id:
            self._expanded_window_id = None

        t1 = time.time()
        session_ids = [w.session_id for w in windows if self._supports_context(w) and w.session_id]
        titles = self._fetch_claude_session_titles(session_ids)
        logger.debug(f"[PERF] fetch_claude_session_titles: {time.time() - t1:.3f}s")

        # Yield to event loop after DB query
        await asyncio.sleep(0)

        t2 = time.time()
        context_info_by_context_id: dict[str, tuple[list[str], int, int]] = {}
        all_context_session_ids: set[str] = set()
        for w in windows:
            if not self._supports_context(w) or not w.context_id:
                continue
            session_ids, session_count, event_count = self._get_loaded_context_info(
                w.context_id
            )
            if not session_ids and session_count == 0 and event_count == 0:
                continue
            context_info_by_context_id[w.context_id] = (
                session_ids,
                session_count,
                event_count,
            )
            all_context_session_ids.update(session_ids)
            # Yield periodically during context info gathering
            await asyncio.sleep(0)
        logger.debug(f"[PERF] get_loaded_context_info loop: {time.time() - t2:.3f}s")

        t3 = time.time()
        if all_context_session_ids:
            titles.update(self._fetch_claude_session_titles(sorted(all_context_session_ids)))
        logger.debug(f"[PERF] fetch context session titles: {time.time() - t3:.3f}s")

        t4 = time.time()
        try:
            await self._render_terminals_tmux(windows, titles, context_info_by_context_id)
        except Exception:
            return
        logger.debug(f"[PERF] render_terminals_tmux: {time.time() - t4:.3f}s")

    def _fetch_claude_session_titles(self, session_ids: list[str]) -> dict[str, str]:
        # Back-compat hook for tests and older call sites.
        return self._fetch_session_titles(session_ids)

    def _fetch_session_titles(self, session_ids: list[str]) -> dict[str, str]:
        if not session_ids:
            return {}
        try:
            from ...db import get_database

            db = get_database(read_only=True)
            sessions = db.get_sessions_by_ids(session_ids)
            titles: dict[str, str] = {}
            for s in sessions:
                title = (s.session_title or "").strip()
                if title:
                    titles[s.id] = title
            return titles
        except Exception:
            return {}

    def _get_loaded_context_info(self, context_id: str) -> tuple[list[str], int, int]:
        """Best-effort: read ~/.aline/load.json for a context_id, and return its session ids."""
        context_id = (context_id or "").strip()
        if not context_id:
            return ([], 0, 0)
        try:
            from ...context import get_context_by_id, load_context_config

            config = load_context_config()
            if config is None:
                return ([], 0, 0)
            entry = get_context_by_id(context_id, config)
            if entry is None:
                return ([], 0, 0)

            raw_sessions: set[str] = set(
                str(s).strip() for s in (entry.context_sessions or []) if str(s).strip()
            )
            raw_events: list[str] = [
                str(e).strip() for e in (entry.context_events or []) if str(e).strip()
            ]
            raw_event_ids: set[str] = set(raw_events)

            out: set[str] = set(raw_sessions)

            if raw_events:
                try:
                    from ...db import get_database

                    db = get_database(read_only=True)
                    for event_id in raw_events:
                        try:
                            sessions = db.get_sessions_for_event(str(event_id))
                            out.update(s.id for s in sessions if getattr(s, "id", None))
                        except Exception:
                            continue
                except Exception:
                    pass

            return (sorted(out), len(raw_sessions), len(raw_event_ids))
        except Exception:
            return ([], 0, 0)

    async def _render_terminals_native(
        self,
        windows: list[TerminalInfo],
        titles: dict[str, str],
        context_info_by_context_id: dict[str, tuple[list[str], int, int]],
    ) -> None:
        """Render terminal list for native backend."""
        container = self.query_one("#terminals", Vertical)
        await container.remove_children()

        if not windows:
            await container.mount(
                Static("No terminals yet. Click 'Create' to open a new agent terminal.")
            )
            return

        for w in windows:
            safe = self._safe_id_fragment(w.session_id)
            row = Horizontal(classes="terminal-row")
            await container.mount(row)

            if w.attention:
                await row.mount(Static("●", classes="attention-dot"))

            switch_classes = "terminal-switch active" if w.active else "terminal-switch"
            loaded_ids: list[str] = []
            raw_sessions = 0
            raw_events = 0
            if self._supports_context(w) and w.context_id:
                loaded_ids, raw_sessions, raw_events = context_info_by_context_id.get(
                    w.context_id, ([], 0, 0)
                )

            label = self._window_label_native(w, titles, raw_sessions, raw_events)
            await row.mount(
                Button(
                    label,
                    id=f"switch-{safe}",
                    name=w.session_id,
                    classes=switch_classes,
                )
            )

            can_toggle_ctx = bool(self._supports_context(w) and w.context_id and (raw_sessions or raw_events))
            expanded = bool(w.active and w.session_id == self._expanded_window_id)
            if w.active and can_toggle_ctx:
                await row.mount(
                    Button(
                        "▼" if expanded else "▶",
                        id=f"toggle-{safe}",
                        name=w.session_id,
                        variant="default",
                        classes="terminal-toggle",
                    )
                )

            await row.mount(
                Button(
                    "✕",
                    id=f"close-{safe}",
                    name=w.session_id,
                    variant="error",
                    classes="terminal-close",
                )
            )

            if w.active and self._supports_context(w) and w.context_id and expanded:
                ctx = VerticalScroll(id=f"ctx-{safe}", classes="context-sessions")
                await container.mount(ctx)
                if loaded_ids:
                    for idx, sid in enumerate(loaded_ids):
                        title = titles.get(sid, "").strip() or "(no title)"
                        await ctx.mount(
                            Button(
                                f"{title} ({self._short_id(sid)})",
                                id=f"ctxsess-{safe}-{idx}",
                                name=sid,
                                variant="default",
                                classes="context-session",
                            )
                        )
                else:
                    await ctx.mount(
                        Static(
                            "[dim]Context loaded, but session list isn't available (events not expanded).[/dim]"
                        )
                    )

    async def _render_terminals_tmux(
        self,
        windows: list[tmux_manager.InnerWindow],
        titles: dict[str, str],
        context_info_by_context_id: dict[str, tuple[list[str], int, int]],
    ) -> None:
        """Render terminal list for tmux backend."""
        container = self.query_one("#terminals", Vertical)
        await container.remove_children()

        if not windows:
            await container.mount(
                Static("No terminals yet. Click 'Create' to open a new agent terminal.")
            )
            return

        for w in windows:
            safe = self._safe_id_fragment(w.window_id)
            row = Horizontal(classes="terminal-row")
            await container.mount(row)
            # Show attention dot if window needs attention
            if w.attention:
                await row.mount(Static("●", classes="attention-dot"))
            switch_classes = "terminal-switch active" if w.active else "terminal-switch"
            loaded_ids: list[str] = []
            raw_sessions = 0
            raw_events = 0
            if self._supports_context(w) and w.context_id:
                loaded_ids, raw_sessions, raw_events = context_info_by_context_id.get(
                    w.context_id, ([], 0, 0)
                )
            label = self._window_label_tmux(w, titles, raw_sessions, raw_events)
            await row.mount(
                Button(
                    label,
                    id=f"switch-{safe}",
                    name=w.window_id,
                    classes=switch_classes,
                )
            )
            can_toggle_ctx = bool(self._supports_context(w) and w.context_id and (raw_sessions or raw_events))
            expanded = bool(w.active and w.window_id == self._expanded_window_id)
            if w.active and can_toggle_ctx:
                await row.mount(
                    Button(
                        "▼" if expanded else "▶",
                        id=f"toggle-{safe}",
                        name=w.window_id,
                        variant="default",
                        classes="terminal-toggle",
                    )
                )
            await row.mount(
                Button(
                    "✕",
                    id=f"close-{safe}",
                    name=w.window_id,
                    variant="error",
                    classes="terminal-close",
                )
            )

            if w.active and self._supports_context(w) and w.context_id and expanded:
                ctx = VerticalScroll(id=f"ctx-{safe}", classes="context-sessions")
                await container.mount(ctx)
                if loaded_ids:
                    for idx, sid in enumerate(loaded_ids):
                        title = titles.get(sid, "").strip() or "(no title)"
                        await ctx.mount(
                            Button(
                                f"{title} ({self._short_id(sid)})",
                                id=f"ctxsess-{safe}-{idx}",
                                name=sid,
                                variant="default",
                                classes="context-session",
                            )
                        )
                else:
                    await ctx.mount(
                        Static(
                            "[dim]Context loaded, but session list isn't available (events not expanded).[/dim]"
                        )
                    )

    @staticmethod
    def _format_context_summary(session_count: int, event_count: int) -> str:
        parts: list[str] = []
        if session_count:
            parts.append(f"{session_count}s")
        if event_count:
            parts.append(f"{event_count}e")
        if not parts:
            return "ctx 0"
        return "ctx " + " ".join(parts)

    def _window_label_native(
        self,
        w: TerminalInfo,
        titles: dict[str, str],
        raw_sessions: int = 0,
        raw_events: int = 0,
    ) -> str | Text:
        """Generate label for native terminal window."""
        if not self._supports_context(w):
            return Text(w.name, no_wrap=True, overflow="ellipsis")

        if self._is_codex_window(w):
            details = Text(no_wrap=True, overflow="ellipsis")
            details.append("Codex")
            details.append("\n")
            detail_line = "[Codex]"
            if w.active:
                loaded_count = raw_sessions + raw_events
                detail_line = f"{detail_line} | loaded context: {loaded_count}"
            else:
                detail_line = (
                    f"{detail_line} · {self._format_context_summary(raw_sessions, raw_events)}"
                )
            if w.metadata.get("no_track") == "1":
                detail_line = f"{detail_line} [NT]"
            details.append(detail_line, style="dim not bold")
            return details

        title = titles.get(w.claude_session_id or "", "").strip() if w.claude_session_id else ""
        header = title or ("Claude" if w.claude_session_id else "New Claude")

        details = Text(no_wrap=True, overflow="ellipsis")
        details.append(header)
        details.append("\n")

        detail_line = "[Claude]"
        if w.claude_session_id:
            detail_line = f"{detail_line} #{self._short_id(w.claude_session_id)}"
        if w.active:
            loaded_count = raw_sessions + raw_events
            detail_line = f"{detail_line} | loaded context: {loaded_count}"
        else:
            detail_line = (
                f"{detail_line} · {self._format_context_summary(raw_sessions, raw_events)}"
            )
        # Show no-track indicator
        if w.metadata.get("no_track") == "1":
            detail_line = f"{detail_line} [NT]"
        details.append(detail_line, style="dim not bold")
        return details

    def _window_label_tmux(
        self,
        w: tmux_manager.InnerWindow,
        titles: dict[str, str],
        raw_sessions: int = 0,
        raw_events: int = 0,
    ) -> str | Text:
        """Generate label for tmux window."""
        if not self._supports_context(w):
            return Text(w.window_name, no_wrap=True, overflow="ellipsis")

        if self._is_codex_window(w):
            title = titles.get(w.session_id or "", "").strip() if w.session_id else ""
            header = title or ("Codex" if w.session_id else "New Codex")

            details = Text(no_wrap=True, overflow="ellipsis")
            details.append(header)
            details.append("\n")

            detail_line = "[Codex]"
            if w.session_id:
                detail_line = f"{detail_line} #{self._short_id(w.session_id)}"
            if w.active:
                loaded_count = raw_sessions + raw_events
                detail_line = f"{detail_line} | loaded context: {loaded_count}"
            else:
                detail_line = (
                    f"{detail_line} · {self._format_context_summary(raw_sessions, raw_events)}"
                )
            if w.no_track:
                detail_line = f"{detail_line} [NT]"
            details.append(detail_line, style="dim not bold")
            return details

        title = titles.get(w.session_id or "", "").strip() if w.session_id else ""
        header = title or ("Claude" if w.session_id else "New Claude")

        details = Text(no_wrap=True, overflow="ellipsis")
        details.append(header)
        details.append("\n")

        detail_line = "[Claude]"
        if w.session_id:
            detail_line = f"{detail_line} #{self._short_id(w.session_id)}"
        if w.active:
            loaded_count = raw_sessions + raw_events
            detail_line = f"{detail_line} | loaded context: {loaded_count}"
        else:
            detail_line = (
                f"{detail_line} · {self._format_context_summary(raw_sessions, raw_events)}"
            )
        # Show no-track indicator
        if w.no_track:
            detail_line = f"{detail_line} [NT]"
        details.append(detail_line, style="dim not bold")
        return details

    @staticmethod
    def _short_id(value: str) -> str:
        value = str(value)
        if len(value) > 20:
            return value[:8] + "..." + value[-8:]
        return value

    @staticmethod
    def _safe_id_fragment(raw: str) -> str:
        # Textual ids must match: [A-Za-z_][A-Za-z0-9_-]*
        safe = re.sub(r"[^A-Za-z0-9_-]+", "-", raw).strip("-_")
        if not safe:
            return "w"
        if safe[0].isdigit():
            return f"w-{safe}"
        return safe

    @staticmethod
    def _command_in_directory(command: str, directory: str) -> str:
        """Wrap a command to run in a specific directory."""
        return f"cd {shlex.quote(directory)} && {command}"

    async def _quick_create_claude_agent(self) -> None:
        """Quickly create a new Claude Code terminal with default settings.

        Uses the last workspace (or cwd) with normal permissions and tracking enabled.
        """
        from ..screens.create_agent import _load_last_workspace

        workspace = _load_last_workspace()
        self.run_worker(
            self._create_agent("claude", workspace, skip_permissions=False, no_track=False),
            group="terminal-panel-create",
            exclusive=True,
        )

    def _on_create_agent_result(self, result: tuple[str, str, bool, bool] | None) -> None:
        """Handle the result from CreateAgentScreen modal."""
        if result is None:
            return

        agent_type, workspace, skip_permissions, no_track = result

        # Capture self reference for use in the deferred callback
        panel = self

        # Use app.call_later to defer worker creation until after the modal is dismissed.
        # This ensures the modal screen is fully closed before the worker starts,
        # preventing UI update conflicts between modal closing and terminal panel refresh.
        def start_worker() -> None:
            panel.run_worker(
                panel._create_agent(
                    agent_type, workspace, skip_permissions=skip_permissions, no_track=no_track
                ),
                group="terminal-panel-create",
                exclusive=True,
            )

        self.app.call_later(start_worker)

    async def _create_agent(
        self, agent_type: str, workspace: str, *, skip_permissions: bool = False, no_track: bool = False
    ) -> None:
        """Create a new agent terminal based on the selected type and workspace."""
        if agent_type == "claude":
            await self._create_claude_terminal(workspace, skip_permissions=skip_permissions, no_track=no_track)
        elif agent_type == "codex":
            await self._create_codex_terminal(workspace, no_track=no_track)
        elif agent_type == "opencode":
            await self._create_opencode_terminal(workspace)
        elif agent_type == "zsh":
            await self._create_zsh_terminal(workspace)
        # Schedule refresh in a separate worker to avoid blocking UI.
        # The refresh involves slow synchronous operations (DB queries, file scans)
        # that would otherwise freeze the dashboard.
        self.run_worker(
            self.refresh_data(),
            group="terminal-panel-refresh",
            exclusive=True,
        )

    async def _create_claude_terminal(
        self, workspace: str, *, skip_permissions: bool = False, no_track: bool = False
    ) -> None:
        """Create a new Claude terminal."""
        if self._is_native_mode():
            await self._create_claude_terminal_native(workspace, skip_permissions=skip_permissions, no_track=no_track)
        else:
            await self._create_claude_terminal_tmux(workspace, skip_permissions=skip_permissions, no_track=no_track)

    async def _create_claude_terminal_native(
        self, workspace: str, *, skip_permissions: bool = False, no_track: bool = False
    ) -> None:
        """Create a new Claude terminal using native backend."""
        backend = await self._ensure_native_backend()
        if not backend:
            self.app.notify(
                "Native terminal backend not available",
                title="Terminal",
                severity="error",
            )
            return

        terminal_id = tmux_manager.new_terminal_id()
        context_id = tmux_manager.new_context_id("cc")

        env = {
            tmux_manager.ENV_TERMINAL_ID: terminal_id,
            tmux_manager.ENV_TERMINAL_PROVIDER: "claude",
            tmux_manager.ENV_CONTEXT_ID: context_id,
        }
        if no_track:
            env["ALINE_NO_TRACK"] = "1"

        # Install hooks
        self._install_claude_hooks(workspace)

        claude_cmd = "claude"
        if skip_permissions:
            claude_cmd = "claude --dangerously-skip-permissions"

        session_id = await backend.create_tab(
            command=claude_cmd,
            terminal_id=terminal_id,
            name="Claude Code",
            env=env,
            cwd=workspace,
        )

        if not session_id:
            self.app.notify(
                "Failed to open Claude terminal",
                title="Terminal",
                severity="error",
            )

    async def _create_claude_terminal_tmux(
        self, workspace: str, *, skip_permissions: bool = False, no_track: bool = False
    ) -> None:
        """Create a new Claude terminal using tmux backend."""
        terminal_id = tmux_manager.new_terminal_id()
        context_id = tmux_manager.new_context_id("cc")
        env = {
            tmux_manager.ENV_TERMINAL_ID: terminal_id,
            tmux_manager.ENV_TERMINAL_PROVIDER: "claude",
            tmux_manager.ENV_INNER_SOCKET: tmux_manager.INNER_SOCKET,
            tmux_manager.ENV_INNER_SESSION: tmux_manager.INNER_SESSION,
            tmux_manager.ENV_CONTEXT_ID: context_id,
        }
        if no_track:
            env["ALINE_NO_TRACK"] = "1"

        # Install hooks
        self._install_claude_hooks(workspace)

        claude_cmd = "claude"
        if skip_permissions:
            claude_cmd = "claude --dangerously-skip-permissions"
        command = self._command_in_directory(
            tmux_manager.zsh_run_and_keep_open(claude_cmd), workspace
        )
        created = tmux_manager.create_inner_window(
            "cc",
            tmux_manager.shell_command_with_env(command, env),
            terminal_id=terminal_id,
            provider="claude",
            context_id=context_id,
            no_track=no_track,
        )
        if not created:
            self.app.notify("Failed to open Claude terminal", title="Terminal", severity="error")

    def _install_claude_hooks(self, workspace: str) -> None:
        """Install Claude hooks for a workspace."""
        try:
            from ...claude_hooks.stop_hook_installer import (
                ensure_stop_hook_installed,
                get_settings_path as get_stop_settings_path,
                install_stop_hook,
            )
            from ...claude_hooks.user_prompt_submit_hook_installer import (
                ensure_user_prompt_submit_hook_installed,
                get_settings_path as get_submit_settings_path,
                install_user_prompt_submit_hook,
            )
            from ...claude_hooks.permission_request_hook_installer import (
                ensure_permission_request_hook_installed,
                get_settings_path as get_permission_settings_path,
                install_permission_request_hook,
            )

            ok_global_stop = ensure_stop_hook_installed(quiet=True)
            ok_global_submit = ensure_user_prompt_submit_hook_installed(quiet=True)
            ok_global_permission = ensure_permission_request_hook_installed(quiet=True)

            project_root = Path(workspace)
            ok_project_stop = install_stop_hook(
                get_stop_settings_path(project_root), quiet=True
            )
            ok_project_submit = install_user_prompt_submit_hook(
                get_submit_settings_path(project_root), quiet=True
            )
            ok_project_permission = install_permission_request_hook(
                get_permission_settings_path(project_root), quiet=True
            )

            all_hooks_ok = (
                ok_global_stop
                and ok_global_submit
                and ok_global_permission
                and ok_project_stop
                and ok_project_submit
                and ok_project_permission
            )
            if not all_hooks_ok:
                self.app.notify(
                    "Claude hooks not fully installed; session id/title may not update",
                    title="Terminal",
                    severity="warning",
                )
        except Exception:
            pass

    async def _create_codex_terminal(self, workspace: str, *, no_track: bool = False) -> None:
        """Create a new Codex terminal."""
        terminal_id = tmux_manager.new_terminal_id()
        context_id = tmux_manager.new_context_id("cx")

        # Use per-terminal CODEX_HOME so sessions/config are isolated and binding is deterministic.
        try:
            from ...codex_home import prepare_codex_home

            codex_home = prepare_codex_home(terminal_id)
        except Exception:
            codex_home = None

        env = {
            tmux_manager.ENV_TERMINAL_ID: terminal_id,
            tmux_manager.ENV_TERMINAL_PROVIDER: "codex",
            tmux_manager.ENV_CONTEXT_ID: context_id,
        }
        if codex_home is not None:
            env["CODEX_HOME"] = str(codex_home)
        if no_track:
            env["ALINE_NO_TRACK"] = "1"

        # Persist agent early so the watcher can bind the Codex session file back to this terminal.
        try:
            from ...db import get_database

            db = get_database(read_only=False)
            db.get_or_create_agent(
                terminal_id,
                provider="codex",
                session_type="codex",
                context_id=context_id,
                cwd=workspace,
                project_dir=workspace,
                source="dashboard",
            )
        except Exception:
            pass

        if self._is_native_mode():
            backend = await self._ensure_native_backend()
            if backend:
                session_id = await backend.create_tab(
                    command="codex",
                    terminal_id=terminal_id,
                    name="Codex",
                    env=env,
                    cwd=workspace,
                )
                if not session_id:
                    self.app.notify(
                        "Failed to open Codex terminal", title="Terminal", severity="error"
                    )
                return

        # Tmux fallback
        command = self._command_in_directory(
            tmux_manager.zsh_run_and_keep_open("codex"), workspace
        )
        created = tmux_manager.create_inner_window(
            "codex",
            tmux_manager.shell_command_with_env(command, env),
            terminal_id=terminal_id,
            provider="codex",
            context_id=context_id,
            no_track=no_track,
        )
        if not created:
            self.app.notify("Failed to open Codex terminal", title="Terminal", severity="error")

    async def _create_opencode_terminal(self, workspace: str) -> None:
        """Create a new Opencode terminal."""
        if self._is_native_mode():
            backend = await self._ensure_native_backend()
            if backend:
                terminal_id = tmux_manager.new_terminal_id()
                session_id = await backend.create_tab(
                    command="opencode",
                    terminal_id=terminal_id,
                    name="Opencode",
                    cwd=workspace,
                )
                if not session_id:
                    self.app.notify(
                        "Failed to open Opencode terminal", title="Terminal", severity="error"
                    )
                return

        # Tmux fallback
        command = self._command_in_directory(
            tmux_manager.zsh_run_and_keep_open("opencode"), workspace
        )
        created = tmux_manager.create_inner_window("opencode", command)
        if not created:
            self.app.notify("Failed to open Opencode terminal", title="Terminal", severity="error")

    async def _create_zsh_terminal(self, workspace: str) -> None:
        """Create a new zsh terminal."""
        t0 = time.time()
        logger.info(f"[PERF] _create_zsh_terminal START")
        if self._is_native_mode():
            backend = await self._ensure_native_backend()
            if backend:
                terminal_id = tmux_manager.new_terminal_id()
                session_id = await backend.create_tab(
                    command="zsh -l",
                    terminal_id=terminal_id,
                    name="zsh",
                    cwd=workspace,
                )
                if not session_id:
                    self.app.notify(
                        "Failed to open zsh terminal", title="Terminal", severity="error"
                    )
                logger.info(f"[PERF] _create_zsh_terminal native END: {time.time() - t0:.3f}s")
                return

        # Tmux fallback
        t1 = time.time()
        command = self._command_in_directory("zsh", workspace)
        logger.info(f"[PERF] _create_zsh_terminal command ready: {time.time() - t1:.3f}s")
        t2 = time.time()
        created = tmux_manager.create_inner_window("zsh", command)
        logger.info(f"[PERF] _create_zsh_terminal create_inner_window: {time.time() - t2:.3f}s")
        if not created:
            self.app.notify("Failed to open zsh terminal", title="Terminal", severity="error")
        logger.info(f"[PERF] _create_zsh_terminal TOTAL: {time.time() - t0:.3f}s")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""

        if not self.supported():
            self.app.notify(
                self._support_message(),
                title="Terminal",
                severity="warning",
            )
            return

        if button_id == "quick-new-agent":
            await self._quick_create_claude_agent()
            return

        if button_id == "new-agent":
            from ..screens import CreateAgentScreen

            self.app.push_screen(CreateAgentScreen(), self._on_create_agent_result)
            return

        if button_id.startswith("switch-"):
            await self._handle_switch(event.button.name or "")
            return

        if button_id.startswith("toggle-"):
            window_id = event.button.name or ""
            if not window_id:
                return
            if self._expanded_window_id == window_id:
                self._expanded_window_id = None
            else:
                self._expanded_window_id = window_id
            await self.refresh_data()
            return

        if button_id.startswith("ctxsess-"):
            session_id = (event.button.name or "").strip()
            if not session_id:
                return
            try:
                from ..screens import SessionDetailScreen

                self.app.push_screen(SessionDetailScreen(session_id))
            except Exception:
                pass
            return

        if button_id.startswith("close-"):
            await self._handle_close(event.button.name or "")
            return

    async def _handle_switch(self, window_id: str) -> None:
        """Handle switching to a terminal."""
        if not window_id:
            return

        if self._is_native_mode():
            backend = await self._ensure_native_backend()
            if backend:
                success = await backend.focus_tab(window_id, steal_focus=True)
                if not success:
                    self.app.notify(
                        "Failed to switch terminal", title="Terminal", severity="error"
                    )
        else:
            if not tmux_manager.select_inner_window(window_id):
                self.app.notify("Failed to switch terminal", title="Terminal", severity="error")
            else:
                # Move cursor focus to the right pane (terminal area)
                tmux_manager.focus_right_pane()
            # Clear attention when user clicks on terminal
            tmux_manager.clear_attention(window_id)

        self._expanded_window_id = None
        await self.refresh_data()

    async def _handle_close(self, window_id: str) -> None:
        """Handle closing a terminal."""
        if not window_id:
            return

        if self._is_native_mode():
            backend = await self._ensure_native_backend()
            if backend:
                success = await backend.close_tab(window_id)
                if not success:
                    self.app.notify(
                        "Failed to close terminal", title="Terminal", severity="error"
                    )
        else:
            if not tmux_manager.kill_inner_window(window_id):
                self.app.notify("Failed to close terminal", title="Terminal", severity="error")

        await self.refresh_data()

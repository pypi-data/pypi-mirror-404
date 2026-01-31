"""tmux integration for the Aline dashboard.

This is an optional runtime dependency:
- If tmux isn't installed, the dashboard runs normally without terminal controls.
- If tmux is installed, `aline dashboard` can bootstrap into a managed tmux session.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
import traceback
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from ..logging_config import setup_logger

logger = setup_logger("realign.dashboard.tmux", "dashboard.log")

OUTER_SESSION = "aline"
OUTER_WINDOW = "dashboard"
OUTER_SOCKET = "aline_dash"
INNER_SOCKET = "aline_term"
INNER_SESSION = "term"
MANAGED_ENV = "ALINE_TMUX_MANAGED"
ENV_TERMINAL_ID = "ALINE_TERMINAL_ID"
ENV_TERMINAL_PROVIDER = "ALINE_TERMINAL_PROVIDER"
ENV_INNER_SOCKET = "ALINE_INNER_TMUX_SOCKET"
ENV_INNER_SESSION = "ALINE_INNER_TMUX_SESSION"
ENV_CONTEXT_ID = "ALINE_CONTEXT_ID"

OPT_TERMINAL_ID = "@aline_terminal_id"
OPT_PROVIDER = "@aline_provider"
OPT_SESSION_TYPE = "@aline_session_type"
OPT_SESSION_ID = "@aline_session_id"
OPT_TRANSCRIPT_PATH = "@aline_transcript_path"
OPT_CONTEXT_ID = "@aline_context_id"
OPT_ATTENTION = "@aline_attention"
OPT_CREATED_AT = "@aline_created_at"
OPT_NO_TRACK = "@aline_no_track"


@dataclass(frozen=True)
class InnerWindow:
    window_id: str
    window_name: str
    active: bool
    terminal_id: str | None = None
    provider: str | None = None
    session_type: str | None = None
    session_id: str | None = None
    transcript_path: str | None = None
    context_id: str | None = None
    attention: str | None = None  # "permission_request", "stop", or None
    created_at: float | None = None  # Unix timestamp when window was created
    no_track: bool = False  # Whether tracking is disabled for this terminal


def tmux_available() -> bool:
    return shutil.which("tmux") is not None


def in_tmux() -> bool:
    return bool(os.environ.get("TMUX"))


def managed_env_enabled() -> bool:
    return os.environ.get(MANAGED_ENV) == "1"


_TMUX_VERSION_RE = re.compile(r"tmux\s+(\d+)\.(\d+)")
_TMUX_NO_SERVER_RE = re.compile(r"no server running on\s+(.+)$", re.MULTILINE)


def tmux_version() -> tuple[int, int] | None:
    if not tmux_available():
        return None
    try:
        proc = subprocess.run(["tmux", "-V"], text=True, capture_output=True, check=False)
    except OSError:
        return None
    match = _TMUX_VERSION_RE.search((proc.stdout or "") + " " + (proc.stderr or ""))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _run_tmux(args: Sequence[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["tmux", *args],
        text=True,
        capture_output=capture,
        check=False,
    )


def _run_outer_tmux(
    args: Sequence[str], *, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run tmux commands against the dedicated outer server socket."""
    return _run_tmux(["-L", OUTER_SOCKET, *args], capture=capture)


def _run_inner_tmux(
    args: Sequence[str], *, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    return _run_tmux(["-L", INNER_SOCKET, *args], capture=capture)


def _python_dashboard_command() -> str:
    # Use the current interpreter for predictable environments (venv, editable installs).
    python_cmd = shlex.join(
        [
            sys.executable,
            "-c",
            "from realign.dashboard.app import run_dashboard; run_dashboard()",
        ]
    )
    return f"{MANAGED_ENV}=1 {python_cmd}"


def _parse_lines(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if line.strip()]


def _unique_name(existing: Iterable[str], base: str) -> str:
    if base not in existing:
        return base
    idx = 2
    while f"{base}-{idx}" in existing:
        idx += 1
    return f"{base}-{idx}"


def zsh_run_and_keep_open(command: str) -> str:
    """Run a command via zsh login shell, then keep an interactive shell open."""
    shell = os.environ.get("SHELL", "zsh")
    if not shell.endswith("zsh"):
        shell = "zsh"
    script = f"{command}; exec {shell} -l"
    return shlex.join([shell, "-lc", script])


def new_terminal_id() -> str:
    return str(uuid.uuid4())


def new_context_id(prefix: str = "cc") -> str:
    """Create a short, random context id suitable for ALINE_CONTEXT_ID."""
    safe_prefix = re.sub(r"[^a-zA-Z0-9_-]+", "-", (prefix or "").strip()).strip("-_") or "ctx"
    return f"{safe_prefix}-{uuid.uuid4().hex[:12]}"


def shell_command_with_env(command: str, env: dict[str, str]) -> str:
    if not env:
        return command
    # Important: callers often pass compound shell commands like `cd ... && zsh -lc ...`.
    # `VAR=... cd ... && ...` only applies VAR to the first command (`cd`) in POSIX sh.
    # Wrap in a subshell so env vars apply to the entire script.
    assignments = " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items())
    return f"env {assignments} sh -lc {shlex.quote(command)}"


_SESSION_ID_FROM_TRANSCRIPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{7,}$")


def _session_id_from_transcript_path(transcript_path: str | None) -> str | None:
    raw = (transcript_path or "").strip()
    if not raw:
        return None
    try:
        path = Path(raw)
    except Exception:
        return None
    if path.suffix != ".jsonl":
        return None
    stem = (path.stem or "").strip()
    if not stem:
        return None
    # Heuristic guard: avoid overwriting with generic filenames like "transcript.jsonl".
    if not _SESSION_ID_FROM_TRANSCRIPT_RE.fullmatch(stem):
        return None
    if not any(ch.isdigit() for ch in stem):
        return None
    return stem


def _load_terminal_state_from_db() -> dict[str, dict[str, str]]:
    """Load terminal state from database (best-effort)."""
    import time as _time
    t0 = _time.time()
    try:
        from ..db import get_database

        t1 = _time.time()
        db = get_database(read_only=True)
        logger.info(f"[PERF] _load_terminal_state_from_db get_database: {_time.time() - t1:.3f}s")
        t2 = _time.time()
        agents = db.list_agents(status="active", limit=100)
        logger.info(f"[PERF] _load_terminal_state_from_db list_agents: {_time.time() - t2:.3f}s")

        out: dict[str, dict[str, str]] = {}
        for agent in agents:
            data: dict[str, str] = {}
            if agent.provider:
                data["provider"] = agent.provider
            if agent.session_type:
                data["session_type"] = agent.session_type
            if agent.session_id:
                data["session_id"] = agent.session_id
            if agent.transcript_path:
                data["transcript_path"] = agent.transcript_path
            if agent.cwd:
                data["cwd"] = agent.cwd
            if agent.project_dir:
                data["project_dir"] = agent.project_dir
            if agent.source:
                data["source"] = agent.source
            if agent.context_id:
                data["context_id"] = agent.context_id
            if agent.attention:
                data["attention"] = agent.attention
            out[agent.id] = data
        return out
    except Exception:
        return {}


def _load_terminal_state_from_json() -> dict[str, dict[str, str]]:
    """Load terminal state from JSON file (fallback)."""
    try:
        path = Path.home() / ".aline" / "terminal.json"
        if not path.exists():
            return {}
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        terminals = payload.get("terminals", {}) if isinstance(payload, dict) else {}
        if not isinstance(terminals, dict):
            return {}
        out: dict[str, dict[str, str]] = {}
        for terminal_id, data in terminals.items():
            if isinstance(terminal_id, str) and isinstance(data, dict):
                out[terminal_id] = {str(k): str(v) for k, v in data.items() if v is not None}
        return out
    except Exception:
        return {}


def _load_terminal_state() -> dict[str, dict[str, str]]:
    """Load terminal state.

    Priority:
    1. SQLite database (primary storage, V15+)
    2. ~/.aline/terminal.json (fallback for backward compatibility)

    Merges both sources, with DB taking precedence.
    """
    # Phase 1: Load from database
    db_state = _load_terminal_state_from_db()

    # Phase 2: Load from JSON as fallback
    json_state = _load_terminal_state_from_json()

    # Merge: DB takes precedence, JSON provides fallback for entries not in DB
    result = dict(json_state)
    result.update(db_state)

    return result


def _aline_tmux_conf_path() -> Path:
    return Path.home() / ".aline" / "tmux" / "tmux.conf"


def _source_aline_tmux_config(run_fn) -> None:  # type: ignore[no-untyped-def]
    """Best-effort source ~/.aline/tmux/tmux.conf if present."""
    try:
        # Ensure the config exists and is parseable.
        # Users may run `aline dashboard` before `aline init`, or have older auto-generated configs
        # that included unquoted `#` bindings (tmux treats `#` as a comment delimiter).
        try:
            from ..commands.init import _initialize_tmux_config

            conf = _initialize_tmux_config()
        except Exception:
            conf = _aline_tmux_conf_path()

        if conf.exists():
            run_fn(["source-file", str(conf)])
    except Exception:
        return


_DID_WARN_AUTOMATION = False


def _warn_automation_blocked(*, terminal_app: str, detail: str | None = None) -> None:
    """Best-effort hint when macOS Automation blocks AppleScript."""
    global _DID_WARN_AUTOMATION
    if _DID_WARN_AUTOMATION:
        return
    _DID_WARN_AUTOMATION = True

    msg = (
        "[aline] Unable to auto-maximize terminal window: macOS Automation permission likely "
        f"blocked AppleScript for {terminal_app}.\n"
        "Enable it at System Settings → Privacy & Security → Automation, then allow "
        f"your terminal (or osascript) to control {terminal_app}.\n"
    )
    if detail:
        msg += f"Detail: {detail.strip()}\n"
    try:
        sys.stderr.write(msg)
    except Exception:
        pass


def _terminal_app_from_env() -> str | None:
    """Detect the hosting terminal via common environment variables (no Automation needed)."""
    term_program = (os.environ.get("TERM_PROGRAM") or "").strip()
    if term_program in {"Apple_Terminal", "Terminal.app"}:
        return "Terminal"
    if term_program in {"iTerm.app", "iTerm2"} or term_program.startswith("iTerm"):
        return "iTerm2"
    return None


def _terminal_app_from_system_events() -> str | None:
    """Detect the frontmost app via System Events (may require Automation permission)."""
    try:
        detect_result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to name of first application process whose frontmost is true',
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except Exception:
        return None

    stderr = (detect_result.stderr or "").strip()
    if detect_result.returncode != 0 and stderr:
        _warn_automation_blocked(terminal_app="System Events", detail=stderr)
        return None

    front_app = (detect_result.stdout or "").strip()
    return front_app or None


def _maximize_terminal_window() -> None:
    """Maximize the current terminal window (non-fullscreen) on macOS.

    Uses AppleScript to set the window to zoomed state, which fills the screen
    but keeps the title bar and menu bar visible.
    """
    if sys.platform != "darwin":
        return

    try:
        front_app = _terminal_app_from_env() or _terminal_app_from_system_events() or ""

        if front_app == "Terminal":
            proc = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "Terminal" to set zoomed of front window to true',
                ],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if proc.returncode != 0 and (proc.stderr or "").strip():
                _warn_automation_blocked(terminal_app="Terminal", detail=proc.stderr)
        elif front_app == "iTerm2":
            # iTerm2: get screen size and set window bounds
            script = (
                'tell application "iTerm2" to tell current window to '
                'set bounds to {0, 25, (do shell script "system_profiler SPDisplaysDataType | '
                "awk '/Resolution/{print $2; exit}'\") as integer, "
                '(do shell script "system_profiler SPDisplaysDataType | '
                "awk '/Resolution/{print $4; exit}'\") as integer}"
            )
            proc = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if proc.returncode != 0 and (proc.stderr or "").strip():
                _warn_automation_blocked(terminal_app="iTerm2", detail=proc.stderr)
    except Exception:
        pass  # Best-effort; don't fail if this doesn't work


def _cleanup_stale_tmux_socket(stderr: str) -> bool:
    """Remove a stale tmux socket when the server is gone (best-effort)."""
    match = _TMUX_NO_SERVER_RE.search(stderr or "")
    if not match:
        return False
    path = match.group(1).strip()
    if not path:
        return False
    try:
        st = os.stat(path)
        if not stat.S_ISSOCK(st.st_mode):
            return False
        os.unlink(path)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def bootstrap_dashboard_into_tmux() -> None:
    """Ensure a managed tmux session exists, then attach to it.

    This is intended to be called when *not* already inside tmux.
    """
    logger.debug("bootstrap_dashboard_into_tmux() started")
    if in_tmux():
        logger.debug("Already in tmux, skipping bootstrap")
        return
    if not tmux_available():
        logger.debug("tmux not available, skipping bootstrap")
        return

    # Maximize terminal window before attaching to tmux
    _maximize_terminal_window()
    logger.debug("Terminal window maximized")

    # Ensure session exists.
    has = _run_outer_tmux(["has-session", "-t", OUTER_SESSION], capture=True)
    if has.returncode != 0:
        created = _run_outer_tmux(
            ["new-session", "-d", "-s", OUTER_SESSION, "-n", OUTER_WINDOW],
            capture=True,
        )
        if created.returncode != 0 and _cleanup_stale_tmux_socket(
            (created.stderr or "") + "\n" + (has.stderr or "")
        ):
            created = _run_outer_tmux(
                ["new-session", "-d", "-s", OUTER_SESSION, "-n", OUTER_WINDOW],
                capture=True,
            )
        if created.returncode != 0:
            detail = (created.stderr or created.stdout or "").strip()
            if detail:
                sys.stderr.write(f"[aline] tmux bootstrap failed: {detail}\n")
            return

    # Load Aline tmux config (clipboard bindings, etc.) into this dedicated server.
    _source_aline_tmux_config(_run_outer_tmux)

    # Enable mouse for the managed session only.
    _run_outer_tmux(["set-option", "-t", OUTER_SESSION, "mouse", "on"])

    # Disable status bar for cleaner UI (Aline sessions only).
    _run_outer_tmux(["set-option", "-t", OUTER_SESSION, "status", "off"])

    # Pane border styling - use double lines for wider, more visible borders.
    # This helps users identify the resizable border area more easily and reduces
    # accidental drag-to-resize when trying to select text near the border.
    _run_outer_tmux(["set-option", "-t", OUTER_SESSION, "pane-border-lines", "double"])
    _run_outer_tmux(["set-option", "-t", OUTER_SESSION, "pane-border-style", "fg=brightblack"])
    _run_outer_tmux(["set-option", "-t", OUTER_SESSION, "pane-active-border-style", "fg=blue"])
    _run_outer_tmux(["set-option", "-t", OUTER_SESSION, "pane-border-indicators", "arrows"])

    # Ensure dashboard window exists.
    windows_out = (
        _run_outer_tmux(
            ["list-windows", "-t", OUTER_SESSION, "-F", "#{window_name}"], capture=True
        ).stdout
        or ""
    )
    windows = set(_parse_lines(windows_out))
    if OUTER_WINDOW not in windows:
        _run_outer_tmux(["new-window", "-t", OUTER_SESSION, "-n", OUTER_WINDOW])

    # (Re)spawn the dashboard app in the left pane only; keep any right-side pane intact.
    _run_outer_tmux(
        [
            "respawn-pane",
            "-k",
            "-t",
            f"{OUTER_SESSION}:{OUTER_WINDOW}.0",
            _python_dashboard_command(),
        ]
    )
    _run_outer_tmux(["select-window", "-t", f"{OUTER_SESSION}:{OUTER_WINDOW}"])

    # Sanity-check before exec'ing into tmux attach. If this fails, fall back to non-tmux mode.
    ready = _run_outer_tmux(["has-session", "-t", OUTER_SESSION], capture=True)
    if ready.returncode != 0:
        detail = (ready.stderr or ready.stdout or "").strip()
        if detail:
            sys.stderr.write(f"[aline] tmux attach skipped: {detail}\n")
        return

    os.execvp("tmux", ["tmux", "-L", OUTER_SOCKET, "attach", "-t", OUTER_SESSION])


_inner_session_configured = False


def ensure_inner_session() -> bool:
    """Ensure the inner tmux server/session exists (returns True on success).

    The full configuration (mouse, status bar, border styles, home window setup) is
    only applied once per process lifetime.  Subsequent calls just verify the session
    is still alive via a cheap ``has-session`` check.
    """
    global _inner_session_configured

    if not (tmux_available() and in_tmux() and managed_env_enabled()):
        return False

    if _run_inner_tmux(["has-session", "-t", INNER_SESSION]).returncode != 0:
        # Create a stable "home" window so user-created terminals can use names like "zsh"
        # without always becoming "zsh-2".
        if (
            _run_inner_tmux(["new-session", "-d", "-s", INNER_SESSION, "-n", "home"]).returncode
            != 0
        ):
            return False
        # Force re-configuration after creating a new session.
        _inner_session_configured = False

    if _inner_session_configured:
        return True

    # --- One-time configuration below ---

    # Ensure the default/home window stays named "home" (tmux auto-rename would otherwise
    # change it to "zsh"/"opencode" depending on the last foreground command).
    try:
        _ensure_inner_home_window()
    except Exception:
        pass

    # Dedicated inner server; safe to enable mouse globally there.
    _run_inner_tmux(["set-option", "-g", "mouse", "on"])

    # Disable status bar for cleaner UI.
    _run_inner_tmux(["set-option", "-t", INNER_SESSION, "status", "off"])

    # Pane border styling - use double lines for wider, more visible borders.
    # This helps users identify the resizable border area more easily and reduces
    # accidental drag-to-resize when trying to select text near the border.
    _run_inner_tmux(["set-option", "-g", "pane-border-lines", "double"])
    _run_inner_tmux(["set-option", "-g", "pane-border-style", "fg=brightblack"])
    _run_inner_tmux(["set-option", "-g", "pane-active-border-style", "fg=blue"])
    _run_inner_tmux(["set-option", "-g", "pane-border-indicators", "arrows"])

    _source_aline_tmux_config(_run_inner_tmux)

    _inner_session_configured = True
    return True


def _ensure_inner_home_window() -> None:
    """Ensure the inner session has a reserved, non-renaming 'home' window (best-effort)."""
    if _run_inner_tmux(["has-session", "-t", INNER_SESSION]).returncode != 0:
        return

    out = (
        _run_inner_tmux(
            [
                "list-windows",
                "-t",
                INNER_SESSION,
                "-F",
                "#{window_id}\t#{window_index}\t#{window_name}\t#{"
                + OPT_TERMINAL_ID
                + "}\t#{"
                + OPT_PROVIDER
                + "}\t#{"
                + OPT_SESSION_TYPE
                + "}\t#{"
                + OPT_CONTEXT_ID
                + "}\t#{"
                + OPT_CREATED_AT
                + "}\t#{"
                + OPT_NO_TRACK
                + "}",
            ],
            capture=True,
        ).stdout
        or ""
    )

    candidates: list[tuple[str, int, str, str, str, str, str, str, str]] = []
    for line in _parse_lines(out):
        parts = (line.split("\t", 8) + [""] * 9)[:9]
        window_id = parts[0]
        try:
            window_index = int(parts[1])
        except Exception:
            window_index = 9999
        window_name = parts[2]
        terminal_id = parts[3]
        provider = parts[4]
        session_type = parts[5]
        context_id = parts[6]
        created_at = parts[7]
        no_track = parts[8]

        # Pick an unmanaged window (the default one created by `new-session`) as "home".
        unmanaged = (
            not (terminal_id or "").strip()
            and not (provider or "").strip()
            and not (session_type or "").strip()
            and not (context_id or "").strip()
            and not (created_at or "").strip()
        )
        if unmanaged:
            candidates.append(
                (
                    window_id,
                    window_index,
                    window_name,
                    terminal_id,
                    provider,
                    session_type,
                    context_id,
                    created_at,
                    no_track,
                )
            )

    if not candidates:
        return

    # Prefer the first window (index 0) if present.
    candidates.sort(key=lambda t: t[1])
    window_id = candidates[0][0]

    # Rename to "home" and prevent tmux auto-renaming it based on foreground command.
    _run_inner_tmux(["rename-window", "-t", window_id, "home"])
    _run_inner_tmux(["set-option", "-w", "-t", window_id, "automatic-rename", "off"])
    _run_inner_tmux(["set-option", "-w", "-t", window_id, "allow-rename", "off"])

    # Mark as internal/no-track so UI can hide it.
    # NOTE: We use _run_inner_tmux directly here instead of set_inner_window_options
    # to avoid recursion: set_inner_window_options → ensure_inner_session →
    # _ensure_inner_home_window → set_inner_window_options.
    try:
        _run_inner_tmux(["set-option", "-w", "-t", window_id, OPT_NO_TRACK, "1"])
        _run_inner_tmux(["set-option", "-w", "-t", window_id, OPT_CREATED_AT, str(time.time())])
    except Exception:
        pass


def ensure_right_pane(width_percent: int = 50) -> bool:
    """Create the right-side pane (terminal area) if it doesn't exist.

    Returns True if the pane exists/was created successfully.
    """
    if not ensure_inner_session():
        return False

    panes_out = (
        _run_tmux(
            [
                "list-panes",
                "-t",
                f"{OUTER_SESSION}:{OUTER_WINDOW}",
                "-F",
                "#{pane_index}",
            ],
            capture=True,
        ).stdout
        or ""
    )
    panes = _parse_lines(panes_out)
    if len(panes) >= 2:
        return True

    # Split from the dashboard pane to keep it on the left.
    attach_cmd = shlex.join(["tmux", "-L", INNER_SOCKET, "attach", "-t", INNER_SESSION])
    split = _run_tmux(
        [
            "split-window",
            "-h",
            "-p",
            str(int(width_percent)),
            "-t",
            f"{OUTER_SESSION}:{OUTER_WINDOW}.0",
            "-d",
            attach_cmd,
        ]
    )
    return split.returncode == 0


def list_inner_windows() -> list[InnerWindow]:
    import time as _time
    t0 = _time.time()
    if not ensure_inner_session():
        return []
    logger.info(f"[PERF] list_inner_windows ensure_inner_session: {_time.time() - t0:.3f}s")
    t1 = _time.time()
    state = _load_terminal_state()
    logger.info(f"[PERF] list_inner_windows _load_terminal_state: {_time.time() - t1:.3f}s")
    out = (
        _run_inner_tmux(
            [
                "list-windows",
                "-t",
                INNER_SESSION,
                "-F",
                "#{window_id}\t#{window_name}\t#{window_active}\t#{"
                + OPT_TERMINAL_ID
                + "}\t#{"
                + OPT_PROVIDER
                + "}\t#{"
                + OPT_SESSION_TYPE
                + "}\t#{"
                + OPT_SESSION_ID
                + "}\t#{"
                + OPT_TRANSCRIPT_PATH
                + "}\t#{"
                + OPT_CONTEXT_ID
                + "}\t#{"
                + OPT_ATTENTION
                + "}\t#{"
                + OPT_CREATED_AT
                + "}\t#{"
                + OPT_NO_TRACK
                + "}",
            ],
            capture=True,
        ).stdout
        or ""
    )
    windows: list[InnerWindow] = []
    for line in _parse_lines(out):
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        window_id = parts[0]
        window_name = parts[1]
        active = parts[2] == "1"
        terminal_id = parts[3] if len(parts) > 3 and parts[3] else None
        provider = parts[4] if len(parts) > 4 and parts[4] else None
        session_type = parts[5] if len(parts) > 5 and parts[5] else None
        session_id = parts[6] if len(parts) > 6 and parts[6] else None
        transcript_path = parts[7] if len(parts) > 7 and parts[7] else None
        context_id = parts[8] if len(parts) > 8 and parts[8] else None
        attention = parts[9] if len(parts) > 9 and parts[9] else None
        created_at_str = parts[10] if len(parts) > 10 and parts[10] else None
        created_at: float | None = None
        if created_at_str:
            try:
                created_at = float(created_at_str)
            except ValueError:
                pass
        no_track_str = parts[11] if len(parts) > 11 and parts[11] else None
        no_track = no_track_str == "1"

        if terminal_id:
            persisted = state.get(terminal_id) or {}
            if not provider:
                provider = persisted.get("provider") or provider
            if not session_type:
                session_type = persisted.get("session_type") or session_type
            if not session_id:
                session_id = persisted.get("session_id") or session_id
            if not transcript_path:
                transcript_path = persisted.get("transcript_path") or transcript_path
            if not context_id:
                context_id = persisted.get("context_id") or context_id

        transcript_session_id = _session_id_from_transcript_path(transcript_path)
        if transcript_session_id:
            session_id = transcript_session_id

        windows.append(
            InnerWindow(
                window_id=window_id,
                window_name=window_name,
                active=active,
                terminal_id=terminal_id,
                provider=provider,
                session_type=session_type,
                session_id=session_id,
                transcript_path=transcript_path,
                context_id=context_id,
                attention=attention,
                created_at=created_at,
                no_track=no_track,
            )
        )
    # Sort by creation time (newest first). Windows without created_at go to the bottom.
    windows.sort(key=lambda w: w.created_at if w.created_at is not None else 0, reverse=True)
    return windows


def set_inner_window_options(window_id: str, options: dict[str, str]) -> bool:
    import time as _time
    if not ensure_inner_session():
        return False
    ok = True
    for key, value in options.items():
        t0 = _time.time()
        # Important: these are per-window (not session-wide) to avoid cross-tab clobbering.
        if _run_inner_tmux(["set-option", "-w", "-t", window_id, key, value]).returncode != 0:
            ok = False
        logger.info(f"[PERF] set_inner_window_options {key}: {_time.time() - t0:.3f}s")
    return ok


def kill_inner_window(window_id: str) -> bool:
    if not ensure_inner_session():
        return False
    return _run_inner_tmux(["kill-window", "-t", window_id]).returncode == 0


def create_inner_window(
    base_name: str,
    command: str,
    *,
    terminal_id: str | None = None,
    provider: str | None = None,
    context_id: str | None = None,
    no_track: bool = False,
) -> InnerWindow | None:
    import time as _time
    t0 = _time.time()
    logger.info(f"[PERF] create_inner_window START")
    if not ensure_right_pane():
        return None
    logger.info(f"[PERF] create_inner_window ensure_right_pane: {_time.time() - t0:.3f}s")

    t1 = _time.time()
    existing = list_inner_windows()
    logger.info(f"[PERF] create_inner_window list_inner_windows: {_time.time() - t1:.3f}s")
    name = _unique_name((w.window_name for w in existing), base_name)

    # Record creation time before creating the window
    created_at = time.time()

    t2 = _time.time()
    proc = _run_inner_tmux(
        [
            "new-window",
            "-P",
            "-F",
            "#{window_id}\t#{window_name}",
            "-t",
            INNER_SESSION,
            "-n",
            name,
            command,
        ],
        capture=True,
    )
    logger.info(f"[PERF] create_inner_window new-window: {_time.time() - t2:.3f}s")
    if proc.returncode != 0:
        return None

    created = _parse_lines(proc.stdout or "")
    if not created:
        return None
    window_id, window_name = (created[0].split("\t", 1) + [""])[:2]

    # Always set options including the creation timestamp
    opts: dict[str, str] = {OPT_CREATED_AT: str(created_at)}
    if terminal_id:
        opts[OPT_TERMINAL_ID] = terminal_id
    if provider:
        opts[OPT_PROVIDER] = provider
    if context_id:
        opts[OPT_CONTEXT_ID] = context_id
    opts.setdefault(OPT_SESSION_TYPE, "")
    opts.setdefault(OPT_SESSION_ID, "")
    opts.setdefault(OPT_TRANSCRIPT_PATH, "")
    if no_track:
        opts[OPT_NO_TRACK] = "1"
    else:
        opts.setdefault(OPT_NO_TRACK, "")
    t3 = _time.time()
    set_inner_window_options(window_id, opts)
    logger.info(f"[PERF] create_inner_window set_options: {_time.time() - t3:.3f}s")

    _run_inner_tmux(["select-window", "-t", window_id])

    return InnerWindow(
        window_id=window_id,
        window_name=window_name or name,
        active=True,
        terminal_id=terminal_id,
        provider=provider,
        context_id=context_id,
        created_at=created_at,
    )


def select_inner_window(window_id: str) -> bool:
    if not ensure_right_pane():
        return False
    return _run_inner_tmux(["select-window", "-t", window_id]).returncode == 0


def focus_right_pane() -> bool:
    """Focus the right pane (terminal area) in the outer tmux layout."""
    return (
        _run_outer_tmux(
            ["select-pane", "-t", f"{OUTER_SESSION}:{OUTER_WINDOW}.1"]
        ).returncode
        == 0
    )


def clear_attention(window_id: str) -> bool:
    """Clear the attention state for a window (e.g., after user acknowledges permission request)."""
    if not ensure_inner_session():
        return False
    return _run_inner_tmux(["set-option", "-w", "-t", window_id, OPT_ATTENTION, ""]).returncode == 0


def get_active_claude_context_id() -> str | None:
    """Return the active inner tmux window's Claude ALINE_CONTEXT_ID (if any)."""
    return get_active_context_id(allowed_providers={"claude"})


def get_active_codex_context_id() -> str | None:
    """Return the active inner tmux window's Codex ALINE_CONTEXT_ID (if any)."""
    return get_active_context_id(allowed_providers={"codex"})


def get_active_context_id(*, allowed_providers: set[str] | None = None) -> str | None:
    """Return the active inner tmux window's ALINE_CONTEXT_ID (optionally filtered by provider)."""
    try:
        windows = list_inner_windows()
    except Exception:
        return None

    active = next((w for w in windows if w.active), None)
    if active is None:
        return None

    if allowed_providers is not None:
        allowed = {str(p).strip() for p in allowed_providers if str(p).strip()}
        provider = (active.provider or "").strip()
        session_type = (active.session_type or "").strip()
        if provider not in allowed and session_type not in allowed:
            return None

    context_id = (active.context_id or "").strip()
    return context_id or None

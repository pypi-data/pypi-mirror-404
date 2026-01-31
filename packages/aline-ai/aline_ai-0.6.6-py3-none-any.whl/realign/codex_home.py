"""Codex home/session path helpers.

We isolate Codex storage via `CODEX_HOME` so the watcher can infer ownership
from the session file path. By default it's per-terminal, but when an
ALINE_AGENT_ID is present we can scope CODEX_HOME per agent.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


ENV_CODEX_HOME = "CODEX_HOME"
AGENT_HOME_PREFIX = "agent-"


def aline_codex_homes_dir() -> Path:
    override = os.environ.get("ALINE_CODEX_HOMES_DIR", "").strip()
    if override:
        return Path(os.path.expanduser(override))
    return Path.home() / ".aline" / "codex_homes"


def _safe_id(raw_id: str) -> str:
    return (raw_id or "").strip().replace("/", "_").replace("\\", "_")


def codex_home_for_terminal(terminal_id: str) -> Path:
    tid = _safe_id(terminal_id)
    return aline_codex_homes_dir() / tid


def codex_home_for_agent(agent_id: str) -> Path:
    aid = _safe_id(agent_id)
    return aline_codex_homes_dir() / f"{AGENT_HOME_PREFIX}{aid}"


def codex_home_for_terminal_or_agent(terminal_id: str, agent_id: Optional[str]) -> Path:
    if agent_id:
        return codex_home_for_agent(agent_id)
    return codex_home_for_terminal(terminal_id)


def codex_sessions_dir_for_home(codex_home: Path) -> Path:
    return codex_home / "sessions"


def codex_sessions_dir_for_terminal(terminal_id: str) -> Path:
    return codex_sessions_dir_for_home(codex_home_for_terminal(terminal_id))


def codex_sessions_dir_for_terminal_or_agent(
    terminal_id: str, agent_id: Optional[str]
) -> Path:
    return codex_sessions_dir_for_home(codex_home_for_terminal_or_agent(terminal_id, agent_id))


def codex_home_owner_from_session_file(session_file: Path) -> Optional[tuple[str, str]]:
    """Return ("terminal", id) or ("agent", id) if session_file is under Aline-managed homes."""
    try:
        homes = aline_codex_homes_dir().resolve()
        p = session_file.resolve()
    except Exception:
        return None

    try:
        rel = p.relative_to(homes)
    except ValueError:
        return None

    parts = rel.parts
    if len(parts) < 3:
        return None
    owner = (parts[0] or "").strip()
    if not owner:
        return None
    if parts[1] != "sessions":
        return None
    if owner.startswith(AGENT_HOME_PREFIX):
        return ("agent", owner[len(AGENT_HOME_PREFIX) :])
    return ("terminal", owner)


def terminal_id_from_codex_session_file(session_file: Path) -> Optional[str]:
    """If session_file is under an Aline-managed CODEX_HOME, return terminal_id."""
    owner = codex_home_owner_from_session_file(session_file)
    if not owner:
        return None
    if owner[0] != "terminal":
        return None
    return owner[1]


def prepare_codex_home(terminal_id: str, *, agent_id: Optional[str] = None) -> Path:
    """Create/prepare an isolated CODEX_HOME (per-agent if agent_id is provided)."""
    home = codex_home_for_terminal_or_agent(terminal_id, agent_id)
    sessions = codex_sessions_dir_for_home(home)
    try:
        sessions.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # Keep Codex skills working under the isolated home by symlinking to the global skills dir.
    try:
        global_skills = Path.home() / ".codex" / "skills"
        if global_skills.exists():
            skills_link = home / "skills"
            if not skills_link.exists():
                skills_link.parent.mkdir(parents=True, exist_ok=True)
                skills_link.symlink_to(global_skills)
    except Exception:
        pass

    return home

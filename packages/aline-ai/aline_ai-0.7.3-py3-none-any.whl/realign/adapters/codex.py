"""
Codex Adapter

Handles session discovery and interaction for Codex CLI.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from .base import SessionAdapter
from ..triggers.codex_trigger import CodexTrigger
from ..codex_detector import find_codex_sessions_for_project


class CodexAdapter(SessionAdapter):
    """Adapter for Codex CLI sessions."""

    name = "codex"
    trigger_class = CodexTrigger

    def discover_sessions(self) -> List[Path]:
        """Find all Codex sessions."""
        sessions: list[Path] = []
        roots: list[Path] = []
        try:
            from ..codex_detector import _codex_session_roots  # type: ignore[attr-defined]

            roots = _codex_session_roots()
        except Exception:
            roots = [Path.home() / ".codex" / "sessions"]

        for root in roots:
            if not root.exists():
                continue
            try:
                sessions.extend(root.rglob("rollout-*.jsonl"))
            except Exception:
                continue

        return sessions

    def discover_sessions_for_project(self, project_path: Path) -> List[Path]:
        """Find sessions for a specific project."""
        return find_codex_sessions_for_project(project_path)

    def extract_project_path(self, session_file: Path) -> Optional[Path]:
        """Extract project path from Codex session file metadata."""
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                first_line = f.readline()
                if not first_line:
                    return None
                data = json.loads(first_line)
                if data.get("type") == "session_meta":
                    cwd = data.get("payload", {}).get("cwd")
                    if cwd:
                        return Path(cwd)
        except Exception:
            pass
        return None

    def is_session_valid(self, session_file: Path) -> bool:
        """Check if this is a Codex session file."""
        if not session_file.name.startswith("rollout-") or not session_file.name.endswith(".jsonl"):
            return False

        # Check first line for Codex signature
        return super().is_session_valid(session_file)

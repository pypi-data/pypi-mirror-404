"""Small persistence helpers for dashboard UI state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DASHBOARD_STATE_FILE = Path.home() / ".aline" / "dashboard_state.json"


def load_dashboard_state() -> dict[str, Any]:
    try:
        if not DASHBOARD_STATE_FILE.exists():
            return {}
        with open(DASHBOARD_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_dashboard_state(state: dict[str, Any]) -> None:
    try:
        DASHBOARD_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DASHBOARD_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        return


def get_dashboard_state_value(key: str, default: Any) -> Any:  # noqa: ANN401
    return load_dashboard_state().get(key, default)


def set_dashboard_state_value(key: str, value: Any) -> None:  # noqa: ANN401
    state = load_dashboard_state()
    state[key] = value
    save_dashboard_state(state)


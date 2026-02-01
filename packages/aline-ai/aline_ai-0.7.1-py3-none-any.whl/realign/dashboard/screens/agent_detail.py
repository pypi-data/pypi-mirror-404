"""Agent detail modal for the dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Static

from ..widgets.openable_table import OpenableDataTable


def _format_dt(dt: object) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if dt is None:
        return "-"
    return str(dt)


def _format_relative_time(dt: datetime) -> str:
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        mins = int(seconds / 60)
        return f"{mins}m ago"
    if seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    days = int(seconds / 86400)
    return f"{days}d ago"


def _format_iso_relative(dt: Optional[datetime]) -> str:
    if not dt:
        return "-"
    try:
        return _format_relative_time(dt)
    except Exception:
        return _format_dt(dt)


def _shorten_id(val: str | None) -> str:
    if not val:
        return "-"
    if len(val) <= 20:
        return val
    return f"{val[:8]}...{val[-8:]}"


class AgentDetailScreen(ModalScreen):
    """Modal that shows agent details and its sessions."""

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
    ]

    DEFAULT_CSS = """
    AgentDetailScreen {
        align: center middle;
    }

    AgentDetailScreen #agent-detail-root {
        width: 95%;
        height: 95%;
        padding: 1;
        background: $background;
        border: none;
    }

    AgentDetailScreen #agent-meta {
        height: auto;
        margin-bottom: 1;
    }

    AgentDetailScreen #agent-detail-body {
        height: 1fr;
    }

    AgentDetailScreen #agent-description {
        height: auto;
        margin-bottom: 1;
    }

    AgentDetailScreen #agent-sessions-table {
        width: 1fr;
        height: 1fr;
    }

    AgentDetailScreen #agent-session-preview {
        width: 1fr;
        height: auto;
        margin-top: 1;
    }

    AgentDetailScreen #agent-hint {
        height: 1;
        margin-top: 1;
        color: $text-muted;
        text-align: right;
    }
    """

    def __init__(self, agent_id: str) -> None:
        super().__init__()
        self.agent_id = agent_id
        self._load_error: Optional[str] = None
        self._agent_info = None
        self._sessions: list[dict] = []
        self._session_record_cache: dict[str, object] = {}
        self._initialized: bool = False

    def compose(self) -> ComposeResult:
        with Container(id="agent-detail-root"):
            yield Static(id="agent-meta")
            with Vertical(id="agent-detail-body"):
                yield Static(id="agent-description")
                sessions_table = OpenableDataTable(id="agent-sessions-table")
                sessions_table.add_columns(
                    "#",
                    "Session ID",
                    "Source",
                    "Project",
                    "Turns",
                    "Title",
                    "Last Activity",
                )
                sessions_table.cursor_type = "row"
                yield sessions_table
                yield Static(id="agent-session-preview")
            yield Static(
                "Click: select   Enter/dblclick: open   Esc: close",
                id="agent-hint",
            )

    def on_show(self) -> None:
        self.call_later(self._ensure_initialized)

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        sessions_table = self.query_one("#agent-sessions-table", DataTable)
        self._load_data()
        self._update_display()

        if sessions_table.row_count > 0:
            sessions_table.focus()

    def action_close(self) -> None:
        self.app.pop_screen()

    def on_openable_data_table_row_activated(
        self, event: OpenableDataTable.RowActivated
    ) -> None:
        if event.data_table.id != "agent-sessions-table":
            return

        session_id = str(event.row_key.value)
        if not session_id:
            return

        from .session_detail import SessionDetailScreen

        self.app.push_screen(SessionDetailScreen(session_id))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id != "agent-sessions-table":
            return
        self._update_session_preview(str(event.row_key.value))

    def _load_data(self) -> None:
        try:
            from ...db import get_database

            db = get_database()
            self._agent_info = db.get_agent_info(self.agent_id)
            sessions = db.get_sessions_by_agent_id(self.agent_id, limit=1000)

            source_map = {
                "claude": "Claude",
                "codex": "Codex",
                "gemini": "Gemini",
            }

            self._sessions = []
            for s in sessions:
                session_id = str(s.id)
                session_type = getattr(s, "session_type", None) or "unknown"
                workspace = getattr(s, "workspace_path", None)
                title = getattr(s, "session_title", None) or "(no title)"
                last_activity = getattr(s, "last_activity_at", None)
                turns = int(getattr(s, "total_turns", 0) or 0)

                project = str(workspace).split("/")[-1] if workspace else "-"
                source = source_map.get(session_type, session_type)

                self._sessions.append(
                    {
                        "id": session_id,
                        "short_id": _shorten_id(session_id),
                        "source": source,
                        "project": project,
                        "turns": turns,
                        "title": title,
                        "last_activity": last_activity,
                    }
                )

            self._sessions.sort(
                key=lambda item: item.get("last_activity") or datetime.min, reverse=True
            )
            self._load_error = None
        except Exception as e:
            self._agent_info = None
            self._sessions = []
            self._session_record_cache = {}
            self._load_error = str(e)

    def _update_display(self) -> None:
        meta = self.query_one("#agent-meta", Static)
        description = self.query_one("#agent-description", Static)
        preview = self.query_one("#agent-session-preview", Static)

        if self._load_error:
            meta.update(f"[red]Failed to load agent {self.agent_id}:[/red] {self._load_error}")
            description.update("")
            preview.update("")
            return

        name = getattr(self._agent_info, "name", None) if self._agent_info else None
        desc = getattr(self._agent_info, "description", None) if self._agent_info else None
        created_at = getattr(self._agent_info, "created_at", None) if self._agent_info else None
        updated_at = getattr(self._agent_info, "updated_at", None) if self._agent_info else None

        meta_lines = [
            f"[bold]Agent[/bold] {self.agent_id}",
            f"[dim]Name:[/dim] {escape(name) if name else '(no name)'}",
            f"[dim]Created:[/dim] {_format_dt(created_at)}    [dim]Updated:[/dim] {_format_dt(updated_at)}",
            f"[dim]Sessions:[/dim] {len(self._sessions)}",
        ]

        meta.update("\n".join(meta_lines))
        description.update(desc or "(no description)")
        preview.update("")

        table = self.query_one("#agent-sessions-table", DataTable)
        selected_session_id: Optional[str] = None
        try:
            if table.row_count > 0:
                selected_session_id = str(
                    table.coordinate_to_cell_key(table.cursor_coordinate)[0].value
                )
        except Exception:
            selected_session_id = None
        table.clear()

        for idx, s in enumerate(self._sessions, 1):
            title_cell = s["title"]
            if len(title_cell) > 40:
                title_cell = title_cell[:40] + "..."

            last_activity_str = _format_iso_relative(s["last_activity"])

            table.add_row(
                str(idx),
                s["short_id"],
                s["source"],
                s["project"],
                str(s["turns"]),
                title_cell,
                last_activity_str,
                key=s["id"],
            )

        if table.row_count > 0:
            if selected_session_id:
                try:
                    table.cursor_coordinate = (table.get_row_index(selected_session_id), 0)
                except Exception:
                    table.cursor_coordinate = (0, 0)
            else:
                table.cursor_coordinate = (0, 0)

            row_key = table.coordinate_to_cell_key(table.cursor_coordinate)[0]
            self._update_session_preview(str(row_key.value))

    def _get_session_record(self, session_id: str) -> Optional[object]:
        if session_id in self._session_record_cache:
            return self._session_record_cache[session_id]
        try:
            from ...db import get_database

            db = get_database()
            record = db.get_session_by_id(session_id)
            self._session_record_cache[session_id] = record
            return record
        except Exception:
            self._session_record_cache[session_id] = None
            return None

    def _update_session_preview(self, session_id: str) -> None:
        preview = self.query_one("#agent-session-preview", Static)
        if not session_id:
            preview.update("")
            return

        record = self._get_session_record(session_id)
        if not record:
            preview.update("[dim]No session details available.[/dim]")
            return

        title = getattr(record, "session_title", None) or "(no title)"
        summary = getattr(record, "session_summary", None) or "(no summary)"

        preview.update(
            "\n".join(
                [
                    f"[bold]Title:[/bold] {escape(title)}",
                    f"[bold]Summary:[/bold] {escape(summary)}",
                ]
            )
        )

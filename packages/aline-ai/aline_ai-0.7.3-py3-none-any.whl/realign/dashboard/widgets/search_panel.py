"""Search Panel Widget for searching sessions, events, and turns."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RadioButton, RadioSet, Static

from .openable_table import OpenableDataTable


class SearchPanel(Static):
    """Panel for searching Aline data."""

    DEFAULT_CSS = """
    SearchPanel {
        height: 100%;
        padding: 1;
    }

    SearchPanel .search-input-row {
        height: 3;
        margin-bottom: 1;
    }

    SearchPanel .search-input-row Input {
        width: 1fr;
    }

    SearchPanel .search-input-row Button {
        width: 12;
        margin-left: 1;
    }

    SearchPanel .search-options {
        height: 3;
        margin-bottom: 1;
    }

    SearchPanel RadioSet {
        layout: horizontal;
        height: 3;
    }

    SearchPanel .results-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }

    SearchPanel DataTable {
        height: 1fr;
    }

    SearchPanel .results-summary {
        height: 2;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._results: list = []
        self._search_type: str = "all"
        self._query: str = ""

    def compose(self) -> ComposeResult:
        """Compose the search panel layout."""
        with Horizontal(classes="search-input-row"):
            yield Input(id="search-input", placeholder="Enter search query (regex supported)...")
            yield Button("Search", id="search-btn", variant="primary")

        with Horizontal(classes="search-options"):
            yield Static("Search in: ")
            with RadioSet(id="search-type"):
                yield RadioButton("All", value=True, id="type-all")
                yield RadioButton("Events", id="type-event")
                yield RadioButton("Sessions", id="type-session")
                yield RadioButton("Turns", id="type-turn")

        yield Static("[bold]Results[/bold]", classes="results-title")
        yield OpenableDataTable(id="results-table")
        yield Static(id="results-summary", classes="results-summary")

    def on_mount(self) -> None:
        """Set up the panel on mount."""
        table = self.query_one("#results-table", OpenableDataTable)
        table.add_columns("Type", "ID", "Title/Content", "Context")
        table.cursor_type = "row"
        table.show_vertical_scrollbar = True

    def on_openable_data_table_row_activated(self, event: OpenableDataTable.RowActivated) -> None:
        """Open the selected result (Enter / double-click)."""
        if event.data_table.id != "results-table":
            return
        if event.cursor_row < 0 or event.cursor_row >= len(self._results):
            return

        result = self._results[event.cursor_row]
        result_type = result.get("type")

        from ..screens import EventDetailScreen, SessionDetailScreen

        if result_type == "Event":
            event_id = result.get("full_id") or ""
            if event_id:
                self.app.push_screen(EventDetailScreen(event_id))
            return

        if result_type == "Session":
            session_id = result.get("full_id") or ""
            if session_id:
                self.app.push_screen(SessionDetailScreen(session_id))
            return

        if result_type == "Turn":
            session_id = result.get("session_id") or ""
            turn_id = result.get("turn_id") or ""
            if session_id:
                self.app.push_screen(
                    SessionDetailScreen(session_id, initial_turn_id=turn_id or None)
                )
            return

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in search input."""
        if event.input.id == "search-input":
            self._perform_search()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "search-btn":
            self._perform_search()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle search type change."""
        button_id = event.pressed.id if event.pressed else "type-all"
        type_map = {
            "type-all": "all",
            "type-event": "event",
            "type-session": "session",
            "type-turn": "turn",
        }
        self._search_type = type_map.get(button_id, "all")

    def _perform_search(self) -> None:
        """Perform the search."""
        search_input = self.query_one("#search-input", Input)
        self._query = search_input.value.strip()

        if not self._query:
            self.app.notify("Please enter a search query", title="Search", severity="warning")
            return

        self._results = []
        try:
            from ...db import get_database

            db = get_database()

            # Search based on type
            if self._search_type in ("all", "event"):
                events = db.search_events(self._query, limit=20, use_regex=True, ignore_case=True)
                for event in events:
                    self._results.append(
                        {
                            "type": "Event",
                            "id": self._shorten_id(event.id),
                            "full_id": event.id,
                            "title": (event.title or "(no title)")[:60],
                            "context": event.event_type or "-",
                        }
                    )

            if self._search_type in ("all", "session"):
                sessions = db.search_sessions(
                    self._query, limit=20, use_regex=True, ignore_case=True
                )
                for session in sessions:
                    self._results.append(
                        {
                            "type": "Session",
                            "id": self._shorten_id(session.id),
                            "full_id": session.id,
                            "title": (session.session_title or "(no title)")[:60],
                            "context": session.session_type or "-",
                        }
                    )

            if self._search_type in ("all", "turn"):
                turns = db.search_conversations(
                    self._query, limit=20, use_regex=True, ignore_case=True
                )
                for turn in turns:
                    session_id = turn.get("session_id", "")
                    turn_id = turn.get("turn_id", "")
                    self._results.append(
                        {
                            "type": "Turn",
                            "id": self._shorten_id(turn_id),
                            "turn_id": turn_id,
                            "session_id": session_id,
                            "title": (turn.get("title") or turn.get("summary") or "(no title)")[
                                :60
                            ],
                            "context": f"{self._shorten_id(session_id)} • Turn #{turn.get('turn_number', '-')}",
                        }
                    )

            self._update_display()

        except Exception as e:
            self.app.notify(f"Search error: {e}", title="Search", severity="error")

    def _update_display(self) -> None:
        """Update the display with search results."""
        table = self.query_one("#results-table", OpenableDataTable)
        table.clear()

        for result in self._results:
            type_display = result["type"]
            if type_display == "Event":
                type_display = "[cyan]Event[/cyan]"
            elif type_display == "Session":
                type_display = "[magenta]Session[/magenta]"
            elif type_display == "Turn":
                type_display = "[green]Turn[/green]"

            table.add_row(
                type_display,
                result["id"],
                result["title"],
                result["context"],
            )

        # Update summary
        summary = self.query_one("#results-summary", Static)
        if self._query:
            event_count = sum(1 for r in self._results if r["type"] == "Event")
            session_count = sum(1 for r in self._results if r["type"] == "Session")
            turn_count = sum(1 for r in self._results if r["type"] == "Turn")

            summary_text = f"Found {len(self._results)} results for '{self._query}'"
            if self._search_type == "all":
                summary_text += (
                    f" (Events: {event_count}, Sessions: {session_count}, Turns: {turn_count})"
                )

            summary.update(f"[dim]{summary_text}[/dim]")
        else:
            summary.update("")

    def _shorten_id(self, id_str: str) -> str:
        """Shorten an ID for display."""
        if len(id_str) > 12:
            return id_str[:8] + "..."
        return id_str

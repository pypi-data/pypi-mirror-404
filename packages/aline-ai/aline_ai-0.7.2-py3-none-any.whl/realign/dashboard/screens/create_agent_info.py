"""Create agent info modal for the dashboard."""

from __future__ import annotations

import uuid
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static
from textual.worker import Worker, WorkerState

from ...logging_config import setup_logger

logger = setup_logger("realign.dashboard.screens.create_agent_info", "dashboard.log")


class CreateAgentInfoScreen(ModalScreen[Optional[dict]]):
    """Modal to create a new agent profile or import from a share link.

    Both options are shown together; the user picks one.
    Returns a dict with agent info on success, None on cancel.
    """

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
    ]

    DEFAULT_CSS = """
    CreateAgentInfoScreen {
        align: center middle;
    }

    CreateAgentInfoScreen #create-agent-info-root {
        width: 65;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: $background;
        border: solid $accent;
    }

    CreateAgentInfoScreen #create-agent-info-title {
        height: auto;
        margin-bottom: 1;
        text-style: bold;
    }

    CreateAgentInfoScreen .section-label {
        height: auto;
        margin-top: 1;
        margin-bottom: 0;
        color: $text-muted;
    }

    CreateAgentInfoScreen Input {
        margin-top: 0;
        border: none;
    }

    CreateAgentInfoScreen #or-separator {
        height: auto;
        margin-top: 1;
        margin-bottom: 0;
        text-align: center;
        color: $text-muted;
    }

    CreateAgentInfoScreen #import-status {
        height: auto;
        margin-top: 1;
        color: $text-muted;
    }

    CreateAgentInfoScreen #create-buttons {
        height: auto;
        margin-top: 1;
        align: right middle;
    }

    CreateAgentInfoScreen #import-buttons {
        height: auto;
        margin-top: 1;
        align: right middle;
    }

    CreateAgentInfoScreen #create-buttons Button {
        margin-left: 1;
    }

    CreateAgentInfoScreen #import-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._import_worker: Optional[Worker] = None
        from ...agent_names import generate_agent_name
        self._default_name: str = generate_agent_name()

    def compose(self) -> ComposeResult:
        with Container(id="create-agent-info-root"):
            yield Static("Create Agent Profile", id="create-agent-info-title")

            # --- Create New section ---
            yield Label("Name", classes="section-label")
            yield Input(placeholder=self._default_name, id="agent-name")

            with Horizontal(id="create-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Create", id="create", variant="primary")

            # --- Separator ---
            yield Static("-- Or --", id="or-separator")

            # --- Import from Link section ---
            yield Label("Import from Link", classes="section-label")
            yield Input(placeholder="https://realign-server.vercel.app/share/...", id="share-url")

            yield Label("Password (optional)", classes="section-label")
            yield Input(placeholder="Leave blank if not password-protected", id="share-password", password=True)

            yield Static("", id="import-status")

            with Horizontal(id="import-buttons"):
                yield Button("Import", id="import", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#agent-name", Input).focus()

    def action_close(self) -> None:
        self.dismiss(None)

    def _set_busy(self, busy: bool) -> None:
        self.query_one("#agent-name", Input).disabled = busy
        self.query_one("#share-url", Input).disabled = busy
        self.query_one("#share-password", Input).disabled = busy
        self.query_one("#create", Button).disabled = busy
        self.query_one("#cancel", Button).disabled = busy
        self.query_one("#import", Button).disabled = busy

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""

        if button_id == "cancel":
            self.dismiss(None)
            return

        if button_id == "create":
            await self._create_agent()
            return

        if button_id == "import":
            await self._import_agent()
            return

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key in input fields."""
        input_id = event.input.id or ""
        if input_id == "agent-name":
            await self._create_agent()
        elif input_id in ("share-url", "share-password"):
            await self._import_agent()

    async def _create_agent(self) -> None:
        """Create the agent profile."""
        try:
            from ...db import get_database

            name_input = self.query_one("#agent-name", Input).value.strip()
            name = name_input or self._default_name

            agent_id = str(uuid.uuid4())

            db = get_database(read_only=False)
            record = db.get_or_create_agent_info(agent_id, name=name)

            self.dismiss({
                "id": record.id,
                "name": record.name,
                "description": record.description or "",
            })
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            self.app.notify(f"Failed to create agent: {e}", severity="error")

    async def _import_agent(self) -> None:
        """Import an agent from a share link."""
        share_url = self.query_one("#share-url", Input).value.strip()
        password = self.query_one("#share-password", Input).value.strip() or None

        if not share_url:
            self.app.notify("Please enter a share URL", severity="warning")
            self.query_one("#share-url", Input).focus()
            return

        if "/share/" not in share_url:
            self.app.notify("Invalid share URL format", severity="warning")
            self.query_one("#share-url", Input).focus()
            return

        status = self.query_one("#import-status", Static)
        status.update("Importing...")
        self._set_busy(True)

        def do_import() -> dict:
            from ...commands.import_shares import import_agent_from_share

            return import_agent_from_share(share_url, password=password)

        self._import_worker = self.run_worker(do_import, thread=True, exit_on_error=False)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if self._import_worker is None or event.worker is not self._import_worker:
            return

        status = self.query_one("#import-status", Static)

        if event.state == WorkerState.ERROR:
            err = self._import_worker.error if self._import_worker else "Unknown error"
            status.update(f"Error: {err}")
            self._set_busy(False)
            return

        if event.state != WorkerState.SUCCESS:
            return

        result = self._import_worker.result if self._import_worker else {}
        if not result or not result.get("success"):
            error_msg = (result or {}).get("error", "Import failed")
            status.update(f"Error: {error_msg}")
            self._set_busy(False)
            return

        self.dismiss({
            "id": result["agent_id"],
            "name": result["agent_name"],
            "description": result.get("agent_description", ""),
            "imported": True,
            "sessions_imported": result.get("sessions_imported", 0),
        })

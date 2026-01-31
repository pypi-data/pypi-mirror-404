"""Create agent info modal for the dashboard."""

from __future__ import annotations

import uuid
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from ...logging_config import setup_logger

logger = setup_logger("realign.dashboard.screens.create_agent_info", "dashboard.log")


class CreateAgentInfoScreen(ModalScreen[Optional[dict]]):
    """Modal to create a new agent profile.

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
        width: 60;
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
        height: auto;
        margin-top: 0;
    }

    CreateAgentInfoScreen #buttons {
        height: auto;
        margin-top: 2;
        align: right middle;
    }

    CreateAgentInfoScreen #buttons Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="create-agent-info-root"):
            yield Static("Create Agent Profile", id="create-agent-info-title")

            yield Label("Name", classes="section-label")
            yield Input(placeholder="Agent name (leave blank for random)", id="agent-name")

            yield Label("Description", classes="section-label")
            yield Input(placeholder="Optional description", id="agent-description")

            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Create", id="create", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#agent-name", Input).focus()

    def action_close(self) -> None:
        self.dismiss(None)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""

        if button_id == "cancel":
            self.dismiss(None)
            return

        if button_id == "create":
            await self._create_agent()
            return

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key in input fields."""
        await self._create_agent()

    async def _create_agent(self) -> None:
        """Create the agent profile."""
        try:
            from ...agent_names import generate_agent_name
            from ...db import get_database

            name_input = self.query_one("#agent-name", Input).value.strip()
            description = self.query_one("#agent-description", Input).value.strip()

            # Generate random name if not provided
            name = name_input or generate_agent_name()

            agent_id = str(uuid.uuid4())

            db = get_database(read_only=False)
            record = db.get_or_create_agent_info(agent_id, name=name)
            if description:
                record = db.update_agent_info(agent_id, description=description)

            self.dismiss({
                "id": record.id,
                "name": record.name,
                "description": record.description or "",
            })
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            self.app.notify(f"Failed to create agent: {e}", severity="error")

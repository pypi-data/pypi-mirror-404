"""Create agent modal for the dashboard."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, RadioButton, RadioSet, Static


# State file for storing last workspace path
DASHBOARD_STATE_FILE = Path.home() / ".aline" / "dashboard_state.json"


def _load_last_workspace() -> str:
    """Load the last used workspace path from state file."""
    try:
        if DASHBOARD_STATE_FILE.exists():
            with open(DASHBOARD_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                path = state.get("last_workspace", "")
                if path and os.path.isdir(path):
                    return path
    except Exception:
        pass
    # Default to current working directory or home
    try:
        return os.getcwd()
    except Exception:
        return str(Path.home())


def _save_last_workspace(path: str) -> None:
    """Save the last used workspace path to state file."""
    _save_state("last_workspace", path)


def _load_claude_permission_mode() -> str:
    """Load the last used Claude permission mode from state file."""
    try:
        if DASHBOARD_STATE_FILE.exists():
            with open(DASHBOARD_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state.get("claude_permission_mode", "normal")
    except Exception:
        pass
    return "normal"


def _save_claude_permission_mode(mode: str) -> None:
    """Save the Claude permission mode to state file."""
    _save_state("claude_permission_mode", mode)


def _load_claude_tracking_mode() -> str:
    """Load the last used Claude tracking mode from state file."""
    try:
        if DASHBOARD_STATE_FILE.exists():
            with open(DASHBOARD_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state.get("claude_tracking_mode", "track")
    except Exception:
        pass
    return "track"


def _save_claude_tracking_mode(mode: str) -> None:
    """Save the Claude tracking mode to state file."""
    _save_state("claude_tracking_mode", mode)


def _save_state(key: str, value: str) -> None:
    """Save a key-value pair to the state file."""
    try:
        DASHBOARD_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        state = {}
        if DASHBOARD_STATE_FILE.exists():
            with open(DASHBOARD_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        state[key] = value
        with open(DASHBOARD_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


class CreateAgentScreen(ModalScreen[Optional[tuple[str, str, bool, bool]]]):
    """Modal to create a new agent terminal.

    Returns a tuple of (agent_type, workspace_path, skip_permissions, no_track) on success, None on cancel.
    """

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
    ]

    DEFAULT_CSS = """
    CreateAgentScreen {
        align: center middle;
    }

    CreateAgentScreen #create-agent-root {
        width: 60;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: $background;
        border: solid $accent;
    }

    CreateAgentScreen #create-agent-title {
        height: auto;
        margin-bottom: 1;
        text-style: bold;
    }

    CreateAgentScreen .section-label {
        height: auto;
        margin-top: 1;
        margin-bottom: 0;
        color: $text-muted;
    }

    CreateAgentScreen RadioSet {
        height: auto;
        margin: 0;
        padding: 0;
        border: none;
        background: transparent;
    }

    CreateAgentScreen RadioButton {
        height: auto;
        padding: 0;
        margin: 0;
        background: transparent;
    }

    CreateAgentScreen #workspace-section {
        height: auto;
        margin-top: 1;
    }

    CreateAgentScreen #claude-options {
        height: auto;
        margin-top: 1;
    }

    CreateAgentScreen #claude-options.hidden {
        display: none;
    }

    CreateAgentScreen #workspace-row {
        height: auto;
        margin-top: 0;
    }

    CreateAgentScreen #workspace-path {
        width: 1fr;
        height: auto;
        padding: 0 1;
        background: $surface;
        border: solid $primary-lighten-2;
    }

    CreateAgentScreen #browse-btn {
        width: auto;
        min-width: 10;
        margin-left: 1;
    }

    CreateAgentScreen #buttons {
        height: auto;
        margin-top: 2;
        align: right middle;
    }

    CreateAgentScreen #buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._workspace_path = _load_last_workspace()
        self._permission_mode = _load_claude_permission_mode()
        self._tracking_mode = _load_claude_tracking_mode()

    def compose(self) -> ComposeResult:
        with Container(id="create-agent-root"):
            yield Static("Create New Agent", id="create-agent-title")

            yield Label("Agent Type", classes="section-label")
            with RadioSet(id="agent-type"):
                yield RadioButton("Claude", id="type-claude", value=True)
                yield RadioButton("Codex", id="type-codex")
                yield RadioButton("Opencode", id="type-opencode")
                yield RadioButton("zsh", id="type-zsh")

            with Vertical(id="workspace-section"):
                yield Label("Workspace", classes="section-label")
                with Horizontal(id="workspace-row"):
                    yield Static(self._workspace_path, id="workspace-path")
                    yield Button("Browse", id="browse-btn", variant="default")

            with Vertical(id="claude-options"):
                yield Label("Permission Mode", classes="section-label")
                with RadioSet(id="permission-mode"):
                    yield RadioButton("Normal", id="perm-normal", value=True)
                    yield RadioButton("Skip (--dangerously-skip-permissions)", id="perm-skip")

                yield Label("Tracking", classes="section-label")
                with RadioSet(id="tracking-mode"):
                    yield RadioButton("Track", id="track-track", value=True)
                    yield RadioButton("No Track (skip LLM summaries)", id="track-notrack")

            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Create", id="create", variant="primary")

    def on_mount(self) -> None:
        # Set the saved permission mode
        if self._permission_mode == "skip":
            self.query_one("#perm-skip", RadioButton).value = True
        else:
            self.query_one("#perm-normal", RadioButton).value = True
        # Set the saved tracking mode
        if self._tracking_mode == "notrack":
            self.query_one("#track-notrack", RadioButton).value = True
        else:
            self.query_one("#track-track", RadioButton).value = True
        self.query_one("#create", Button).focus()

    def action_close(self) -> None:
        self.dismiss(None)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Show/hide Claude options based on selected agent type."""
        # Only handle agent type changes
        if event.radio_set.id != "agent-type":
            return
        claude_options = self.query_one("#claude-options", Vertical)
        is_claude = event.pressed.id == "type-claude" if event.pressed else False
        if is_claude:
            claude_options.remove_class("hidden")
        else:
            claude_options.add_class("hidden")

    def _update_workspace_display(self) -> None:
        """Update the workspace path display."""
        self.query_one("#workspace-path", Static).update(self._workspace_path)

    async def _select_workspace(self) -> str | None:
        """Open macOS folder picker and return selected path, or None if cancelled."""
        default_path = self._workspace_path
        default_path_escaped = default_path.replace('"', '\\"')
        prompt = "Select workspace folder"
        prompt_escaped = prompt.replace('"', '\\"')
        script = f"""
            set defaultFolder to POSIX file "{default_path_escaped}" as alias
            try
                set selectedFolder to choose folder with prompt "{prompt_escaped}" default location defaultFolder
                return POSIX path of selectedFolder
            on error
                return ""
            end try
        """
        try:
            proc = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                    timeout=120,
                ),
            )
            result = (proc.stdout or "").strip()
            if result and os.path.isdir(result):
                return result
            return None
        except Exception:
            return None

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""

        if button_id == "cancel":
            self.dismiss(None)
            return

        if button_id == "browse-btn":
            new_path = await self._select_workspace()
            if new_path:
                self._workspace_path = new_path
                self._update_workspace_display()
            return

        if button_id == "create":
            # Get selected agent type
            radio_set = self.query_one("#agent-type", RadioSet)
            pressed_button = radio_set.pressed_button
            if pressed_button is None:
                self.app.notify("Please select an agent type", severity="warning")
                return

            agent_type_map = {
                "type-claude": "claude",
                "type-codex": "codex",
                "type-opencode": "opencode",
                "type-zsh": "zsh",
            }
            agent_type = agent_type_map.get(pressed_button.id or "", "claude")

            # Get permission mode and tracking mode (only relevant for Claude)
            skip_permissions = False
            no_track = False
            if agent_type == "claude":
                perm_radio_set = self.query_one("#permission-mode", RadioSet)
                perm_pressed = perm_radio_set.pressed_button
                skip_permissions = perm_pressed is not None and perm_pressed.id == "perm-skip"
                # Save the permission mode for next time
                permission_mode = "skip" if skip_permissions else "normal"
                _save_claude_permission_mode(permission_mode)

                # Get tracking mode
                track_radio_set = self.query_one("#tracking-mode", RadioSet)
                track_pressed = track_radio_set.pressed_button
                no_track = track_pressed is not None and track_pressed.id == "track-notrack"
                # Save the tracking mode for next time
                tracking_mode = "notrack" if no_track else "track"
                _save_claude_tracking_mode(tracking_mode)

            # Save the workspace path for next time
            _save_last_workspace(self._workspace_path)

            # Return the result
            self.dismiss((agent_type, self._workspace_path, skip_permissions, no_track))

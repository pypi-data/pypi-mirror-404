"""Agents Panel Widget - Lists agent profiles with their terminals."""

from __future__ import annotations

import asyncio
import re
import shlex
from pathlib import Path
from typing import Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Static
from textual.message import Message
from textual.worker import Worker, WorkerState
from rich.text import Text

from .. import tmux_manager
from ...logging_config import setup_logger
from ..clipboard import copy_text

logger = setup_logger("realign.dashboard.widgets.agents_panel", "dashboard.log")


class AgentNameButton(Button):
    """Button that emits a message on double-click."""

    class DoubleClicked(Message, bubble=True):
        def __init__(self, button: "AgentNameButton", agent_id: str) -> None:
            super().__init__()
            self.button = button
            self.agent_id = agent_id

    async def _on_click(self, event: events.Click) -> None:
        await super()._on_click(event)
        if event.chain >= 2:
            self.post_message(self.DoubleClicked(self, self.name or ""))


class AgentsPanel(Container, can_focus=True):
    """Panel displaying agent profiles with their associated terminals."""

    DEFAULT_CSS = """
    AgentsPanel {
        height: 100%;
        padding: 0 1;
        overflow: hidden;
    }

    AgentsPanel:focus {
        border: none;
    }

    AgentsPanel .summary {
        height: auto;
        margin: 0 0 1 0;
        padding: 0;
        background: transparent;
        border: none;
    }

    AgentsPanel Button {
        min-width: 0;
        padding: 0 1;
        background: transparent;
        border: none;
    }

    AgentsPanel Button:hover {
        background: $surface-lighten-1;
    }

    AgentsPanel .summary Button {
        width: auto;
        margin-right: 1;
    }

    AgentsPanel .list {
        height: 1fr;
        padding: 0;
        overflow-y: auto;
        border: none;
        background: transparent;
    }

    AgentsPanel .agent-row {
        height: auto;
        min-height: 2;
        margin: 0 0 0 0;
    }

    AgentsPanel .agent-row Button.agent-name {
        width: 1fr;
        height: 2;
        margin: 0;
        padding: 0 1;
        text-align: left;
        content-align: left middle;
    }

    AgentsPanel .agent-row Button.agent-create {
        width: auto;
        min-width: 8;
        height: 2;
        margin-left: 1;
        padding: 0 1;
        content-align: center middle;
    }

    AgentsPanel .agent-row Button.agent-delete {
        width: 3;
        min-width: 3;
        height: 2;
        margin-left: 1;
        padding: 0;
        content-align: center middle;
    }

    AgentsPanel .agent-row Button.agent-share {
        width: auto;
        min-width: 8;
        height: 2;
        margin-left: 1;
        padding: 0 1;
        content-align: center middle;
    }

    AgentsPanel .terminal-list {
        margin: 0 0 1 2;
        padding: 0;
        height: auto;
        background: transparent;
        border: none;
    }

    AgentsPanel .terminal-row {
        height: auto;
        min-height: 2;
        margin: 0;
    }

    AgentsPanel .terminal-row Button.terminal-switch {
        width: 1fr;
        height: 2;
        margin: 0;
        padding: 0 1;
        text-align: left;
        content-align: left top;
    }

    AgentsPanel .terminal-row Button.terminal-close {
        width: 3;
        min-width: 3;
        height: 2;
        margin-left: 1;
        padding: 0;
        content-align: center middle;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._refresh_lock = asyncio.Lock()
        self._agents: list[dict] = []
        self._refresh_worker: Optional[Worker] = None
        self._share_worker: Optional[Worker] = None
        self._share_agent_id: Optional[str] = None
        self._refresh_timer = None

    def compose(self) -> ComposeResult:
        with Horizontal(classes="summary"):
            yield Button("+ Create Agent", id="create-agent", variant="primary")
        with Vertical(id="agents-list", classes="list"):
            yield Static("No agents yet. Click 'Create Agent' to add one.")

    def on_show(self) -> None:
        if self._refresh_timer is None:
            self._refresh_timer = self.set_interval(30.0, self._on_refresh_timer)
        else:
            try:
                self._refresh_timer.resume()
            except Exception:
                pass
        self.refresh_data()

    def on_hide(self) -> None:
        if self._refresh_timer is not None:
            try:
                self._refresh_timer.pause()
            except Exception:
                pass

    def _on_refresh_timer(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        if not self.display:
            return
        if self._refresh_worker is not None and self._refresh_worker.state in (
            WorkerState.PENDING,
            WorkerState.RUNNING,
        ):
            return
        self._refresh_worker = self.run_worker(
            self._collect_agents, thread=True, exit_on_error=False
        )

    def _collect_agents(self) -> list[dict]:
        """Collect agent info with their terminals."""
        agents = []
        try:
            from ...db import get_database

            db = get_database(read_only=True)
            agent_infos = db.list_agent_info()
            active_terminals = db.list_agents(status="active", limit=1000)

            # Get tmux windows to retrieve session_id (same as Terminal panel)
            tmux_windows = tmux_manager.list_inner_windows()
            # Map terminal_id -> tmux window
            terminal_to_window = {
                w.terminal_id: w for w in tmux_windows if w.terminal_id
            }

            # Collect all session_ids from tmux windows for title lookup
            session_ids = [
                w.session_id for w in tmux_windows if w.session_id and w.terminal_id
            ]
            # Fetch titles from database (same method as Terminal panel)
            titles = self._fetch_session_titles(session_ids)

            # Map agent_info.id -> list of terminals
            agent_to_terminals: dict[str, list[dict]] = {}
            for t in active_terminals:
                # Find which agent_info this terminal belongs to
                agent_info_id = None

                # Method 1: Check source field for "agent:{agent_info_id}" format
                source = t.source or ""
                if source.startswith("agent:"):
                    agent_info_id = source[6:]  # Extract agent_info_id after "agent:"

                # Method 2: Fallback - check tmux window's session.agent_id
                if not agent_info_id:
                    window = terminal_to_window.get(t.id)
                    if window and window.session_id:
                        # Look up session to get agent_id
                        session = db.get_session_by_id(window.session_id)
                        if session:
                            agent_info_id = session.agent_id

                if agent_info_id:
                    if agent_info_id not in agent_to_terminals:
                        agent_to_terminals[agent_info_id] = []

                    # Get session_id and title from tmux window (same as Terminal panel)
                    window = terminal_to_window.get(t.id)
                    session_id = window.session_id if window else None
                    title = titles.get(session_id, "") if session_id else ""

                    agent_to_terminals[agent_info_id].append(
                        {
                            "terminal_id": t.id,
                            "session_id": session_id,
                            "provider": t.provider or "",
                            "session_type": t.session_type or "",
                            "title": title,
                            "cwd": t.cwd or "",
                        }
                    )

            for info in agent_infos:
                terminals = agent_to_terminals.get(info.id, [])
                agents.append(
                    {
                        "id": info.id,
                        "name": info.name,
                        "description": info.description or "",
                        "terminals": terminals,
                    }
                )
        except Exception as e:
            logger.debug(f"Failed to collect agents: {e}")
        return agents

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        # Handle refresh worker
        if self._refresh_worker is not None and event.worker is self._refresh_worker:
            if event.state == WorkerState.ERROR:
                self._agents = []
            elif event.state == WorkerState.SUCCESS:
                self._agents = self._refresh_worker.result or []
            else:
                return
            self.run_worker(
                self._render_agents(), group="agents-render", exclusive=True
            )
            return

        # Handle share worker
        if self._share_worker is not None and event.worker is self._share_worker:
            self._handle_share_worker_state_changed(event)

    async def _render_agents(self) -> None:
        async with self._refresh_lock:
            try:
                container = self.query_one("#agents-list", Vertical)
            except Exception:
                return

            await container.remove_children()

            if not self._agents:
                await container.mount(
                    Static("No agents yet. Click 'Create Agent' to add one.")
                )
                return

            for agent in self._agents:
                safe_id = self._safe_id(agent["id"])

                # Agent row with name, create button, and delete button
                row = Horizontal(classes="agent-row")
                await container.mount(row)

                # Agent name button
                name_label = Text(agent["name"], style="bold")
                terminal_count = len(agent["terminals"])
                if terminal_count > 0:
                    name_label.append(f" ({terminal_count})", style="dim")

                await row.mount(
                    AgentNameButton(
                        name_label,
                        id=f"agent-{safe_id}",
                        name=agent["id"],
                        classes="agent-name",
                    )
                )

                # Share button
                await row.mount(
                    Button(
                        "Share",
                        id=f"share-{safe_id}",
                        name=agent["id"],
                        classes="agent-share",
                    )
                )

                # Create terminal button
                await row.mount(
                    Button(
                        "+ Term",
                        id=f"create-term-{safe_id}",
                        name=agent["id"],
                        classes="agent-create",
                    )
                )

                # Delete agent button
                await row.mount(
                    Button(
                        "✕",
                        id=f"delete-{safe_id}",
                        name=agent["id"],
                        variant="error",
                        classes="agent-delete",
                    )
                )

                # Terminal list (indented under agent)
                if agent["terminals"]:
                    term_list = Vertical(classes="terminal-list")
                    await container.mount(term_list)

                    for term in agent["terminals"]:
                        term_safe_id = self._safe_id(term["terminal_id"])
                        term_row = Horizontal(classes="terminal-row")
                        await term_list.mount(term_row)

                        label = self._make_terminal_label(term)
                        await term_row.mount(
                            Button(
                                label,
                                id=f"switch-{term_safe_id}",
                                name=term["terminal_id"],
                                classes="terminal-switch",
                            )
                        )
                        await term_row.mount(
                            Button(
                                "✕",
                                id=f"close-{term_safe_id}",
                                name=term["terminal_id"],
                                variant="error",
                                classes="terminal-close",
                            )
                        )

    def _make_terminal_label(self, term: dict) -> Text:
        """Generate label for a terminal."""
        provider = term.get("provider", "")
        session_id = term.get("session_id", "")
        title = term.get("title", "")

        label = Text(no_wrap=True, overflow="ellipsis")

        # First line: title or provider
        if title:
            label.append(title)
        elif provider:
            label.append(provider.capitalize())
        else:
            label.append("Terminal")

        label.append("\n")

        # Second line: [provider] session_id
        if provider:
            detail = f"[{provider.capitalize()}]"
        else:
            detail = ""
        if session_id:
            detail = f"{detail} #{self._short_id(session_id)}"

        label.append(detail, style="dim")
        return label

    @staticmethod
    def _short_id(val: str | None) -> str:
        if not val:
            return ""
        if len(val) > 20:
            return val[:8] + "..." + val[-8:]
        return val

    def _fetch_session_titles(self, session_ids: list[str]) -> dict[str, str]:
        """Fetch session titles from database (same method as Terminal panel)."""
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

    @staticmethod
    def _safe_id(raw: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "-", raw).strip("-_")
        if not safe:
            return "a"
        if safe[0].isdigit():
            return f"a-{safe}"
        return safe

    def _find_window(self, terminal_id: str) -> str | None:
        if not terminal_id:
            return None
        try:
            for w in tmux_manager.list_inner_windows():
                if w.terminal_id == terminal_id:
                    return w.window_id
        except Exception:
            pass
        return None

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""

        if btn_id == "create-agent":
            await self._create_agent()
            return

        if btn_id.startswith("agent-"):
            # Click on agent name - could expand/collapse or do nothing
            return

        if btn_id.startswith("create-term-"):
            agent_id = event.button.name or ""
            await self._create_terminal_for_agent(agent_id)
            return

        if btn_id.startswith("delete-"):
            agent_id = event.button.name or ""
            await self._delete_agent(agent_id)
            return

        if btn_id.startswith("share-"):
            agent_id = event.button.name or ""
            await self._share_agent(agent_id)
            return

        if btn_id.startswith("switch-"):
            terminal_id = event.button.name or ""
            await self._switch_to_terminal(terminal_id)
            return

        if btn_id.startswith("close-"):
            terminal_id = event.button.name or ""
            await self._close_terminal(terminal_id)
            return

    async def on_agent_name_button_double_clicked(
        self, event: AgentNameButton.DoubleClicked
    ) -> None:
        agent_id = event.agent_id
        if not agent_id:
            return

        from ..screens import AgentDetailScreen

        self.app.push_screen(AgentDetailScreen(agent_id))

    async def _create_agent(self) -> None:
        try:
            from ..screens import CreateAgentInfoScreen

            self.app.push_screen(CreateAgentInfoScreen(), self._on_create_result)
        except ImportError:
            try:
                from ...agent_names import generate_agent_name
                from ...db import get_database
                import uuid

                db = get_database(read_only=False)
                agent_id = str(uuid.uuid4())
                name = generate_agent_name()
                db.get_or_create_agent_info(agent_id, name=name)
                self.app.notify(f"Created: {name}", title="Agent")
                self.refresh_data()
            except Exception as e:
                self.app.notify(f"Failed: {e}", title="Agent", severity="error")

    def _on_create_result(self, result: dict | None) -> None:
        if result:
            self.app.notify(f"Created: {result.get('name')}", title="Agent")
        self.refresh_data()

    async def _create_terminal_for_agent(self, agent_id: str) -> None:
        """Create a new terminal under the specified agent."""
        if not agent_id:
            return

        # Get agent info
        agent = next((a for a in self._agents if a["id"] == agent_id), None)
        if not agent:
            self.app.notify("Agent not found", title="Agent", severity="error")
            return

        # Show create terminal screen with agent context
        try:
            from ..screens import CreateAgentScreen

            self.app.push_screen(
                CreateAgentScreen(),
                lambda result: self._on_create_terminal_result(result, agent_id),
            )
        except ImportError as e:
            self.app.notify(f"Failed: {e}", title="Agent", severity="error")

    def _on_create_terminal_result(
        self, result: tuple[str, str, bool, bool] | None, agent_id: str
    ) -> None:
        """Handle result from CreateAgentScreen."""
        if result is None:
            return

        agent_type, workspace, skip_permissions, no_track = result

        # Create the terminal with agent association
        self.run_worker(
            self._do_create_terminal(
                agent_type, workspace, skip_permissions, no_track, agent_id
            ),
            group="terminal-create",
            exclusive=True,
        )

    async def _do_create_terminal(
        self,
        agent_type: str,
        workspace: str,
        skip_permissions: bool,
        no_track: bool,
        agent_id: str,
    ) -> None:
        """Actually create the terminal with agent association."""
        if agent_type == "claude":
            await self._create_claude_terminal(
                workspace, skip_permissions, no_track, agent_id
            )
        elif agent_type == "codex":
            await self._create_codex_terminal(workspace, no_track, agent_id)
        elif agent_type == "opencode":
            await self._create_opencode_terminal(workspace, agent_id)
        elif agent_type == "zsh":
            await self._create_zsh_terminal(workspace, agent_id)

        self.refresh_data()

    async def _create_claude_terminal(
        self, workspace: str, skip_permissions: bool, no_track: bool, agent_id: str
    ) -> None:
        """Create a Claude terminal associated with an agent."""
        terminal_id = tmux_manager.new_terminal_id()
        context_id = tmux_manager.new_context_id("cc")

        # Prepare CODEX_HOME so user can run codex in this terminal
        try:
            from ...codex_home import prepare_codex_home

            codex_home = prepare_codex_home(terminal_id, agent_id=agent_id)
        except Exception:
            codex_home = None

        env = {
            tmux_manager.ENV_TERMINAL_ID: terminal_id,
            tmux_manager.ENV_TERMINAL_PROVIDER: "claude",
            tmux_manager.ENV_INNER_SOCKET: tmux_manager.INNER_SOCKET,
            tmux_manager.ENV_INNER_SESSION: tmux_manager.INNER_SESSION,
            tmux_manager.ENV_CONTEXT_ID: context_id,
            "ALINE_AGENT_ID": agent_id,  # Pass agent_id to hooks
        }
        if codex_home:
            env["CODEX_HOME"] = str(codex_home)
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

        if created:
            # Store agent association in database with agent_info_id in source
            try:
                from ...db import get_database

                db = get_database(read_only=False)
                db.get_or_create_agent(
                    terminal_id,
                    provider="claude",
                    session_type="claude",
                    context_id=context_id,
                    cwd=workspace,
                    project_dir=workspace,
                    source=f"agent:{agent_id}",  # Store agent_info_id in source
                )
            except Exception:
                pass
        else:
            self.app.notify(
                "Failed to create terminal", title="Agent", severity="error"
            )

    async def _create_codex_terminal(
        self, workspace: str, no_track: bool, agent_id: str
    ) -> None:
        """Create a Codex terminal associated with an agent."""
        try:
            from ...db import get_database
            from datetime import datetime, timedelta

            db = get_database(read_only=True)
            cutoff = datetime.now() - timedelta(seconds=10)
            for agent in db.list_agents(status="active", limit=1000):
                if agent.provider != "codex":
                    continue
                if (agent.source or "") != f"agent:{agent_id}":
                    continue
                if agent.created_at >= cutoff and not agent.session_id:
                    self.app.notify(
                        "Please wait a few seconds before opening another Codex terminal for this agent.",
                        title="Agent",
                        severity="warning",
                    )
                    return
        except Exception:
            pass

        terminal_id = tmux_manager.new_terminal_id()
        context_id = tmux_manager.new_context_id("cx")

        try:
            from ...codex_home import prepare_codex_home

            codex_home = prepare_codex_home(terminal_id, agent_id=agent_id)
        except Exception:
            codex_home = None

        env = {
            tmux_manager.ENV_TERMINAL_ID: terminal_id,
            tmux_manager.ENV_TERMINAL_PROVIDER: "codex",
            tmux_manager.ENV_INNER_SOCKET: tmux_manager.INNER_SOCKET,
            tmux_manager.ENV_INNER_SESSION: tmux_manager.INNER_SESSION,
            tmux_manager.ENV_CONTEXT_ID: context_id,
            "ALINE_AGENT_ID": agent_id,
        }
        if codex_home:
            env["CODEX_HOME"] = str(codex_home)
        if no_track:
            env["ALINE_NO_TRACK"] = "1"

        # Store agent in database with agent_info_id in source
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
                source=f"agent:{agent_id}",  # Store agent_info_id in source
            )
        except Exception:
            pass

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
            self.app.notify(
                "Failed to create terminal", title="Agent", severity="error"
            )

    async def _create_opencode_terminal(self, workspace: str, agent_id: str) -> None:
        """Create an Opencode terminal associated with an agent."""
        terminal_id = tmux_manager.new_terminal_id()
        context_id = tmux_manager.new_context_id("oc")

        # Prepare CODEX_HOME so user can run codex in this terminal
        try:
            from ...codex_home import prepare_codex_home

            codex_home = prepare_codex_home(terminal_id, agent_id=agent_id)
        except Exception:
            codex_home = None

        env = {
            tmux_manager.ENV_TERMINAL_ID: terminal_id,
            tmux_manager.ENV_TERMINAL_PROVIDER: "opencode",
            tmux_manager.ENV_INNER_SOCKET: tmux_manager.INNER_SOCKET,
            tmux_manager.ENV_INNER_SESSION: tmux_manager.INNER_SESSION,
            tmux_manager.ENV_CONTEXT_ID: context_id,
            "ALINE_AGENT_ID": agent_id,
        }
        if codex_home:
            env["CODEX_HOME"] = str(codex_home)

        # Install Claude hooks in case user runs claude manually
        self._install_claude_hooks(workspace)

        command = self._command_in_directory(
            tmux_manager.zsh_run_and_keep_open("opencode"), workspace
        )

        created = tmux_manager.create_inner_window(
            "opencode",
            tmux_manager.shell_command_with_env(command, env),
            terminal_id=terminal_id,
            provider="opencode",
            context_id=context_id,
        )

        if created:
            # Store agent association in database
            try:
                from ...db import get_database

                db = get_database(read_only=False)
                db.get_or_create_agent(
                    terminal_id,
                    provider="opencode",
                    session_type="opencode",
                    context_id=context_id,
                    cwd=workspace,
                    project_dir=workspace,
                    source=f"agent:{agent_id}",
                )
            except Exception:
                pass
        else:
            self.app.notify(
                "Failed to create terminal", title="Agent", severity="error"
            )

    async def _create_zsh_terminal(self, workspace: str, agent_id: str) -> None:
        """Create a zsh terminal associated with an agent."""
        terminal_id = tmux_manager.new_terminal_id()
        context_id = tmux_manager.new_context_id("zsh")

        # Prepare CODEX_HOME so user can run codex in this terminal
        try:
            from ...codex_home import prepare_codex_home

            codex_home = prepare_codex_home(terminal_id, agent_id=agent_id)
        except Exception:
            codex_home = None

        env = {
            tmux_manager.ENV_TERMINAL_ID: terminal_id,
            tmux_manager.ENV_TERMINAL_PROVIDER: "zsh",
            tmux_manager.ENV_INNER_SOCKET: tmux_manager.INNER_SOCKET,
            tmux_manager.ENV_INNER_SESSION: tmux_manager.INNER_SESSION,
            tmux_manager.ENV_CONTEXT_ID: context_id,
            "ALINE_AGENT_ID": agent_id,
        }
        if codex_home:
            env["CODEX_HOME"] = str(codex_home)

        # Install Claude hooks in case user runs claude manually
        self._install_claude_hooks(workspace)

        command = self._command_in_directory("zsh", workspace)

        created = tmux_manager.create_inner_window(
            "zsh",
            tmux_manager.shell_command_with_env(command, env),
            terminal_id=terminal_id,
            provider="zsh",
            context_id=context_id,
        )

        if created:
            # Store agent association in database
            try:
                from ...db import get_database

                db = get_database(read_only=False)
                db.get_or_create_agent(
                    terminal_id,
                    provider="zsh",
                    session_type="zsh",
                    context_id=context_id,
                    cwd=workspace,
                    project_dir=workspace,
                    source=f"agent:{agent_id}",
                )
            except Exception:
                pass
        else:
            self.app.notify(
                "Failed to create terminal", title="Agent", severity="error"
            )

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

            ensure_stop_hook_installed(quiet=True)
            ensure_user_prompt_submit_hook_installed(quiet=True)
            ensure_permission_request_hook_installed(quiet=True)

            project_root = Path(workspace)
            install_stop_hook(get_stop_settings_path(project_root), quiet=True)
            install_user_prompt_submit_hook(
                get_submit_settings_path(project_root), quiet=True
            )
            install_permission_request_hook(
                get_permission_settings_path(project_root), quiet=True
            )
        except Exception:
            pass

    @staticmethod
    def _command_in_directory(command: str, directory: str) -> str:
        return f"cd {shlex.quote(directory)} && {command}"

    async def _delete_agent(self, agent_id: str) -> None:
        if not agent_id:
            return
        try:
            from ...db import get_database

            db = get_database(read_only=False)
            info = db.get_agent_info(agent_id)
            name = info.name if info else "Unknown"

            record = db.update_agent_info(agent_id, visibility="invisible")
            if record:
                self.app.notify(f"Hidden: {name}", title="Agent")
            self.refresh_data()
        except Exception as e:
            self.app.notify(f"Failed: {e}", title="Agent", severity="error")

    async def _switch_to_terminal(self, terminal_id: str) -> None:
        if not terminal_id:
            return

        window_id = self._find_window(terminal_id)
        if not window_id:
            self.app.notify("Window not found", title="Agent", severity="warning")
            return

        if tmux_manager.select_inner_window(window_id):
            tmux_manager.focus_right_pane()
            tmux_manager.clear_attention(window_id)
        else:
            self.app.notify("Failed to switch", title="Agent", severity="error")

    async def _close_terminal(self, terminal_id: str) -> None:
        if not terminal_id:
            return

        # Try to close the tmux window if it exists
        window_id = self._find_window(terminal_id)
        if window_id:
            tmux_manager.kill_inner_window(window_id)

        # Also update the agent status in the database to mark it as inactive
        try:
            from ...db import get_database

            db = get_database(read_only=False)
            db.update_agent(terminal_id, status="inactive")
        except Exception as e:
            logger.debug(f"Failed to update agent status: {e}")

        self.refresh_data()

    async def _share_agent(self, agent_id: str) -> None:
        """Share all sessions for an agent."""
        if not agent_id:
            return

        # Check if share is already in progress
        if self._share_worker is not None and self._share_worker.state in (
            WorkerState.PENDING,
            WorkerState.RUNNING,
        ):
            return

        # Check if agent has sessions
        try:
            from ...db import get_database

            db = get_database(read_only=True)
            sessions = db.get_sessions_by_agent_id(agent_id)
            if not sessions:
                self.app.notify(
                    "Agent has no sessions to share", title="Share", severity="warning"
                )
                return
        except Exception as e:
            self.app.notify(
                f"Failed to check sessions: {e}", title="Share", severity="error"
            )
            return

        # Store agent_id for the worker callback
        self._share_agent_id = agent_id

        # Create progress callback that posts notifications from worker thread
        app = self.app  # Capture reference for closure

        def progress_callback(message: str) -> None:
            """Send progress notification from worker thread."""
            try:
                app.call_from_thread(app.notify, message, title="Share", timeout=3)
            except Exception:
                pass  # Ignore errors if app is closing

        def work() -> dict:
            import contextlib
            import io
            import json as json_module
            import re

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                from ...commands import export_shares

                exit_code = export_shares.export_agent_shares_command(
                    agent_id=agent_id,
                    password=None,
                    json_output=True,
                    compact=True,
                    progress_callback=progress_callback,
                )

            output = stdout.getvalue().strip()
            error_text = stderr.getvalue().strip()
            result: dict = {
                "exit_code": exit_code,
                "output": output,
                "stderr": error_text,
            }

            if output:
                try:
                    result["json"] = json_module.loads(output)
                except Exception:
                    result["json"] = None
                    try:
                        from ...llm_client import extract_json

                        result["json"] = extract_json(output)
                    except Exception:
                        result["json"] = None
                        try:
                            match = re.search(r"\{.*\}", output, re.DOTALL)
                            if match:
                                result["json"] = json_module.loads(
                                    match.group(0), strict=False
                                )
                        except Exception:
                            result["json"] = None

            if not result.get("json") and output:
                match = re.search(r"https?://[^\s\"']+/share/[^\s\"']+", output)
                if match:
                    result["share_link_guess"] = match.group(0)
            else:
                result["json"] = None

            return result

        self.app.notify("Starting share...", title="Share", timeout=2)
        self._share_worker = self.run_worker(work, thread=True, exit_on_error=False)

    def _handle_share_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle share worker state changes."""
        from ..clipboard import copy_text

        if event.state == WorkerState.ERROR:
            err = self._share_worker.error if self._share_worker else "Unknown error"
            self.app.notify(f"Share failed: {err}", title="Share", severity="error")
            return

        if event.state != WorkerState.SUCCESS:
            return

        result = self._share_worker.result if self._share_worker else {}
        raw_exit_code = result.get("exit_code", None)
        exit_code = 1 if raw_exit_code is None else int(raw_exit_code)
        payload = result.get("json") or {}
        share_link = payload.get("share_link") or payload.get("share_url")
        if not share_link:
            share_link = result.get("share_link_guess")
        slack_message = (
            payload.get("slack_message") if isinstance(payload, dict) else None
        )
        if not slack_message:
            try:
                from ...db import get_database

                db = get_database()
                agent_info = (
                    db.get_agent_info(self._share_agent_id) if self._share_agent_id else None
                )
                agent_name = agent_info.name if agent_info and agent_info.name else "agent"
                slack_message = f"Sharing {agent_name} sessions from Aline."
            except Exception:
                slack_message = "Sharing sessions from Aline."

        if exit_code == 0 and share_link:
            if slack_message:
                text_to_copy = str(slack_message) + "\n\n" + str(share_link)
            else:
                text_to_copy = str(share_link)

            copied = copy_text(self.app, text_to_copy)

            suffix = " (copied)" if copied else ""
            self.app.notify(
                f"Share link: {share_link}{suffix}", title="Share", timeout=6
            )
        elif exit_code == 0:
            self.app.notify("Share completed", title="Share", timeout=3)
        else:
            extra = result.get("stderr") or ""
            suffix = f": {extra}" if extra else ""
            self.app.notify(
                f"Share failed (exit {exit_code}){suffix}", title="Share", timeout=6
            )

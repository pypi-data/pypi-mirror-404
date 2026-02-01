#!/usr/bin/env python3
"""ReAlign CLI - Main command-line interface."""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.syntax import Syntax

from .commands import (
    init,
    config,
    watcher,
    worker,
    export_shares,
    search,
    upgrade,
    restore,
    add,
    auth,
    doctor,
    agent,
)

app = typer.Typer(
    name="realign",
    help="Track and version AI agent chat sessions with git commits",
    add_completion=False,
    invoke_without_command=True,
)
console = Console()


@app.callback()
def main(
    ctx: typer.Context,
    dev: bool = typer.Option(False, "--dev", help="Enable developer mode (shows Watcher and Worker tabs)"),
):
    """
    Aline CLI - Shared AI Memory for teams.

    Run 'aline' without arguments to open the interactive dashboard.
    """
    # Store dev mode in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["dev"] = dev

    if ctx.invoked_subcommand is None:
        def _needs_global_init() -> bool:
            config_path = Path.home() / ".aline" / "config.yaml"
            if not config_path.exists():
                return True
            try:
                from .config import ReAlignConfig

                cfg = ReAlignConfig.load(config_path)
                db_path = Path(cfg.sqlite_db_path).expanduser()
                if not db_path.exists():
                    return True
            except Exception:
                return True
            prompts_dir = Path.home() / ".aline" / "prompts"
            return not prompts_dir.exists()

        # Check login status before launching dashboard
        from .auth import is_logged_in, get_current_user

        if not is_logged_in():
            console.print("[yellow]You need to login before using Aline.[/yellow]")
            console.print("Starting login flow...\n")

            # Run login command
            exit_code = auth.login_command()
            if exit_code != 0:
                console.print("\n[red]Login failed. Please try again with 'aline login'.[/red]")
                raise typer.Exit(code=1)

            # Verify login succeeded
            if not is_logged_in():
                console.print("\n[red]Login verification failed. Please try again.[/red]")
                raise typer.Exit(code=1)

            console.print()  # Add spacing before dashboard launch

        # First run after install/upgrade: ensure global artifacts exist.
        if _needs_global_init():
            console.print("[dim]First run detected. Running 'aline init'...[/dim]\n")
            try:
                from .commands import init as init_cmd

                init_cmd.init_command(force=False, start_watcher=None)
            except typer.Exit as e:
                if getattr(e, "exit_code", 1) != 0:
                    raise

        # Check for updates before launching dashboard
        from .commands.upgrade import check_and_prompt_update

        if check_and_prompt_update():
            # Update was performed, exit so user can restart with new version
            raise typer.Exit(0)

        # Launch the dashboard when no subcommand is provided
        import os

        terminal_mode = os.environ.get("ALINE_TERMINAL_MODE", "").strip().lower()
        use_native_terminal = terminal_mode in {"native", "iterm2", "iterm", "kitty"}

        right_pane_session_id = None

        if not use_native_terminal:
            # Only bootstrap tmux for tmux mode (default)
            from .dashboard.tmux_manager import bootstrap_dashboard_into_tmux

            bootstrap_dashboard_into_tmux()
        elif terminal_mode in {"iterm2", "iterm"}:
            # Set up split pane layout for iTerm2
            try:
                from .dashboard.backends.iterm2 import setup_split_pane_layout_sync

                right_pane_session_id = setup_split_pane_layout_sync()
                if right_pane_session_id:
                    # Store in environment for dashboard to pick up
                    os.environ["ALINE_ITERM2_RIGHT_PANE"] = right_pane_session_id
            except Exception as e:
                console.print(f"[yellow]Warning: Could not set up split pane: {e}[/yellow]")

        from .dashboard.app import AlineDashboard

        dashboard = AlineDashboard(dev_mode=dev, use_native_terminal=use_native_terminal)
        dashboard.run()


# Register commands
app.command(name="init")(init.init_command)
app.command(name="config")(config.config_command)
app.command(name="upgrade")(upgrade.upgrade_command)
app.command(name="doctor")(doctor.doctor_command)


# Auth commands
@app.command(name="login")
def login_cli():
    """Login to Aline via web browser to enable share features."""
    exit_code = auth.login_command()
    raise typer.Exit(code=exit_code)


@app.command(name="logout")
def logout_cli():
    """Logout from Aline and clear local credentials."""
    exit_code = auth.logout_command()
    raise typer.Exit(code=exit_code)


@app.command(name="whoami")
def whoami_cli():
    """Display current login status and user information."""
    exit_code = auth.whoami_command()
    raise typer.Exit(code=exit_code)


@app.command(name="search")
def search_cli(
    query: str = typer.Argument(..., help="Search query (keywords or regex pattern)"),
    type: str = typer.Option(
        "all", "--type", "-t", help="Search type: all, event, turn, session, content"
    ),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    regex: bool = typer.Option(
        True,
        "--regex/--no-regex",
        "-E",
        help="Use regular expression search (default: True)",
    ),
    ignore_case: bool = typer.Option(
        True, "-i/--case-sensitive", help="Ignore case (default: True)"
    ),
    count_only: bool = typer.Option(False, "--count", "-c", help="Only show match count"),
    line_numbers: bool = typer.Option(True, "-n/--no-line-numbers", help="Show line numbers"),
    sessions: str = typer.Option(
        None,
        "--sessions",
        "-s",
        help="Limit search to specific sessions (comma-separated IDs)",
    ),
    events: str = typer.Option(
        None,
        "--events",
        "-e",
        help="Limit search to sessions within specific events (comma-separated IDs)",
    ),
    turns: str = typer.Option(
        None,
        "--turns",
        help="Limit content search to specific turns (comma-separated IDs)",
    ),
    no_context: bool = typer.Option(
        False,
        "--no-context",
        help="Ignore loaded context from ~/.aline/load.json",
    ),
):
    """
    Search project history, events, turns, sessions, and content.

    Examples:
        aline search "sqlite.*migration"        # Regex search (default)
        aline search "auth" --no-regex          # Simple keyword search
        aline search -t turn "refactor"         # Search turn titles/summaries
        aline search -t content "error|bug"     # Search full content
        aline search "error|bug" -c             # Count regex matches
        aline search "bug" -s abc123de          # Search within specific session prefix
        aline search "bug" -e rel               # Search within specific event prefix
        aline search "bug" -t content --turns t123  # Search within specific turn prefix
        aline search "bug" --no-context         # Search all, ignore loaded context
    """
    exit_code = search.search_command(
        query=query,
        type=type,
        limit=limit,
        verbose=verbose,
        regex=regex,
        ignore_case=ignore_case,
        count_only=count_only,
        line_numbers=line_numbers,
        sessions=sessions,
        events=events,
        turns=turns,
        no_context=no_context,
    )
    raise typer.Exit(code=exit_code)


# Create watcher subcommand group
watcher_app = typer.Typer(help="Manage watcher daemon process")
app.add_typer(watcher_app, name="watcher")

# Create worker subcommand group
worker_app = typer.Typer(help="Manage worker daemon process")
app.add_typer(worker_app, name="worker")

# Create context subcommand group
context_app = typer.Typer(help="Manage search context (limit search scope)")
app.add_typer(context_app, name="context")

# Create add subcommand group
add_app = typer.Typer(help="Install optional local tooling")
app.add_typer(add_app, name="add")

# Create agent subcommand group
agent_app = typer.Typer(help="Manage agents")
app.add_typer(agent_app, name="agent")


@agent_app.command(name="new")
def agent_new_cli(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Agent name"),
    desc: str = typer.Option("", "--desc", "-d", help="Agent description"),
):
    """Create a new agent with a random name (or specify one)."""
    exit_code = agent.agent_new_command(name=name, desc=desc)
    raise typer.Exit(code=exit_code)


@agent_app.command(name="list")
def agent_list_cli(
    all: bool = typer.Option(
        False, "--all", "-a", help="Include invisible agents"
    ),
):
    """List all agents."""
    exit_code = agent.agent_list_command(include_invisible=all)
    raise typer.Exit(code=exit_code)


@agent_app.command(name="share")
def agent_share_cli(
    agent_id: str = typer.Argument(..., help="Agent ID to share"),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Password for encrypted share"
    ),
    expiry_days: int = typer.Option(7, "--expiry", help="Number of days before share expires"),
    max_views: int = typer.Option(100, "--max-views", help="Maximum number of views allowed"),
    mcp: bool = typer.Option(
        True,
        "--mcp/--no-mcp",
        help="Include MCP usage instructions (default: enabled)",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
):
    """Share all sessions for an agent.

    Creates a shareable link for all sessions associated with the specified agent.
    The share includes a generated Slack message for easy sharing.

    Examples:
        aline agent share abc123de
        aline agent share abc123de --json
        aline agent share abc123de --password mypass
    """
    exit_code = export_shares.export_agent_shares_command(
        agent_id=agent_id,
        password=password,
        expiry_days=expiry_days,
        max_views=max_views,
        enable_mcp=mcp,
        json_output=json_output,
    )
    raise typer.Exit(code=exit_code)


@add_app.command(name="tmux")
def add_tmux_cli():
    """Install tmux via Homebrew and set up Aline tmux clipboard bindings."""
    exit_code = add.add_tmux_command(install_brew=True)
    raise typer.Exit(code=exit_code)


@add_app.command(name="skills")
def add_skills_cli(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing skill"),
):
    """Install Aline skill for Claude Code.

    Installs the /aline skill to ~/.claude/skills/aline/ so Claude Code
    can search your conversation history.

    Examples:
        aline add skills           # Install skill
        aline add skills --force   # Reinstall/update skill
    """
    exit_code = add.add_skills_command(force=force)
    raise typer.Exit(code=exit_code)


@add_app.command(name="skills-dev")
def add_skills_dev_cli(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing skills"),
):
    """Install developer skills from skill-dev/ directory.

    Scans skill-dev/ for SKILL.md files and installs them to ~/.claude/skills/.
    This is for developer use only.

    Examples:
        aline add skills-dev           # Install dev skills
        aline add skills-dev --force   # Reinstall/update dev skills
    """
    exit_code = add.add_skills_dev_command(force=force)
    raise typer.Exit(code=exit_code)


@context_app.command(name="load")
def context_load_cli(
    sessions: Optional[str] = typer.Option(
        None,
        "--sessions",
        "-s",
        help="Session IDs to add to context (comma-separated or space-separated)",
    ),
    events: Optional[str] = typer.Option(
        None,
        "--events",
        "-e",
        help="Event IDs to add to context (comma-separated or space-separated)",
    ),
    context_id: Optional[str] = typer.Option(
        None,
        "--context-id",
        help="Context ID (for named contexts, used with ALINE_CONTEXT_ID env var)",
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace path (defaults to current directory)",
    ),
):
    """Load sessions/events into a search context.

    The context limits which sessions/events are searched by 'aline search'.

    Examples:
        aline context load -s session-id-1,session-id-2
        aline context load -e event-id-1 -s session-id-1
        aline context load -s s1,s2 --context-id my-project
    """
    from .commands.context import context_load_command

    # Parse comma or space separated IDs
    session_list = None
    if sessions:
        session_list = [s.strip() for s in sessions.replace(",", " ").split() if s.strip()]

    event_list = None
    if events:
        event_list = [e.strip() for e in events.replace(",", " ").split() if e.strip()]

    exit_code = context_load_command(
        sessions=session_list,
        events=event_list,
        context_id=context_id,
        workspace=workspace,
    )
    raise typer.Exit(code=exit_code)


@context_app.command(name="show")
def context_show_cli(
    context_id: Optional[str] = typer.Option(
        None,
        "--context-id",
        help="Show a specific context by ID",
    ),
    all_contexts: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show all defined contexts",
    ),
):
    """Show the current or specified search context.

    Examples:
        aline context show                  # Show current context
        aline context show --all            # Show all contexts
        aline context show --context-id my-project
    """
    from .commands.context import context_show_command

    exit_code = context_show_command(
        context_id=context_id,
        show_all=all_contexts,
    )
    raise typer.Exit(code=exit_code)


@context_app.command(name="clear")
def context_clear_cli(
    context_id: Optional[str] = typer.Option(
        None,
        "--context-id",
        help="Clear a specific context by ID",
    ),
):
    """Clear the current or specified search context.

    Examples:
        aline context clear                 # Clear current context
        aline context clear --context-id my-project
    """
    from .commands.context import context_clear_command

    exit_code = context_clear_command(context_id=context_id)
    raise typer.Exit(code=exit_code)


@watcher_app.command(name="status")
def watcher_status_cli(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed session tracking information"
    ),
    watch: bool = typer.Option(False, "--watch", "-w", help="Refresh status every second"),
):
    """Display watcher status."""
    import time

    if watch:
        try:
            while True:
                console.clear()
                watcher.watcher_status_command(verbose=verbose)
                console.print("[dim]Press Ctrl+C to exit watch mode[/dim]")
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[dim]Watch mode stopped[/dim]")
            raise typer.Exit(code=0)
    else:
        exit_code = watcher.watcher_status_command(verbose=verbose)
        raise typer.Exit(code=exit_code)


@watcher_app.command(name="start")
def watcher_start_cli():
    """Start the watcher daemon."""
    exit_code = watcher.watcher_start_command()
    raise typer.Exit(code=exit_code)


@watcher_app.command(name="stop")
def watcher_stop_cli():
    """Stop the watcher daemon."""
    exit_code = watcher.watcher_stop_command()
    raise typer.Exit(code=exit_code)


@watcher_app.command(name="fresh")
def watcher_fresh_cli():
    """Restart the watcher daemon (stop + start)."""
    exit_code = watcher.watcher_fresh_command()
    raise typer.Exit(code=exit_code)


@worker_app.command(name="status")
def worker_status_cli(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show job queue info"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Refresh status every second"),
    json_output: bool = typer.Option(False, "--json", help="Output status in JSON format"),
):
    """Display worker status."""
    import time

    if json_output:
        if watch:
            console.print("[red]Error:[/red] --json cannot be used with --watch")
            raise typer.Exit(code=1)
        exit_code = worker.worker_status_command(verbose=verbose, json_output=True)
        raise typer.Exit(code=exit_code)

    if watch:
        try:
            while True:
                console.clear()
                worker.worker_status_command(verbose=verbose)
                console.print("[dim]Press Ctrl+C to exit watch mode[/dim]")
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[dim]Watch mode stopped[/dim]")
            raise typer.Exit(code=0)
    else:
        exit_code = worker.worker_status_command(verbose=verbose)
        raise typer.Exit(code=exit_code)


@worker_app.command(name="start")
def worker_start_cli():
    """Start the worker daemon."""
    exit_code = worker.worker_start_command()
    raise typer.Exit(code=exit_code)


@worker_app.command(name="stop")
def worker_stop_cli():
    """Stop the worker daemon."""
    exit_code = worker.worker_stop_command()
    raise typer.Exit(code=exit_code)


@worker_app.command(name="fresh")
def worker_fresh_cli():
    """Restart the worker daemon (stop + start)."""
    exit_code = worker.worker_fresh_command()
    raise typer.Exit(code=exit_code)


@worker_app.command(name="repair")
def worker_repair_cli(
    force: bool = typer.Option(
        False,
        "--force",
        help="Requeue ALL processing jobs (including non-expired leases). Use only when worker is stopped.",
    ),
):
    """Repair jobs queue by requeueing orphaned processing jobs."""
    exit_code = worker.worker_repair_command(force=force)
    raise typer.Exit(code=exit_code)


@watcher_app.command(name="llm")
def watcher_llm_cli(
    watch: bool = typer.Option(
        False, "--watch", "-w", help="Watch mode: refresh display every 1 second"
    ),
    include_expired: bool = typer.Option(
        False, "--expired", "-e", help="(Deprecated) Kept for compatibility"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="(Deprecated) Kept for compatibility"
    ),
):
    """Monitor lock operations in real-time from log file."""
    exit_code = watcher.watcher_llm_command(
        watch=watch, include_expired=include_expired, verbose=verbose
    )
    raise typer.Exit(code=exit_code)


# Create session subcommand group under watcher
session_app = typer.Typer(help="Manage session discovery and import")
watcher_app.add_typer(session_app, name="session")

# Create event subcommand group under watcher
event_app = typer.Typer(help="Manage events")
watcher_app.add_typer(event_app, name="event")


@event_app.command(name="list")
def watcher_event_list_cli(
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum number of events to show"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
):
    """List all events from the database."""
    exit_code = watcher.watcher_event_list_command(
        limit=limit, verbose=verbose, json_output=json_output
    )
    raise typer.Exit(code=exit_code)


@event_app.command(name="generate")
def watcher_event_generate_cli(
    session_selector: str = typer.Argument(
        ...,
        help="Session selector: 'list' to show sessions, numbers (1, 1-3), or UUID/prefix",
    ),
):
    """Generate an event from selected sessions.

    Examples:
        aline watcher event generate list    (show available sessions)
        aline watcher event generate 1
        aline watcher event generate 1-3
        aline watcher event generate 1,3,5-7
        aline watcher event generate abc123de
    """
    exit_code = watcher.watcher_event_generate_command(session_selector=session_selector)
    raise typer.Exit(code=exit_code)


@event_app.command(name="show")
def watcher_event_show_cli(
    event_selector: str = typer.Argument(
        ..., help="Event index or UUID/prefix (from 'aline watcher event list')"
    ),
):
    """Show details of a specific event, including its sessions."""
    exit_code = watcher.watcher_event_show_command(event_selector=event_selector)
    raise typer.Exit(code=exit_code)


@event_app.command(name="delete")
def watcher_event_delete_cli(
    event_selector: str = typer.Argument(
        ...,
        help="Event selector: number (1), range (1-3), multiple (1,3,5-7), UUID/prefix, or 'all'",
    ),
):
    """Delete events by number.

    Examples:
        aline watcher event delete 1
        aline watcher event delete 2-5
        aline watcher event delete all
    """
    exit_code = watcher.watcher_event_delete_command(event_selector=event_selector)
    raise typer.Exit(code=exit_code)


@event_app.command(name="revise-slack")
def watcher_event_revise_slack_cli(
    instruction: str = typer.Argument(
        ...,
        help="Revision instruction (e.g., 'make it shorter', 'add more technical details')",
    ),
    input_data: str = typer.Option(
        ...,
        "--input",
        "-i",
        help="JSON string from 'aline share export --json --no-preview'",
    ),
    provider: str = typer.Option(
        "auto",
        "--provider",
        "-p",
        help="LLM provider: auto, claude, openai",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results in JSON format (same as aline share export --json)"
    ),
):
    """Revise the Slack share message for an event.

    Examples:
        aline watcher event revise-slack "make it shorter" -i '{"event_id": "...", ...}'
        aline watcher event revise-slack "add emojis" -i "$(aline share export -i 1 --no-preview --json)" --json
    """
    import json

    try:
        input_json = json.loads(input_data)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON input: {e}", err=True)
        raise typer.Exit(code=1)

    exit_code = watcher.watcher_event_revise_slack_command(
        input_json=input_json,
        instruction=instruction,
        json_output=json_output,
    )
    raise typer.Exit(code=exit_code)


@session_app.command(name="list")
def watcher_session_list_cli(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
    page: int = typer.Option(1, "--page", "-p", min=1, help="Page number (1-based)"),
    per_page: int = typer.Option(30, "--per-page", "-n", min=1, help="Sessions per page"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
    detect_turns: bool = typer.Option(
        False, "--detect-turns", help="Compute total turns from files (uses mtime cache)"
    ),
    records: bool = typer.Option(
        False, "--records", help="Include turn titles for each session (JSON mode only)"
    ),
    include_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Include empty sessions (0 turns). Only effective with --detect-turns",
    ),
):
    """List discovered sessions with tracking status."""
    exit_code = watcher.watcher_session_list_command(
        verbose=verbose,
        page=page,
        per_page=per_page,
        json_output=json_output,
        detect_turns=detect_turns,
        records=records,
        include_all=include_all,
    )
    raise typer.Exit(code=exit_code)


@session_app.command(name="import")
def watcher_session_import_cli(
    session_id: str = typer.Argument(..., help="Number (1), range (1-10), or session ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Re-import already tracked sessions"),
    debug: Optional[str] = typer.Option(
        None, "--debug", help="Path to debug log file for troubleshooting"
    ),
    regenerate: bool = typer.Option(
        False,
        "--regenerate",
        "-r",
        help="Regenerate summaries even if content unchanged (bypass hash dedup)",
    ),
    queue: bool = typer.Option(
        True,
        "--queue/--sync",
        help="Queue turn jobs for background processing (default: queue)",
    ),
):
    """Import sessions by number, range, or session ID."""
    exit_code = watcher.watcher_session_import_command(
        session_id=session_id,
        force=force,
        debug=debug,
        regenerate=regenerate,
        queue=queue,
    )
    raise typer.Exit(code=exit_code)


@session_app.command(name="show")
def watcher_session_show_cli(
    session_selector: str = typer.Argument(
        ..., help="Session index or UUID/prefix (from 'aline watcher session list')"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
):
    """Show all turns for a specific session."""
    exit_code = watcher.watcher_session_show_command(
        session_selector=session_selector, json_output=json_output
    )
    raise typer.Exit(code=exit_code)


@session_app.command(name="refresh")
def watcher_session_refresh_cli(
    session_selector: str = typer.Argument(
        ...,
        help="Session selector: number (1), range (1-5), multiple (1,3,5-7), or UUID/prefix",
    ),
):
    """Refresh (regenerate) all turn summaries for session(s).

    This command regenerates the LLM summary for each turn in the session(s),
    then regenerates the session-level summary. Highest priority, ignores debounce.

    Examples:
        aline watcher session refresh 1
        aline watcher session refresh 1-5
        aline watcher session refresh 1,3,5-7
        aline watcher session refresh abc123de
    """
    exit_code = watcher.watcher_session_refresh_command(session_selector=session_selector)
    raise typer.Exit(code=exit_code)


@session_app.command(name="delete")
def watcher_session_delete_cli(
    session_selector: str = typer.Argument(
        ...,
        help="Session index or UUID/prefix (from 'aline watcher session list')",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Delete a session from the database.

    This permanently deletes the session and all its turns from the database.
    The original session files are not affected.

    Examples:
        aline watcher session delete 1
        aline watcher session delete abc123de
        aline watcher session delete 1 --force
    """
    exit_code = watcher.watcher_session_delete_command(
        session_selector=session_selector, force=force
    )
    raise typer.Exit(code=exit_code)


# Push/Pull commands


# Share command group
share_app = typer.Typer(help="Export and share session history")
app.add_typer(share_app, name="share")


@share_app.command(name="export")
def share_export_cli(
    indices: Optional[str] = typer.Option(
        None,
        "--indices",
        "-i",
        help="Event index (e.g., '1') or event_id UUID prefix (e.g., 'ea48983b')",
    ),
    local: bool = typer.Option(
        False, "--local", help="Export to local JSON only (skip interactive web upload)"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", help="[DEPRECATED] Interactive mode is now default"
    ),
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Username for local export file"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Custom output directory for local export"
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-p",
        help="Password for encrypted share (auto-generated if not provided)",
    ),
    expiry_days: int = typer.Option(7, "--expiry", help="Number of days before share expires"),
    max_views: int = typer.Option(100, "--max-views", help="Maximum number of views allowed"),
    no_preview: bool = typer.Option(
        False,
        "--no-preview",
        help="Skip UI preview and editing (auto-accept LLM-generated content)",
    ),
    mcp: bool = typer.Option(
        True,
        "--mcp/--no-mcp",
        help="Include MCP usage instructions for agent-to-agent communication (default: enabled)",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
    size_report: bool = typer.Option(
        False,
        "--size-report",
        help="Print a size breakdown (largest JSONL lines) to explain big uploads",
    ),
    compact: bool = typer.Option(
        True,
        "--compact/--no-compact",
        help="Compact exported records to reduce upload size (omit tool logs, drop thinking/signatures; default: enabled for uploads)",
    ),
    max_tool_result_chars: int = typer.Option(
        8000,
        "--max-tool-result-chars",
        help="(With --compact) Max chars to keep for each tool_result content",
    ),
    max_tool_command_chars: int = typer.Option(
        2000,
        "--max-tool-command-chars",
        help="(With --compact) Max chars to keep for each tool_use input.command",
    ),
    dump_payload_dir: Optional[str] = typer.Option(
        None,
        "--dump-payload-dir",
        help="Save full+compact export payload JSONs to this directory (dev/debug)",
    ),
    new_link: bool = typer.Option(
        False,
        "--new-link",
        help="Create a new share link even if this event was shared before",
    ),
):
    """
    Export chat history as encrypted shareable link (default) or local JSON.

    Interactive mode (default): Creates encrypted web-accessible chatbot
    Local mode (--local): Exports to JSON file only
    """
    # Deprecation warning
    if interactive:
        print("⚠️  Warning: --interactive flag is deprecated.")
        print("   Interactive mode is now default. Use --local for JSON export.\n")

    # Determine mode (backward compatible)
    use_local_mode = local or username or output_dir

    if use_local_mode:
        # Local JSON export
        output_path = Path(output_dir) if output_dir else None
        exit_code = export_shares.export_shares_command(
            indices=indices, username=username, output_dir=output_path
        )
    else:
        # Interactive web export (DEFAULT)
        exit_code = export_shares.export_shares_interactive_command(
            indices=indices,
            password=password,
            expiry_days=expiry_days,
            max_views=max_views,
            enable_preview=not no_preview,
            enable_mcp=mcp,
            json_output=json_output,
            size_report=size_report,
            compact=compact,
            max_tool_result_chars=max_tool_result_chars,
            max_tool_command_chars=max_tool_command_chars,
            dump_payload_dir=Path(dump_payload_dir) if dump_payload_dir else None,
            force_new_link=new_link,
        )
    raise typer.Exit(code=exit_code)


@share_app.command(name="import")
def share_import_cli(
    share_url: str = typer.Argument(..., help="Share URL to import"),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Password for encrypted share"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Re-import existing sessions (override duplicates)"
    ),
):
    """
    Import shared conversation from URL into local database.

    This command downloads a shared conversation and imports it with full
    Event/Session/Turn structure preserved. Supports both v1.0 (legacy) and
    v2.0 (enhanced) share formats.

    Examples:
      aline share import https://realign-server.vercel.app/share/abc123
      aline share import https://realign-server.vercel.app/share/xyz789 --password mypass
      aline share import <url> --force  # Re-import even if exists
    """
    from .commands import import_shares

    exit_code = import_shares.import_share_command(
        share_url=share_url, password=password, force=force
    )
    raise typer.Exit(code=exit_code)


@app.command()
def version():
    """Show ReAlign version and database schema version."""
    upgrade.version_command()


@app.command()
def dashboard(
    ctx: typer.Context,
    dev: bool = typer.Option(False, "--dev", help="Enable developer mode (shows Watcher and Worker tabs)"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging to ~/.aline/.logs/dashboard.log"),
):
    """Open the interactive TUI dashboard."""
    import os
    import traceback

    # Set debug log level if requested
    if debug:
        os.environ["REALIGN_LOG_LEVEL"] = "DEBUG"

    from .logging_config import setup_logger

    # Initialize logger before dashboard
    logger = setup_logger("realign.dashboard", "dashboard.log")
    logger.info(f"Dashboard command invoked (dev={dev}, debug={debug})")

    try:
        # Check terminal mode
        terminal_mode = os.environ.get("ALINE_TERMINAL_MODE", "").strip().lower()
        use_native_terminal = terminal_mode in {"native", "iterm2", "iterm", "kitty"}

        if not use_native_terminal:
            # Only bootstrap tmux for tmux mode (default)
            from .dashboard.tmux_manager import bootstrap_dashboard_into_tmux

            bootstrap_dashboard_into_tmux()
        elif terminal_mode in {"iterm2", "iterm"}:
            # Set up split pane layout for iTerm2
            try:
                from .dashboard.backends.iterm2 import setup_split_pane_layout_sync

                right_pane_session_id = setup_split_pane_layout_sync()
                if right_pane_session_id:
                    os.environ["ALINE_ITERM2_RIGHT_PANE"] = right_pane_session_id
                    logger.info(f"Set up split pane with right pane: {right_pane_session_id}")
            except Exception as e:
                logger.warning(f"Could not set up split pane: {e}")

        from .dashboard.app import AlineDashboard

        # Use dev flag from this command or inherit from parent context
        dev_mode = dev or (ctx.obj.get("dev", False) if ctx.obj else False)
        dash = AlineDashboard(dev_mode=dev_mode, use_native_terminal=use_native_terminal)
        dash.run()
    except Exception as e:
        logger.error(f"Dashboard crashed: {e}\n{traceback.format_exc()}")
        # Re-raise so user sees the error
        raise


# Restore command group
restore_app = typer.Typer(help="Restore session data from database to original formats")
app.add_typer(restore_app, name="restore")


@restore_app.command(name="claude")
def restore_claude_cli(
    session_selector: Optional[str] = typer.Argument(
        None,
        help="Session selector: 'list' to show sessions, number (1), range (1-3), or UUID prefix",
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory (default: /tmp/aline_restore)"
    ),
):
    """
    Restore Claude sessions from database to original JSONL format.

    The turn_content stored in aline.db will be restored to JSONL files.

    Examples:
        aline restore claude list              # List available Claude sessions
        aline restore claude                   # Restore all Claude sessions
        aline restore claude 1                 # Restore session #1
        aline restore claude 1-5               # Restore sessions 1-5
        aline restore claude abc123            # Restore session by UUID prefix
        aline restore claude -o ./my_restore   # Custom output directory
    """
    from pathlib import Path

    list_sessions = session_selector == "list"
    selector = None if list_sessions else session_selector
    out_path = Path(output_dir) if output_dir else None

    exit_code = restore.restore_claude_command(
        session_selector=selector,
        output_dir=out_path,
        list_sessions=list_sessions,
    )
    raise typer.Exit(code=exit_code)


@restore_app.command(name="codex")
def restore_codex_cli(
    session_selector: Optional[str] = typer.Argument(
        None,
        help="Session selector: 'list' to show sessions, number (1), range (1-3), or UUID prefix",
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory (default: /tmp/aline_restore)"
    ),
):
    """
    Restore Codex sessions from database to original JSONL format.

    The turn_content stored in aline.db will be restored to JSONL files.

    Examples:
        aline restore codex list              # List available Codex sessions
        aline restore codex                   # Restore all Codex sessions
        aline restore codex 1                 # Restore session #1
        aline restore codex 1-5               # Restore sessions 1-5
        aline restore codex abc123            # Restore session by UUID prefix
        aline restore codex -o ./my_restore   # Custom output directory
    """
    from pathlib import Path

    list_sessions = session_selector == "list"
    selector = None if list_sessions else session_selector
    out_path = Path(output_dir) if output_dir else None

    exit_code = restore.restore_codex_command(
        session_selector=selector,
        output_dir=out_path,
        list_sessions=list_sessions,
    )
    raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()

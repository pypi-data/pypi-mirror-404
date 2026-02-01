"""Context command for managing search scope.

This module provides CLI commands for loading, showing, and clearing
search contexts in ~/.aline/load.json.
"""

import os
from typing import List, Optional

from rich.console import Console
from rich.table import Table

from ..context import (
    CONTEXT_ID_ENV_VAR,
    add_context,
    clear_context,
    get_context_by_id,
    load_context_config,
    resolve_current_context,
)

console = Console()


def context_load_command(
    sessions: Optional[List[str]] = None,
    events: Optional[List[str]] = None,
    context_id: Optional[str] = None,
    workspace: Optional[str] = None,
) -> int:
    """Load sessions/events into a search context.

    Args:
        sessions: Session IDs to add to the context
        events: Event IDs to add to the context
        context_id: Optional context ID (otherwise uses current workspace)
        workspace: Optional workspace path (otherwise uses cwd)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if not sessions and not events:
        console.print("[red]Error:[/red] Must specify at least one session (-s) or event (-e)")
        return 1

    try:
        entry = add_context(
            sessions=sessions,
            events=events,
            context_id=context_id,
            workspace=workspace,
        )

        # Display what was loaded
        console.print("[green]Context loaded successfully.[/green]")
        console.print()

        if context_id:
            console.print(f"[bold]Context ID:[/bold] {context_id}")
        if entry.workspace:
            console.print(f"[bold]Workspace:[/bold] {entry.workspace}")

        if entry.context_sessions:
            console.print(f"[bold]Sessions ({len(entry.context_sessions)}):[/bold]")
            for sid in entry.context_sessions[:10]:
                console.print(f"  - {sid[:8]}...")
            if len(entry.context_sessions) > 10:
                console.print(f"  ... and {len(entry.context_sessions) - 10} more")

        if entry.context_events:
            console.print(f"[bold]Events ({len(entry.context_events)}):[/bold]")
            for eid in entry.context_events[:10]:
                console.print(f"  - {eid[:8]}...")
            if len(entry.context_events) > 10:
                console.print(f"  ... and {len(entry.context_events) - 10} more")

        console.print()
        console.print("[dim]Searches will now be limited to this context.[/dim]")
        console.print("[dim]Use 'aline context clear' to remove the context.[/dim]")
        console.print("[dim]Use 'aline search --no-context' to search all.[/dim]")

        return 0

    except Exception as e:
        console.print(f"[red]Error loading context:[/red] {e}")
        return 1


def context_show_command(
    context_id: Optional[str] = None,
    show_all: bool = False,
) -> int:
    """Show current or specified context.

    Args:
        context_id: Optional context ID to show (otherwise uses current)
        show_all: Show all contexts in the configuration

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        config = load_context_config()

        if config is None:
            console.print("[dim]No context configuration found (~/.aline/load.json).[/dim]")
            console.print("[dim]Use 'aline context load' to create one.[/dim]")
            return 0

        if show_all:
            # Show all contexts
            if not config.contexts:
                console.print("[dim]No contexts defined.[/dim]")
                return 0

            table = Table(title="All Contexts")
            table.add_column("ID/Workspace", style="cyan")
            table.add_column("Sessions", justify="right")
            table.add_column("Events", justify="right")
            table.add_column("Loaded At")

            for entry in config.contexts:
                id_or_ws = entry.context_id or entry.workspace or "(unknown)"
                if len(id_or_ws) > 40:
                    id_or_ws = "..." + id_or_ws[-37:]
                table.add_row(
                    id_or_ws,
                    str(len(entry.context_sessions)),
                    str(len(entry.context_events)),
                    entry.loaded_at[:19] if entry.loaded_at else "-",
                )

            console.print(table)
            return 0

        # Show specific or current context
        if context_id:
            entry = get_context_by_id(context_id, config)
            if not entry:
                console.print(f"[red]Context not found:[/red] {context_id}")
                return 1
        else:
            entry = resolve_current_context(config)

        if entry is None:
            console.print("[dim]No active context.[/dim]")
            env_val = os.environ.get(CONTEXT_ID_ENV_VAR)
            if env_val:
                console.print(
                    f"[dim]ALINE_CONTEXT_ID is set to '{env_val}' but no matching context found.[/dim]"
                )
            console.print("[dim]Searches will include all sessions/events.[/dim]")
            return 0

        # Display the context
        console.print("[bold]Active Context[/bold]")
        console.print()

        if entry.context_id:
            console.print(f"[bold]Context ID:[/bold] {entry.context_id}")
        if entry.workspace:
            console.print(f"[bold]Workspace:[/bold] {entry.workspace}")
        if entry.loaded_at:
            console.print(f"[bold]Loaded at:[/bold] {entry.loaded_at}")

        console.print()

        if entry.context_sessions:
            console.print(f"[bold]Sessions ({len(entry.context_sessions)}):[/bold]")
            for sid in entry.context_sessions:
                console.print(f"  - {sid}")
        else:
            console.print("[dim]No sessions in context.[/dim]")

        if entry.context_events:
            console.print(f"[bold]Events ({len(entry.context_events)}):[/bold]")
            for eid in entry.context_events:
                console.print(f"  - {eid}")
        else:
            console.print("[dim]No events in context.[/dim]")

        return 0

    except Exception as e:
        console.print(f"[red]Error showing context:[/red] {e}")
        return 1


def context_clear_command(
    context_id: Optional[str] = None,
) -> int:
    """Clear the current or specified context.

    Args:
        context_id: Optional context ID to clear (otherwise uses current)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        cleared = clear_context(context_id=context_id)

        if cleared:
            if context_id:
                console.print(f"[green]Context '{context_id}' cleared.[/green]")
            else:
                console.print("[green]Context cleared.[/green]")
            console.print("[dim]Searches will now include all sessions/events.[/dim]")
        else:
            console.print("[dim]No matching context found to clear.[/dim]")

        return 0

    except Exception as e:
        console.print(f"[red]Error clearing context:[/red] {e}")
        return 1

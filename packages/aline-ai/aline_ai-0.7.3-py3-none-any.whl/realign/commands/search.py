"""Search command for exploring project history via SQLite."""

import re
import json
import typer
from rich.console import Console
from rich.text import Text
from rich.markdown import Markdown
from typing import List, Tuple, Optional

from ..db import get_database

console = Console()


def _extract_text_from_jsonl(content: str) -> List[Tuple[int, str]]:
    """Extract searchable text lines from JSONL content.

    Returns:
        List of (line_number, text) tuples
    """
    results = []
    for line_no, line in enumerate(content.split("\n"), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            text = _extract_text_from_json(data)
            if text:
                # Split multi-line text and preserve line numbers
                for sub_line in text.split("\n"):
                    if sub_line.strip():
                        results.append((line_no, sub_line))
        except json.JSONDecodeError:
            continue
    return results


def _extract_text_from_json(data: dict) -> Optional[str]:
    """Extract human-readable text from a JSONL record."""
    if not isinstance(data, dict):
        return None

    # Claude Code format
    msg_type = data.get("type")
    if msg_type == "assistant":
        parts = []
        for item in data.get("message", {}).get("content", []):
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(parts) if parts else None

    if msg_type == "user":
        content = data.get("message", {}).get("content", [])
        if isinstance(content, str):
            return content
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(parts) if parts else None

    return None


def _find_matches(
    text: str, pattern: str, is_regex: bool, ignore_case: bool
) -> List[Tuple[int, int]]:
    """Find all match spans in text.

    Returns:
        List of (start, end) tuples for each match
    """
    if not text:
        return []

    flags = re.IGNORECASE if ignore_case else 0

    if is_regex:
        try:
            regex = re.compile(pattern, flags)
            return [(m.start(), m.end()) for m in regex.finditer(text)]
        except re.error:
            return []
    else:
        # Simple substring match
        search_text = text.lower() if ignore_case else text
        search_pattern = pattern.lower() if ignore_case else pattern
        matches = []
        start = 0
        while True:
            idx = search_text.find(search_pattern, start)
            if idx < 0:
                break
            matches.append((idx, idx + len(pattern)))
            start = idx + 1
        return matches


def _print_grep_line(
    source_id: str,
    line_no: int,
    text: str,
    matches: List[Tuple[int, int]],
    show_line_numbers: bool,
    source_category: str,  # 'event', 'turn', 'session', 'content'
    field_type: str,  # 'title', 'desc', 'summary', 'content'
    session_id: Optional[str] = None,
    turn_number: Optional[int] = None,
) -> None:
    """Print a single match line with new format.

    Format:
      - Turns: [session]xxx | [turn]xxx | [title/summary] | [line]n: matched_text
      - Events: [event]xxx | [title/desc] | [line]n: matched_text
      - Sessions: [session]xxx | [title/summary] | [line]n: matched_text
      - Content: [session]xxx | [turn]xxx | [line]n: matched_text
    """
    from rich.text import Text

    # Build prefix with pipe separators and labels
    parts = []
    prefix = Text()

    # First field: source category and ID
    if source_category == "event":
        prefix.append("[event]", style="dim")
        prefix.append(source_id, style="dim")
    elif source_category == "turn":
        if session_id:
            prefix.append("[session]", style="dim")
            prefix.append(session_id, style="dim")
        else:
            prefix.append("[session]", style="dim")
            prefix.append(" ", style="dim")
        prefix.append(" | ", style="dim")
        prefix.append("[turn]", style="dim")
        prefix.append(source_id, style="dim")
    elif source_category == "session":
        prefix.append("[session]", style="dim")
        prefix.append(source_id, style="dim")
    elif source_category == "content":
        if session_id:
            prefix.append("[session]", style="dim")
            prefix.append(session_id, style="dim")
        else:
            prefix.append("[session]", style="dim")
            prefix.append(" ", style="dim")
        prefix.append(" | ", style="dim")
        prefix.append("[turn]", style="dim")
        prefix.append(source_id, style="dim")

    # Second field: field type (not for content)
    if source_category == "content":
        # Content doesn't have field type in the middle
        pass
    else:
        prefix.append(" | ", style="dim")
        prefix.append(f"[{field_type}]", style="dim")

    # Third field: line number
    if show_line_numbers:
        prefix.append(" | ", style="dim")
        prefix.append(f"[line {line_no}]", style="dim")

    prefix.append(": ", style="")

    # Build highlighted text
    highlighted = Text()
    last_end = 0
    for start, end in sorted(matches):
        if start > last_end:
            highlighted.append(text[last_end:start])
        highlighted.append(text[start:end], style="bold red")
        last_end = end
    if last_end < len(text):
        highlighted.append(text[last_end:])

    console.print(prefix, end="")
    console.print(highlighted)


def _grep_search_content(
    content: str,
    pattern: str,
    source_id: str,
    is_regex: bool,
    ignore_case: bool,
    show_line_numbers: bool,
    session_id: Optional[str] = None,
    turn_number: Optional[int] = None,
) -> int:
    """Search content and print grep-style output.

    Returns:
        Number of matches found
    """
    # Use raw lines instead of extracting text from JSONL
    match_count = 0
    lines = [(i, line) for i, line in enumerate(content.splitlines(), 1) if line.strip()]

    for line_no, text in lines:
        matches = _find_matches(text, pattern, is_regex, ignore_case)
        if matches:
            _print_grep_line(
                source_id,
                line_no,
                text,
                matches,
                show_line_numbers,
                source_category="content",
                field_type="content",
                session_id=session_id,
                turn_number=turn_number,
            )
            match_count += 1

    return match_count


def _resolve_id_prefixes(db, table: str, selectors: str) -> List[str]:
    """Resolve a comma-separated list of IDs or prefixes to full IDs."""
    if not selectors:
        return []

    prefixes = [s.strip() for s in selectors.split(",") if s.strip()]
    resolved_ids = []

    # Use a raw connection to check for prefixes
    conn = db._get_connection()
    cursor = conn.cursor()

    for prefix in prefixes:
        # If it's already a full UUID (36 chars), just add it
        if len(prefix) == 36:
            resolved_ids.append(prefix)
            continue

        # Search for full IDs matching the prefix
        cursor.execute(f"SELECT id FROM {table} WHERE id LIKE ?", (f"{prefix}%",))
        matches = [row[0] for row in cursor.fetchall()]
        if matches:
            resolved_ids.extend(matches)
        else:
            # If no matches found, keep the prefix as is
            resolved_ids.append(prefix)

    return list(set(resolved_ids))


def search_command(
    query: str = typer.Argument(..., help="Search query (keywords or regex pattern)"),
    type: str = typer.Option(
        "all", "--type", "-t", help="Search type: all, event, turn, session, content"
    ),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    # Regex options
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
    line_numbers: bool = typer.Option(
        True, "-n/--no-line-numbers", help="Show line numbers (default: True)"
    ),
    sessions: Optional[str] = typer.Option(
        None,
        "--sessions",
        "-s",
        help="Limit search to specific sessions (comma-separated IDs)",
    ),
    events: Optional[str] = typer.Option(
        None,
        "--events",
        "-e",
        help="Limit search to sessions within specific events (comma-separated IDs)",
    ),
    turns: Optional[str] = typer.Option(
        None,
        "--turns",
        help="Limit content search to specific turns (comma-separated IDs)",
    ),
    no_context: bool = typer.Option(
        False,
        "--no-context",
        help="Ignore loaded context from ~/.aline/load.json",
    ),
) -> int:
    """
    Search project history, events, turns, sessions, and content.

    This command uses the ReAlign SQLite database to perform keyword or regex searches.

    Search types:
      - event: Search event title and description
      - turn: Search turn title and summary only
      - session: Search session title and summary
      - content: Search full turn content (JSONL)
      - all: Search events, turns, and sessions (default)

    Note: 'all' does not include 'content' search as it can be very slow.
    Use '-t content' to search full JSONL dialogue history.

    Examples:
        aline search "sqlite.*migration"        # Regex search (default)
        aline search "auth" --no-regex          # Simple keyword search
        aline search -t turn "refactor"         # Search turn titles/summaries
        aline search -t content "error|bug"     # Search full content
        aline search -t session "migration"     # Search sessions
        aline search "pattern" -c               # Count matches only
        aline search "bug" -s abc123,def456     # Search within specific sessions
        aline search "bug" -e event1,event2     # Search within specific events
        aline search "bug" -t content --turns turn1,turn2  # Search within specific turns
    """
    try:
        db = get_database()

        results = {}
        total_matches = 0

        # Apply context filtering unless --no-context
        context_session_ids = None
        context_event_ids = None
        if not no_context:
            from ..context import get_context_session_ids, get_context_event_ids

            context_session_ids = get_context_session_ids()
            context_event_ids = get_context_event_ids()

        # Apply agent scoping if ALINE_AGENT_ID is set
        agent_session_ids = None
        if not no_context:
            import os

            agent_id = os.environ.get("ALINE_AGENT_ID")
            if agent_id:
                agent_sessions = db.get_sessions_by_agent_id(agent_id)
                # Always set agent_session_ids when agent_id exists
                # (empty list means no sessions for this agent -> empty results)
                agent_session_ids = [s.id for s in agent_sessions]

        # Parse session IDs if provided (resolve prefixes)
        session_ids = _resolve_id_prefixes(db, "sessions", sessions) or None

        # Intersect with agent sessions first (highest priority)
        if agent_session_ids is not None:
            if session_ids:
                session_ids = list(set(session_ids) & set(agent_session_ids))
            else:
                session_ids = agent_session_ids if agent_session_ids else []

        # Intersect with context sessions
        if context_session_ids:
            if session_ids:
                session_ids = list(set(session_ids) & set(context_session_ids))
            else:
                session_ids = context_session_ids

        # Parse event IDs and get associated session IDs
        event_ids = _resolve_id_prefixes(db, "events", events) or None

        # Intersect with context events
        if context_event_ids:
            if event_ids:
                event_ids = list(set(event_ids) & set(context_event_ids))
            else:
                event_ids = context_event_ids

        if event_ids:
            # Get all session IDs associated with these events
            event_session_ids: List[str] = []
            for event_id in event_ids:
                event_sessions = db.get_sessions_for_event(event_id)
                event_session_ids.extend([s.id for s in event_sessions])
            # Merge with directly specified session IDs
            if session_ids:
                # Union: sessions from both --sessions and --events
                session_ids = list(set(session_ids) | set(event_session_ids))
            else:
                session_ids = list(set(event_session_ids)) if event_session_ids else None

        # Parse turn IDs if provided (for content search)
        turn_ids = _resolve_id_prefixes(db, "turns", turns) or None

        # 1. Search Events (events don't have session scope, skip if sessions/events filter is active)
        # Use 'is None' to distinguish "no filter" from "empty filter results"
        if type in ("all", "event") and session_ids is None and event_ids is None:
            events = db.search_events(query, limit=limit, use_regex=regex, ignore_case=ignore_case)
            results["events"] = events

        # 2. Search Turns (skip if session filter results in empty list)
        if type in ("all", "turn"):
            if session_ids is not None and len(session_ids) == 0:
                results["turns"] = []
            else:
                turns = db.search_conversations(
                    query,
                    limit=limit,
                    use_regex=regex,
                    ignore_case=ignore_case,
                    session_ids=session_ids if session_ids else None,
                )
                results["turns"] = turns

        # 3. Search Sessions (skip if session filter results in empty list)
        if type in ("all", "session"):
            if session_ids is not None and len(session_ids) == 0:
                results["sessions"] = []
            else:
                sessions_results = db.search_sessions(
                    query,
                    limit=limit,
                    use_regex=regex,
                    ignore_case=ignore_case,
                    session_ids=session_ids if session_ids else None,
                )
                results["sessions"] = sessions_results

        # 4. Search Turn Content (skip if session filter results in empty list)
        if type == "content":
            if session_ids is not None and len(session_ids) == 0:
                results["content"] = []
            else:
                content_results = db.search_turn_content(
                    query,
                    limit=limit,
                    use_regex=regex,
                    ignore_case=ignore_case,
                    session_ids=session_ids if session_ids else None,
                    turn_ids=turn_ids,
                )
                results["content"] = content_results

        # === Grep-style output for regex mode ===
        if regex:
            if not count_only:
                console.print(f"\n[bold]Regex Search:[/bold] '{query}'")

            # Events grep output
            if results.get("events"):
                for event in results["events"]:
                    # Search in title and description
                    for field_name, field_value in [
                        ("title", event.title),
                        ("desc", event.description),
                    ]:
                        if field_value:
                            matches = _find_matches(field_value, query, True, ignore_case)
                            if matches:
                                if not count_only:
                                    _print_grep_line(
                                        event.id,
                                        1,
                                        field_value[:200],
                                        matches,
                                        line_numbers,
                                        source_category="event",
                                        field_type=field_name,
                                    )
                                total_matches += 1

            # Turns grep output (title/summary only)
            if results.get("turns"):
                for turn in results["turns"]:
                    # Search in title and summary
                    for field_name, field_value in [
                        ("title", turn.get("title")),
                        ("summary", turn.get("summary")),
                    ]:
                        if field_value:
                            matches = _find_matches(field_value, query, True, ignore_case)
                            if matches:
                                if not count_only:
                                    _print_grep_line(
                                        turn["turn_id"],
                                        1,
                                        field_value[:200],
                                        matches,
                                        line_numbers,
                                        source_category="turn",
                                        field_type=field_name,
                                        session_id=turn.get("session_id"),
                                        turn_number=turn.get("turn_number"),
                                    )
                                total_matches += 1

            # Sessions grep output
            if results.get("sessions"):
                for session in results["sessions"]:
                    # Search in title and summary
                    for field_name, field_value in [
                        ("title", session.session_title),
                        ("summary", session.session_summary),
                    ]:
                        if field_value:
                            matches = _find_matches(field_value, query, True, ignore_case)
                            if matches:
                                if not count_only:
                                    _print_grep_line(
                                        session.id,
                                        1,
                                        field_value[:200],
                                        matches,
                                        line_numbers,
                                        source_category="session",
                                        field_type=field_name,
                                    )
                                total_matches += 1

            # Content grep output (full JSONL content)
            if results.get("content"):
                for item in results["content"]:
                    content = item.get("content", "")
                    if content:
                        match_count = 0
                        if not count_only:
                            match_count = _grep_search_content(
                                content,
                                query,
                                item["turn_id"],
                                True,
                                ignore_case,
                                line_numbers,
                                session_id=item.get("session_id"),
                                turn_number=item.get("turn_number"),
                            )
                        else:
                            # Just count matches
                            lines = content.splitlines()
                            for text in lines:
                                if _find_matches(text, query, True, ignore_case):
                                    match_count += 1
                        total_matches += match_count

            # Print summary
            console.print()
            event_count = len(results.get("events", []))
            turn_count = len(results.get("turns", []))
            session_count = len(results.get("sessions", []))
            summary_parts = [
                f"{total_matches} matches in {event_count} events",
                f"{turn_count} turns",
                f"{session_count} sessions",
            ]

            if type == "content":
                content_count = len(results.get("content", []))
                summary_parts.append(f"{content_count} content items")

            console.print(f"[dim]Found {', '.join(summary_parts)}.[/dim]")

            # Check if any result count hits the limit - suggest increasing limit
            hit_limit = (
                event_count == limit
                or turn_count == limit
                or session_count == limit
                or (type == "content" and len(results.get("content", [])) == limit)
            )
            if hit_limit:
                console.print(
                    f"[yellow]Results may be truncated (limit={limit}). "
                    f"Use --limit N to see more results.[/yellow]"
                )

        # === Original structured output for non-regex mode ===
        else:
            if type == "all":
                console.print(f"\n[bold]Search Results for:[/bold] '{query}'\n")

            # -- Events Output --
            if results.get("events"):
                console.print(f"[bold cyan]Events ({len(results['events'])})[/bold cyan]")
                for event in results["events"]:
                    console.print(f"• [bold]{event.title}[/bold] (ID: {event.id[:8]})")
                    if event.description:
                        console.print(f"  {event.description}")
                    generated_by = event.event_type
                    if generated_by == "task":
                        generated_by = "user"
                    generated_by_display = {
                        "user": "user",
                        "preset_day": "preset(day)",
                        "preset_week": "preset(week)",
                    }.get(generated_by, generated_by)
                    console.print(f"  [dim]Generated by: {generated_by_display}[/dim]")
                    console.print("")
            elif type == "event" or (type == "all" and not results.get("events")):
                if type == "event":
                    console.print("[dim]No events found.[/dim]")

            # -- Turns Output --
            if results.get("turns"):
                console.print(f"[bold green]Turns ({len(results['turns'])})[/bold green]")
                for turn in results["turns"]:
                    title = turn.get("title") or "(No Title)"
                    summary = turn.get("summary") or ""
                    console.print(f"• [bold]{title}[/bold] (Turn #{turn['turn_number']})")
                    if summary:
                        console.print(f"  {summary}")
                    console.print(f"  [dim]ID: {turn['turn_id'][:8]}[/dim]")
                    console.print("")
            elif type == "turn" or (type == "all" and not results.get("turns")):
                if type == "turn":
                    console.print("[dim]No turns found.[/dim]")

            # -- Sessions Output --
            if results.get("sessions"):
                console.print(f"[bold magenta]Sessions ({len(results['sessions'])})[/bold magenta]")
                for session in results["sessions"]:
                    title = session.session_title or "(No Title)"
                    summary = session.session_summary or ""
                    console.print(f"• [bold]{title}[/bold] (ID: {session.id[:8]})")
                    if summary:
                        # Truncate long summaries
                        summary_preview = summary[:200] + "..." if len(summary) > 200 else summary
                        console.print(f"  {summary_preview}")
                    console.print("")
            elif type == "session" or (type == "all" and not results.get("sessions")):
                if type == "session":
                    console.print("[dim]No sessions found.[/dim]")

            # -- Content Output --
            if results.get("content"):
                console.print(f"[bold yellow]Content ({len(results['content'])})[/bold yellow]")
                for item in results["content"]:
                    title = item.get("title") or "(No Title)"
                    console.print(f"• [bold]{title}[/bold] (Turn #{item['turn_number']})")
                    console.print(f"  [dim]ID: {item['turn_id'][:8]}[/dim]")
                    if verbose:
                        console.print(Markdown(item["content_preview"]))
                    console.print("")
            elif type == "content" or (type == "all" and not results.get("content")):
                if type == "content":
                    console.print("[dim]No content found.[/dim]")

            # -- Hints --
            if not verbose and (
                results.get("events")
                or results.get("turns")
                or results.get("sessions")
                or results.get("content")
            ):
                console.print("\n[bold blue]Next steps for exploration:[/bold blue]")
                if results.get("events"):
                    console.print(
                        "  • To explore an event's sessions: [green]aline watcher event show <event_id>[/green]"
                    )
                if results.get("turns") or results.get("sessions"):
                    console.print(
                        "  • To view full session dialogue: [green]aline watcher session show <session_id>[/green]"
                    )
                if type != "content":
                    console.print(
                        "  • To search deep inside raw dialogue content: [green]aline search -t content '<query>'[/green]"
                    )

                console.print(
                    "\n[dim]Tip: Use --verbose to see Markdown previews, or --no-regex for exact keyword match.[/dim]"
                )

                # Check if any result count hits the limit - suggest increasing limit
                event_count = len(results.get("events", []))
                turn_count = len(results.get("turns", []))
                session_count = len(results.get("sessions", []))
                content_count = len(results.get("content", []))
                hit_limit = (
                    event_count == limit
                    or turn_count == limit
                    or session_count == limit
                    or content_count == limit
                )
                if hit_limit:
                    console.print(
                        f"[yellow]Results may be truncated (limit={limit}). "
                        f"Use --limit N to see more results.[/yellow]"
                    )

        return 0

    except Exception as e:
        console.print(f"[red]Error searching: {e}[/red]")
        return 1

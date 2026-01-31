"""Aline doctor command - Repair common issues after updates."""

from __future__ import annotations

import contextlib
import io
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer
from rich.console import Console
from rich.table import Table

from ..config import ReAlignConfig, get_default_config_content

console = Console()


def _clear_python_cache(root: Path, *, verbose: bool) -> Tuple[int, int]:
    pyc_count = 0
    pycache_count = 0

    for pyc_file in root.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            pyc_count += 1
            if verbose:
                console.print(f"  [dim]Removed: {pyc_file}[/dim]")
        except Exception as e:
            if verbose:
                console.print(f"  [yellow]Failed to remove {pyc_file}: {e}[/yellow]")

    for pycache_dir in root.rglob("__pycache__"):
        if not pycache_dir.is_dir():
            continue
        try:
            shutil.rmtree(pycache_dir)
            pycache_count += 1
            if verbose:
                console.print(f"  [dim]Removed: {pycache_dir}[/dim]")
        except Exception as e:
            if verbose:
                console.print(f"  [yellow]Failed to remove {pycache_dir}: {e}[/yellow]")

    return pyc_count, pycache_count


def _ensure_global_config(*, force: bool, verbose: bool) -> Path:
    config_path = Path.home() / ".aline" / "config.yaml"

    if force or not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(get_default_config_content(), encoding="utf-8")
        if verbose:
            console.print(f"  [dim]Wrote config: {config_path}[/dim]")

    return config_path


def _ensure_database_initialized(config: ReAlignConfig, *, verbose: bool) -> Path:
    db_path = Path(config.sqlite_db_path).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    from ..db.sqlite_db import SQLiteDatabase

    db = SQLiteDatabase(str(db_path))
    ok = db.initialize()
    db.close()
    if verbose:
        console.print(f"  [dim]Database init: {'ok' if ok else 'failed'}[/dim]")

    return db_path


def _update_claude_hooks(*, verbose: bool) -> Tuple[list[str], list[str]]:
    hooks_updated: list[str] = []
    hooks_failed: list[str] = []

    # Stop hook
    try:
        from ..claude_hooks.stop_hook_installer import install_stop_hook, get_settings_path

        if install_stop_hook(get_settings_path(), quiet=True, force=True):
            hooks_updated.append("Stop")
            if verbose:
                console.print("  [dim]Stop hook updated[/dim]")
        else:
            hooks_failed.append("Stop")
    except Exception as e:
        hooks_failed.append("Stop")
        if verbose:
            console.print(f"  [yellow]Stop hook failed: {e}[/yellow]")

    # UserPromptSubmit hook
    try:
        from ..claude_hooks.user_prompt_submit_hook_installer import (
            install_user_prompt_submit_hook,
            get_settings_path as get_submit_settings_path,
        )

        if install_user_prompt_submit_hook(get_submit_settings_path(), quiet=True, force=True):
            hooks_updated.append("UserPromptSubmit")
            if verbose:
                console.print("  [dim]UserPromptSubmit hook updated[/dim]")
        else:
            hooks_failed.append("UserPromptSubmit")
    except Exception as e:
        hooks_failed.append("UserPromptSubmit")
        if verbose:
            console.print(f"  [yellow]UserPromptSubmit hook failed: {e}[/yellow]")

    # PermissionRequest hook
    try:
        from ..claude_hooks.permission_request_hook_installer import (
            install_permission_request_hook,
            get_settings_path as get_permission_settings_path,
        )

        if install_permission_request_hook(get_permission_settings_path(), quiet=True, force=True):
            hooks_updated.append("PermissionRequest")
            if verbose:
                console.print("  [dim]PermissionRequest hook updated[/dim]")
        else:
            hooks_failed.append("PermissionRequest")
    except Exception as e:
        hooks_failed.append("PermissionRequest")
        if verbose:
            console.print(f"  [yellow]PermissionRequest hook failed: {e}[/yellow]")

    return hooks_updated, hooks_failed


def _update_skills(*, verbose: bool) -> int:
    from .add import add_skills_command

    stdout_capture = io.StringIO()
    with contextlib.redirect_stdout(stdout_capture):
        add_skills_command(force=True)

    output = stdout_capture.getvalue()
    updated_count = output.count("✓")
    if verbose and output.strip():
        for line in output.strip().split("\n"):
            console.print(f"  [dim]{line}[/dim]")
    return updated_count


def _check_failed_jobs(
    config: ReAlignConfig,
    *,
    verbose: bool,
    fix: bool,
) -> Tuple[int, int]:
    """
    Check for failed turn_summary and session_summary jobs.

    Returns:
        (failed_count, requeued_count)
    """
    from ..db.sqlite_db import SQLiteDatabase

    db_path = Path(config.sqlite_db_path).expanduser()
    if not db_path.exists():
        return 0, 0

    db = SQLiteDatabase(str(db_path))

    try:
        # Count failed jobs in queue
        failed_turn_count = db.count_jobs(kinds=["turn_summary"], statuses=["failed"])
        failed_session_count = db.count_jobs(kinds=["session_summary"], statuses=["failed"])
        total_failed = failed_turn_count + failed_session_count

        if verbose and total_failed > 0:
            # Show details of failed jobs
            failed_jobs = db.list_jobs(statuses=["failed"], limit=20)
            if failed_jobs:
                table = Table(title="Failed Jobs in Queue", show_header=True, header_style="bold")
                table.add_column("Kind", style="cyan")
                table.add_column("Session", style="dim")
                table.add_column("Turn", style="dim")
                table.add_column("Error", style="red", max_width=40)
                table.add_column("Attempts", justify="right")

                for job in failed_jobs:
                    payload = job.get("payload", {})
                    session_id = str(payload.get("session_id", ""))[:8]
                    turn_num = str(payload.get("turn_number", "-"))
                    error = (job.get("last_error") or "")[:40]
                    attempts = str(job.get("attempts", 0))
                    table.add_row(job["kind"], session_id, turn_num, error, attempts)

                console.print(table)

        requeued = 0
        if fix and total_failed > 0:
            # Requeue failed jobs
            requeued, _ = db.requeue_failed_jobs(kinds=["turn_summary", "session_summary"])

        return total_failed, requeued

    finally:
        db.close()


def _check_llm_error_turns(
    config: ReAlignConfig,
    *,
    verbose: bool,
    fix: bool,
) -> Tuple[int, int]:
    """
    Check for turns with LLM API errors (llm_title contains 'LLM API Error').

    Returns:
        (error_count, requeued_count)
    """
    from ..db.sqlite_db import SQLiteDatabase

    db_path = Path(config.sqlite_db_path).expanduser()
    if not db_path.exists():
        return 0, 0

    db = SQLiteDatabase(str(db_path))

    try:
        conn = db._get_connection()

        # Find turns with LLM API Error marker (exact prefix match)
        rows = conn.execute(
            """
            SELECT t.session_id, t.turn_number, t.llm_title, s.session_file_path, s.workspace_path
            FROM turns t
            JOIN sessions s ON t.session_id = s.id
            WHERE t.llm_title LIKE '⚠ LLM API Error%'
            ORDER BY t.timestamp DESC
            """
        ).fetchall()

        if not rows:
            return 0, 0

        if verbose:
            table = Table(title="Turns with LLM API Error", show_header=True, header_style="bold")
            table.add_column("Session", style="dim")
            table.add_column("Turn", justify="right")
            table.add_column("Title", style="yellow", max_width=50)

            for row in rows[:20]:  # Show max 20
                session_id = str(row["session_id"])[:12]
                turn_num = str(row["turn_number"])
                title = (row["llm_title"] or "")[:50]
                table.add_row(session_id, turn_num, title)

            if len(rows) > 20:
                table.add_row("...", "...", f"({len(rows) - 20} more)")

            console.print(table)

        if not fix:
            return len(rows), 0

        # Requeue turn_summary jobs for these turns
        requeued = 0
        skipped = 0
        for row in rows:
            session_file_path_str = row["session_file_path"] or ""

            # Skip invalid session file paths
            if not session_file_path_str or session_file_path_str in (".", ".."):
                if verbose:
                    console.print(f"  [dim]Skip: invalid session path for {row['session_id'][:8]} #{row['turn_number']}[/dim]")
                skipped += 1
                continue

            session_file_path = Path(session_file_path_str)
            workspace_path = Path(row["workspace_path"]) if row["workspace_path"] else None

            if not session_file_path.exists():
                if verbose:
                    console.print(f"  [dim]Skip: session file not found: {session_file_path}[/dim]")
                skipped += 1
                continue

            try:
                db.enqueue_turn_summary_job(
                    session_file_path=session_file_path,
                    workspace_path=workspace_path,
                    turn_number=row["turn_number"],
                    skip_dedup=True,  # Force regeneration
                )
                requeued += 1
            except Exception as e:
                if verbose:
                    console.print(f"  [yellow]Failed to enqueue {row['session_id'][:8]} #{row['turn_number']}: {e}[/yellow]")
                skipped += 1

        return len(rows), requeued

    finally:
        db.close()


def run_doctor(
    *,
    restart_daemons: bool,
    start_if_not_running: bool,
    verbose: bool,
    clear_cache: bool,
    auto_fix: bool = False,
) -> int:
    """
    Core doctor logic.

    Args:
        restart_daemons: Restart/ensure daemons at the end.
        start_if_not_running: If True and restart_daemons is True, start daemons even if not running.
        verbose: Print details.
        clear_cache: Clear Python bytecode cache for the installed package directory.
        auto_fix: If True, automatically fix failed jobs without prompting.
    """
    from ..auth import is_logged_in
    from . import watcher as watcher_cmd
    from . import worker as worker_cmd
    from . import init as init_cmd

    console.print("\n[bold blue]═══ Aline Doctor ═══[/bold blue]\n")

    watcher_running, _watcher_pid, _watcher_mode = watcher_cmd.detect_watcher_process()
    worker_running, _worker_pid, _worker_mode = worker_cmd.detect_worker_process()

    can_start_daemons = is_logged_in()
    if restart_daemons and not can_start_daemons:
        console.print("[yellow]![/yellow] Not logged in; skipping daemon restart/start.")
        console.print("[dim]Run 'aline login' then re-run 'aline doctor'.[/dim]")
        restart_daemons = False

    # Stop daemons early to avoid DB lock during migrations.
    if restart_daemons:
        if watcher_running:
            if verbose:
                console.print("[dim]Stopping watcher...[/dim]")
            try:
                watcher_cmd.watcher_stop_command()
            except Exception:
                pass
        if worker_running:
            if verbose:
                console.print("[dim]Stopping worker...[/dim]")
            try:
                worker_cmd.worker_stop_command()
            except Exception:
                pass

    # 1. Clear Python cache (package scope)
    if clear_cache:
        console.print("[bold]1. Clearing Python cache...[/bold]")
        package_root = Path(__file__).resolve().parents[1]
        pyc_count, pycache_count = _clear_python_cache(package_root, verbose=verbose)
        console.print(
            f"  [green]✓[/green] Cleared {pyc_count} .pyc files, {pycache_count} __pycache__ directories"
        )

    # 2. Ensure global environment (config/db/prompts/tmux)
    console.print("\n[bold]2. Ensuring global environment...[/bold]")
    try:
        config_path = _ensure_global_config(force=False, verbose=verbose)
        config = ReAlignConfig.load(config_path)
        db_path = _ensure_database_initialized(config, verbose=verbose)

        # Prompts + tmux are safe to re-run (no overwrite for prompts; tmux auto-updates Aline-managed config).
        init_cmd._initialize_prompts_directory()
        tmux_conf = init_cmd._initialize_tmux_config()

        console.print(f"  [green]✓[/green] Config: {config_path}")
        console.print(f"  [green]✓[/green] Database: {db_path}")
        console.print(f"  [green]✓[/green] Prompts: {Path.home() / '.aline' / 'prompts'}")
        console.print(f"  [green]✓[/green] Tmux: {tmux_conf}")
    except Exception as e:
        console.print(f"  [red]✗[/red] Failed to ensure global environment: {e}")
        return 1

    # 3. Update Claude Code hooks
    console.print("\n[bold]3. Updating Claude Code hooks...[/bold]")
    hooks_updated, hooks_failed = _update_claude_hooks(verbose=verbose)
    if hooks_updated:
        console.print(f"  [green]✓[/green] Updated hooks: {', '.join(hooks_updated)}")
    if hooks_failed:
        console.print(f"  [yellow]![/yellow] Failed hooks: {', '.join(hooks_failed)}")

    # 4. Update skills
    console.print("\n[bold]4. Updating skills...[/bold]")
    try:
        updated_count = _update_skills(verbose=verbose)
        if updated_count > 0:
            console.print(f"  [green]✓[/green] Updated {updated_count} skill(s)")
        else:
            console.print("  [green]✓[/green] Skills are up to date")
    except Exception as e:
        console.print(f"  [yellow]![/yellow] Failed to update skills: {e}")

    # 5. Check/fix failed jobs and LLM error turns
    console.print("\n[bold]5. Checking failed summary jobs...[/bold]")
    try:
        # First pass: check counts without fixing
        failed_count, _ = _check_failed_jobs(config, verbose=verbose, fix=False)
        llm_error_count, _ = _check_llm_error_turns(config, verbose=verbose, fix=False)

        total_issues = failed_count + llm_error_count

        if total_issues == 0:
            console.print("  [green]✓[/green] No failed jobs or LLM errors found")
        else:
            # Show what was found
            if failed_count > 0:
                console.print(f"  [yellow]![/yellow] Found {failed_count} failed job(s) in queue")
            if llm_error_count > 0:
                console.print(f"  [yellow]![/yellow] Found {llm_error_count} turn(s) with LLM API errors")

            # Ask user if they want to fix
            if auto_fix or typer.confirm("\n  Do you want to requeue these for regeneration?", default=True):
                requeued_jobs = 0
                requeued_turns = 0

                if failed_count > 0:
                    _, requeued_jobs = _check_failed_jobs(config, verbose=verbose, fix=True)
                if llm_error_count > 0:
                    _, requeued_turns = _check_llm_error_turns(config, verbose=verbose, fix=True)

                total_requeued = requeued_jobs + requeued_turns
                console.print(f"  [green]✓[/green] Requeued {total_requeued} item(s) for regeneration")
            else:
                console.print("  [dim]Skipped fixing failed jobs[/dim]")
    except Exception as e:
        console.print(f"  [yellow]![/yellow] Failed to check jobs: {e}")

    # 6. Restart/ensure daemons
    if restart_daemons:
        console.print("\n[bold]6. Checking daemons...[/bold]")

        should_start_watcher = watcher_running or start_if_not_running
        should_start_worker = worker_running or start_if_not_running

        if should_start_watcher:
            try:
                exit_code = watcher_cmd.watcher_start_command()
                if exit_code == 0:
                    console.print("  [green]✓[/green] Watcher is running")
                else:
                    console.print("  [yellow]![/yellow] Failed to start watcher")
            except Exception as e:
                console.print(f"  [yellow]![/yellow] Failed to start watcher: {e}")
        else:
            console.print("  [dim]Watcher was not running; leaving it stopped.[/dim]")

        if should_start_worker:
            try:
                exit_code = worker_cmd.worker_start_command()
                if exit_code == 0:
                    console.print("  [green]✓[/green] Worker is running")
                else:
                    console.print("  [yellow]![/yellow] Failed to start worker")
            except Exception as e:
                console.print(f"  [yellow]![/yellow] Failed to start worker: {e}")
        else:
            console.print("  [dim]Worker was not running; leaving it stopped.[/dim]")
    else:
        console.print("\n[dim]Skipping daemon restart (--no-restart)[/dim]")

    console.print("\n[green]Done![/green] Aline is ready with the latest code.")
    return 0


def doctor_command(
    no_restart: bool = typer.Option(False, "--no-restart", help="Only repair files, don't restart daemons"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """
    Fix common issues after code updates.

    This command:
    - Clears Python bytecode cache for the installed Aline package
    - Ensures global config/DB/prompts/tmux are present and up to date
    - Updates Claude Code hooks (Stop, UserPromptSubmit, PermissionRequest)
    - Updates Claude Code skills to the latest version
    - Checks for failed summary jobs (prompts to fix if found)
    - Restarts watcher/worker (default) so long-running processes use the latest code
    """
    exit_code = run_doctor(
        restart_daemons=not no_restart,
        start_if_not_running=True,
        verbose=verbose,
        clear_cache=True,
    )
    raise typer.Exit(code=exit_code)


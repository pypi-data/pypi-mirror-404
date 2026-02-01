"""ReAlign upgrade command - Upgrade database schema to latest version."""

from pathlib import Path
import subprocess
import typer
from rich.console import Console
from rich.table import Table
from typing import Optional, Tuple

from ..config import ReAlignConfig
from ..db.schema import SCHEMA_VERSION, get_migration_scripts

console = Console()


def get_latest_pypi_version() -> Optional[str]:
    """Fetch the latest version of aline-ai from PyPI.

    Returns:
        The latest version string, or None if unable to fetch.
    """
    import urllib.request
    import json

    try:
        url = "https://pypi.org/pypi/aline-ai/json"
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode())
            return data.get("info", {}).get("version")
    except Exception:
        return None


def compare_versions(current: str, latest: str) -> int:
    """Compare two version strings.

    Returns:
        -1 if current < latest (update available)
         0 if current == latest
         1 if current > latest
    """
    def parse_version(v: str) -> Tuple[int, ...]:
        """Parse version string to tuple of integers."""
        parts = []
        for part in v.split("."):
            # Handle pre-release versions like "0.5.5a1"
            num_part = ""
            for char in part:
                if char.isdigit():
                    num_part += char
                else:
                    break
            if num_part:
                parts.append(int(num_part))
            else:
                parts.append(0)
        return tuple(parts)

    current_tuple = parse_version(current)
    latest_tuple = parse_version(latest)

    # Pad shorter tuple with zeros
    max_len = max(len(current_tuple), len(latest_tuple))
    current_tuple = current_tuple + (0,) * (max_len - len(current_tuple))
    latest_tuple = latest_tuple + (0,) * (max_len - len(latest_tuple))

    if current_tuple < latest_tuple:
        return -1
    elif current_tuple > latest_tuple:
        return 1
    return 0


def check_and_prompt_update() -> bool:
    """Check for updates and prompt user to update if available.

    Returns:
        True if update was performed (should restart), False otherwise.
    """
    from importlib.metadata import version

    try:
        current_version = version("aline-ai")
    except Exception:
        return False

    latest_version = get_latest_pypi_version()
    if latest_version is None:
        return False

    if compare_versions(current_version, latest_version) >= 0:
        # Current version is up to date or newer
        return False

    # New version available - prompt user
    console.print(
        f"\n[bold yellow]⬆ Update available:[/bold yellow] "
        f"[cyan]{current_version}[/cyan] → [green]{latest_version}[/green]"
    )

    try:
        response = console.input(
            "[dim]Do you want to update now? ([/dim][green]y[/green][dim]/[/dim][yellow]n[/yellow][dim]):[/dim] "
        ).strip().lower()
    except (EOFError, KeyboardInterrupt):
        console.print("\n[dim]Update skipped.[/dim]\n")
        return False

    if response not in ("y", "yes"):
        console.print("[dim]Update skipped.[/dim]\n")
        return False

    # Perform update using pipx
    console.print("\n[bold]Updating aline-ai via pipx...[/bold]\n")

    try:
        result = subprocess.run(
            ["pipx", "upgrade", "aline-ai"],
            capture_output=False,
        )

        if result.returncode == 0:
            console.print(
                f"\n[bold green]✓ Successfully updated to {latest_version}![/bold green]"
            )
            console.print("[dim]Please restart 'aline' to use the new version.[/dim]\n")
            return True
        else:
            console.print("\n[bold red]✗ Update failed.[/bold red]")
            console.print("[dim]You can manually update with: pipx upgrade aline-ai[/dim]\n")
            return False

    except FileNotFoundError:
        console.print("\n[bold red]✗ pipx not found.[/bold red]")
        console.print("[dim]Please install with: pip install aline-ai --upgrade[/dim]\n")
        return False
    except Exception as e:
        console.print(f"\n[bold red]✗ Update failed: {e}[/bold red]\n")
        return False


def get_current_db_version(db_path: Path) -> int:
    """Get current schema version from database without triggering migration."""
    import sqlite3

    if not db_path.exists():
        return -1  # Database doesn't exist

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] is not None else 0
    except sqlite3.OperationalError:
        return 0  # Table doesn't exist, fresh database


def upgrade_command(
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be done without making changes"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Force upgrade even if versions match"),
    restart_watcher: bool = typer.Option(
        True, "--restart-watcher/--no-restart-watcher", help="Restart watcher after upgrade"
    ),
):
    """Upgrade aline database schema to the latest version.

    This command is useful after updating aline via pip install to ensure
    the database schema is compatible with the new code version.

    Examples:
        aline upgrade                    # Upgrade database
        aline upgrade --dry-run          # Preview changes
        aline upgrade --no-restart-watcher  # Don't restart watcher
    """
    console.print("\n[bold blue]═══ Aline Upgrade ═══[/bold blue]\n")

    # Load config
    try:
        config = ReAlignConfig.load()
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        console.print("[dim]Run 'aline init' first to initialize aline.[/dim]")
        raise typer.Exit(1)

    db_path = Path(config.sqlite_db_path).expanduser()

    # Check current version
    current_version = get_current_db_version(db_path)
    target_version = SCHEMA_VERSION

    # Display version info
    table = Table(title="Schema Version", show_header=False, box=None)
    table.add_column("Label", style="bold")
    table.add_column("Value", style="cyan")

    if current_version == -1:
        table.add_row("Database", "[red]Not found[/red]")
        table.add_row("Path", str(db_path))
        console.print(table)
        console.print("\n[yellow]Database does not exist. Run 'aline init' first.[/yellow]")
        raise typer.Exit(1)

    table.add_row("Current version", f"V{current_version}")
    table.add_row("Target version", f"V{target_version}")
    table.add_row("Database path", str(db_path))
    console.print(table)

    # Check if upgrade is needed
    if current_version >= target_version and not force:
        console.print("\n[green]✓ Database is already up to date![/green]")
        raise typer.Exit(0)

    if current_version == target_version and force:
        console.print(
            "\n[yellow]Versions match, but --force specified. Re-running migrations...[/yellow]"
        )

    # Get migration scripts
    migrations = get_migration_scripts(current_version, target_version)

    if not migrations:
        console.print("\n[green]✓ No migrations needed.[/green]")
        raise typer.Exit(0)

    # Display migrations
    console.print(f"\n[bold]Migrations to apply ({len(migrations)} scripts):[/bold]")
    for i, script in enumerate(migrations, 1):
        # Show truncated script preview
        preview = script.strip().replace("\n", " ")[:60]
        if len(script.strip()) > 60:
            preview += "..."
        console.print(f"  {i}. [dim]{preview}[/dim]")

    if dry_run:
        console.print("\n[yellow]Dry run - no changes made.[/yellow]")
        raise typer.Exit(0)

    # Confirm upgrade
    console.print("")

    # Check if watcher/worker are running (to restart later)
    watcher_was_running = False
    worker_was_running = False
    if restart_watcher:
        try:
            from . import watcher as watcher_cmd

            watcher_was_running = watcher_cmd._is_watcher_running()
            if watcher_was_running:
                console.print("[dim]Stopping watcher for upgrade...[/dim]")
                watcher_cmd.watcher_stop_command()
        except Exception:
            pass
        try:
            from . import worker as worker_cmd

            is_running, _pid, _mode = worker_cmd.detect_worker_process()
            worker_was_running = bool(is_running)
            if worker_was_running:
                console.print("[dim]Stopping worker for upgrade...[/dim]")
                worker_cmd.worker_stop_command()
        except Exception:
            pass

    # Perform upgrade
    console.print("[bold]Upgrading database...[/bold]")

    try:
        from ..db.sqlite_db import SQLiteDatabase

        db = SQLiteDatabase(str(db_path))
        db.initialize()  # This handles migrations automatically
        db.close()

        # Verify upgrade
        new_version = get_current_db_version(db_path)

        if new_version >= target_version:
            console.print(
                f"\n[bold green]✓ Upgrade successful![/bold green] V{current_version} → V{new_version}"
            )
        else:
            console.print(
                f"\n[yellow]⚠ Partial upgrade: V{current_version} → V{new_version} (target: V{target_version})[/yellow]"
            )

    except Exception as e:
        console.print(f"\n[bold red]✗ Upgrade failed: {e}[/bold red]")
        raise typer.Exit(1)

    # Restart watcher/worker if they were running
    if watcher_was_running and restart_watcher:
        console.print("\n[dim]Restarting watcher...[/dim]")
        try:
            from . import watcher as watcher_cmd

            exit_code = watcher_cmd.watcher_start_command()
            if exit_code == 0:
                console.print("[green]✓ Watcher restarted[/green]")
            else:
                console.print(
                    "[yellow]⚠ Failed to restart watcher. Run 'aline watcher start' manually.[/yellow]"
                )
        except Exception as e:
            console.print(f"[yellow]⚠ Failed to restart watcher: {e}[/yellow]")

    if worker_was_running and restart_watcher:
        console.print("[dim]Restarting worker...[/dim]")
        try:
            from . import worker as worker_cmd

            exit_code = worker_cmd.worker_start_command()
            if exit_code == 0:
                console.print("[green]✓ Worker restarted[/green]")
            else:
                console.print(
                    "[yellow]⚠ Failed to restart worker. Run 'aline worker start' manually.[/yellow]"
                )
        except Exception as e:
            console.print(f"[yellow]⚠ Failed to restart worker: {e}[/yellow]")

    console.print("\n[bold]Done![/bold]\n")


def version_command():
    """Show aline version and database schema version."""
    console.print("\n[bold blue]═══ Aline Version Info ═══[/bold blue]\n")

    # Package version
    try:
        from importlib.metadata import version

        pkg_version = version("aline-ai")
    except Exception:
        pkg_version = "unknown"

    # Load config and check DB version
    try:
        config = ReAlignConfig.load()
        db_path = Path(config.sqlite_db_path).expanduser()
        current_version = get_current_db_version(db_path)
    except Exception:
        db_path = Path("~/.aline/db/aline.db").expanduser()
        current_version = -1

    table = Table(show_header=False, box=None)
    table.add_column("Label", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row("Package version", pkg_version)
    table.add_row("Schema version (code)", f"V{SCHEMA_VERSION}")

    if current_version == -1:
        table.add_row("Schema version (db)", "[red]Not found[/red]")
    else:
        if current_version < SCHEMA_VERSION:
            table.add_row(
                "Schema version (db)", f"[yellow]V{current_version}[/yellow] (upgrade available)"
            )
        else:
            table.add_row("Schema version (db)", f"[green]V{current_version}[/green]")

    table.add_row("Database path", str(db_path))

    console.print(table)

    if current_version >= 0 and current_version < SCHEMA_VERSION:
        console.print(
            f"\n[yellow]Tip: Run 'aline upgrade' to update database schema V{current_version} → V{SCHEMA_VERSION}[/yellow]"
        )

    console.print("")


if __name__ == "__main__":
    typer.run(upgrade_command)

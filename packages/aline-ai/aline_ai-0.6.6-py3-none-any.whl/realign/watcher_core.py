"""Session file watcher for auto-commit per user request completion.

Supports both Claude Code and Codex session formats with unified interface.
"""

import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional, Dict, Literal
from datetime import datetime

from .config import ReAlignConfig
from .hooks import find_all_active_sessions
from .logging_config import setup_logger

# Initialize logger for watcher
logger = setup_logger("realign.watcher_core", "watcher_core.log")


# Session type detection
SessionType = Literal["claude", "codex", "gemini", "unknown"]


def is_path_blacklisted(project_path: Path) -> bool:
    """
    Check if a project path is blacklisted for auto-init.

    Blacklisted paths:
    - Anything inside ~/.aline/ (where aline data is stored)
    - Anything inside ~/.realign/ (legacy location)
    - Any path containing .aline or .realign directory components
    - User home directory itself (~)
    - ~/Desktop, ~/Documents, ~/Downloads (top-level only, subdirs allowed)

    Args:
        project_path: Absolute path to check

    Returns:
        True if blacklisted, False if allowed
    """
    try:
        # Normalize path (resolve symlinks, make absolute)
        normalized = project_path.resolve()
        home = Path.home().resolve()
        aline_global_dir = (home / ".aline").resolve()
        realign_global_dir = (home / ".realign").resolve()

        # Check if inside ~/.aline/ directory (where all project data is stored)
        try:
            normalized.relative_to(aline_global_dir)
            logger.debug(f"Blacklisted (inside ~/.aline): {normalized}")
            return True
        except ValueError:
            pass  # Not inside ~/.aline

        # Check if inside ~/.realign/ directory (legacy)
        try:
            normalized.relative_to(realign_global_dir)
            logger.debug(f"Blacklisted (inside ~/.realign): {normalized}")
            return True
        except ValueError:
            pass  # Not inside ~/.realign

        # Check if path contains .aline or .realign components anywhere
        # This prevents initializing within project's local .aline/.realign directories
        path_parts = normalized.parts
        for part in path_parts:
            if part in [".aline", ".realign"]:
                logger.debug(f"Blacklisted (contains {part} component): {normalized}")
                return True

        # Check if it IS the home directory itself
        if normalized == home:
            logger.debug(f"Blacklisted (home directory): {normalized}")
            return True

        # Check forbidden top-level home subdirectories
        # But allow their subdirectories (e.g., ~/Desktop/project is OK)
        forbidden_dirs = ["Desktop", "Documents", "Downloads"]
        for forbidden in forbidden_dirs:
            forbidden_path = (home / forbidden).resolve()
            if normalized == forbidden_path:
                logger.debug(f"Blacklisted (forbidden dir): {normalized}")
                return True

        return False

    except Exception as e:
        logger.error(f"Error checking blacklist for {project_path}: {e}")
        # If we can't determine, err on the side of caution
        return True


def decode_claude_project_path(project_dir_name: str) -> Optional[Path]:
    """
    Decode Claude Code project directory name to actual project path.

    Claude naming: -Users-huminhao-Projects-ReAlign
    Decoded: /Users/huminhao/Projects/ReAlign

    If naive decoding fails (e.g., paths with underscores/hyphens in directory names),
    falls back to reading the 'cwd' field from JSONL session files.

    Args:
        project_dir_name: Claude project directory name (or full path to Claude project dir)

    Returns:
        Decoded Path if valid, None otherwise
    """
    # Handle both directory name and full path
    if isinstance(project_dir_name, Path):
        project_dir = project_dir_name
        dir_name = project_dir.name
    elif "/" in project_dir_name:
        project_dir = Path(project_dir_name)
        dir_name = project_dir.name
    else:
        dir_name = project_dir_name
        project_dir = Path.home() / ".claude" / "projects" / dir_name

    if not dir_name.startswith("-"):
        return None

    # Try naive decoding first
    path_str = "/" + dir_name[1:].replace("-", "/")
    project_path = Path(path_str)

    if project_path.exists():
        return project_path

    # Naive decoding failed - try reading from JSONL files
    logger.debug(f"Naive decoding failed for {dir_name}, trying JSONL fallback")

    if not project_dir.exists() or not project_dir.is_dir():
        logger.debug(f"Claude project directory not found: {project_dir}")
        return None

    # Find any JSONL file (excluding agent files)
    try:
        jsonl_files = [
            f
            for f in project_dir.iterdir()
            if f.suffix == ".jsonl" and not f.name.startswith("agent-")
        ]

        if not jsonl_files:
            logger.debug(f"No JSONL session files found in {project_dir}")
            return None

        # Read lines from first JSONL file to find cwd field
        jsonl_file = jsonl_files[0]
        with jsonl_file.open("r", encoding="utf-8") as f:
            # Check up to first 20 lines for cwd field
            for i, line in enumerate(f):
                if i >= 20:
                    break

                line = line.strip()
                if not line:
                    continue

                session_data = json.loads(line)
                cwd = session_data.get("cwd")

                if cwd:
                    project_path = Path(cwd)
                    if project_path.exists():
                        logger.debug(f"Decoded path from JSONL: {dir_name} -> {project_path}")
                        return project_path
                    else:
                        logger.debug(f"Path from JSONL doesn't exist: {project_path}")
                        return None

            logger.debug(f"No 'cwd' field found in first 20 lines of {jsonl_file.name}")
            return None

    except Exception as e:
        logger.debug(f"Error reading JSONL files from {project_dir}: {e}")
        return None

    return None


def is_aline_initialized() -> bool:
    """
    Check if Aline has been initialized globally (config + database present).
    """
    try:
        from .config import ReAlignConfig

        config = ReAlignConfig.load()
        db_path = Path(config.sqlite_db_path).expanduser()
        config_path = Path.home() / ".aline" / "config.yaml"
        return config_path.exists() and db_path.exists()
    except Exception as e:
        logger.debug(f"Error checking global init status: {e}")
        return False


class DialogueWatcher:
    """Watch session files and auto-commit immediately after each user request completes."""

    def __init__(self):
        """Initialize watcher for multi-project monitoring - extracts project paths dynamically from sessions."""
        self.config = ReAlignConfig.load()
        self.last_commit_times: Dict[str, float] = {}  # Track last commit time per project
        self.last_session_sizes: Dict[str, int] = {}  # Track file sizes
        self.last_stop_reason_counts: Dict[str, int] = {}  # Track stop_reason counts per session
        self.last_session_mtimes: Dict[str, float] = (
            {}
        )  # Track last mtime of session files for idle detection
        self.last_final_commit_times: Dict[str, float] = (
            {}
        )  # Track when we last tried final commit per session
        self.min_commit_interval = 5.0  # Minimum 5 seconds between commits (cooldown)
        self.debounce_delay = 10.0  # Wait 10 seconds after file change to ensure turn is complete (increased from 2.0 to handle streaming responses)
        self.final_commit_idle_timeout = 300.0  # 5 minutes idle to trigger final commit
        self.running = False
        self.pending_commit_task: Optional[asyncio.Task] = None
        self._pending_changed_files: set[str] = (
            set()
        )  # Accumulate changed files instead of cancelling

        # Trigger support for pluggable turn detection
        from .triggers.registry import get_global_registry

        self.trigger_registry = get_global_registry()
        self.trigger_name = "next_turn"  # Default trigger (可配置)
        self._session_triggers: Dict[str, "TurnTrigger"] = {}  # Cache triggers per session

        # Owner id for DB-backed lease locks (cross-process).
        try:
            from .db.locks import make_lock_owner

            self.lock_owner = make_lock_owner("watcher")
        except Exception:
            self.lock_owner = f"watcher:{os.getpid()}"

        # Per-turn "processing" TTL: if a processing placeholder turn exists longer than this,
        # a new run may take over and re-process it to avoid permanent stuck states.
        self.processing_turn_ttl_seconds = 20 * 60  # 20 minutes

        # Signal directory for Stop hook integration
        self.signal_dir = Path.home() / ".aline" / ".signals"
        self.signal_dir.mkdir(parents=True, exist_ok=True)
        self.user_prompt_signal_dir = self.signal_dir / "user_prompt_submit"
        self.user_prompt_signal_dir.mkdir(parents=True, exist_ok=True)

    def _maybe_link_codex_terminal(self, session_file: Path) -> None:
        """Best-effort: bind a Codex session file to the most likely active Codex terminal."""
        try:
            if self._detect_session_type(session_file) != "codex":
                return
        except Exception:
            return

        try:
            from .codex_home import codex_home_owner_from_session_file
            from .codex_terminal_linker import read_codex_session_meta, select_agent_for_codex_session
            from .db import get_database

            meta = read_codex_session_meta(session_file)
            if meta is None:
                return

            db = get_database(read_only=False)
            agents = db.list_agents(status="active", limit=1000)
            # Deterministic mapping: session file stored under ~/.aline/codex_homes/<terminal_id>/...
            owner = codex_home_owner_from_session_file(session_file)
            agent_id = None
            agent_info_id = None
            if owner:
                if owner[0] == "terminal":
                    agent_id = owner[1]
                elif owner[0] == "agent":
                    agent_info_id = owner[1]
                    scoped_agents = [
                        a
                        for a in agents
                        if getattr(a, "provider", "") == "codex"
                        and getattr(a, "status", "") == "active"
                        and (getattr(a, "source", "") or "") == f"agent:{agent_info_id}"
                    ]
                    agent_id = select_agent_for_codex_session(
                        scoped_agents, session=meta, max_time_delta_seconds=None
                    )
            if not agent_id:
                # Fallback heuristic mapping (legacy default ~/.codex/sessions).
                agent_id = select_agent_for_codex_session(agents, session=meta)
            if not agent_id:
                return

            owner_agent_info_id = agent_info_id
            # Get existing agent to preserve agent_info_id in source field
            existing_agent = db.get_agent_by_id(agent_id)
            agent_info_id = None
            existing_source = None
            if existing_agent:
                existing_source = existing_agent.source or ""
                if existing_source.startswith("agent:"):
                    agent_info_id = existing_source[6:]

            if not agent_info_id and owner_agent_info_id:
                agent_info_id = owner_agent_info_id

            if existing_source:
                source = existing_source
            elif agent_info_id:
                source = f"agent:{agent_info_id}"
            else:
                source = "codex:auto-link"

            db.update_agent(
                agent_id,
                provider="codex",
                session_type="codex",
                session_id=session_file.stem,
                transcript_path=str(session_file),
                cwd=meta.cwd,
                project_dir=meta.cwd,
                source=source,
            )

            # Link session to agent_info if available (bidirectional linking)
            if agent_info_id:
                try:
                    db.update_session_agent_id(session_file.stem, agent_info_id)
                except Exception:
                    pass
        except Exception:
            return

    async def start(self):
        """Start watching session files."""
        if not self.config.mcp_auto_commit:
            logger.info("Auto-commit disabled in config")
            print("[Watcher] Auto-commit disabled in config", file=sys.stderr)
            return

        self.running = True
        logger.info("Started watching for dialogue completion")
        logger.info(f"Mode: Multi-project monitoring (all Claude Code projects)")
        logger.info(f"Trigger: Per-request (at end of each AI response)")
        logger.info(f"Supports: Claude Code & Codex (auto-detected)")
        logger.info(f"Debounce: {self.debounce_delay}s, Cooldown: {self.min_commit_interval}s")
        print("[Watcher] Started watching for dialogue completion", file=sys.stderr)
        print(
            f"[Watcher] Mode: Multi-project monitoring (all Claude Code projects)", file=sys.stderr
        )
        print(f"[Watcher] Trigger: Per-request (at end of each AI response)", file=sys.stderr)
        print(f"[Watcher] Supports: Claude Code & Codex (auto-detected)", file=sys.stderr)
        print(
            f"[Watcher] Debounce: {self.debounce_delay}s, Cooldown: {self.min_commit_interval}s",
            file=sys.stderr,
        )

        # Auto-install Claude Code Stop hook for reliable turn completion detection
        try:
            from .claude_hooks.stop_hook_installer import ensure_stop_hook_installed

            if ensure_stop_hook_installed(quiet=True):
                logger.info("Claude Code Stop hook is ready")
            else:
                logger.warning("Failed to install Stop hook, falling back to polling-only mode")
        except Exception as e:
            logger.debug(f"Stop hook installation skipped: {e}")

        if self.config.enable_temp_turn_titles:
            # Auto-install Claude Code UserPromptSubmit hook for temp title generation
            try:
                from .claude_hooks.user_prompt_submit_hook_installer import (
                    ensure_user_prompt_submit_hook_installed,
                )

                if ensure_user_prompt_submit_hook_installed(quiet=True):
                    logger.info("Claude Code UserPromptSubmit hook is ready")
                else:
                    logger.warning("Failed to install UserPromptSubmit hook")
            except Exception as e:
                logger.debug(f"UserPromptSubmit hook installation skipped: {e}")

        # Initialize baseline sizes and stop_reason counts
        self.last_session_sizes, self.last_session_mtimes = self._get_session_stats()
        self.last_stop_reason_counts = self._get_stop_reason_counts()

        # Note: Idle timeout checking is now integrated into main loop instead of separate task

        # Ensure global config/database exists (no per-project init)
        logger.info("Ensuring global Aline initialization")
        print("[Watcher] Ensuring global Aline initialization", file=sys.stderr)
        await self.auto_init_projects()

        # Catch up any missed turns using persistent state
        await self._catch_up_uncommitted_turns()

        # Poll for file changes more frequently
        while self.running:
            try:
                # Priority 1: Check Stop hook signals (immediate trigger, no debounce)
                await self._check_stop_signals()

                # Priority 2: Check UserPromptSubmit signals (temp title generation)
                if self.config.enable_temp_turn_titles:
                    await self._check_user_prompt_submit_signals()

                # Priority 2: Fallback polling mechanism (with debounce)
                await self.check_for_changes()

                # Check for idle sessions that need final commit
                await self._check_idle_sessions_for_final_commit()

                await asyncio.sleep(0.5)  # Check every 0.5 seconds for responsiveness
            except Exception as e:
                logger.error(f"Error in check loop: {e}", exc_info=True)
                print(f"[Watcher] Error: {e}", file=sys.stderr)
                await asyncio.sleep(1.0)

    async def stop(self):
        """Stop watching."""
        self.running = False
        if self.pending_commit_task:
            self.pending_commit_task.cancel()
        logger.info("Watcher stopped")
        print("[Watcher] Stopped", file=sys.stderr)

    async def _check_stop_signals(self):
        """
        Check for Stop hook signal files.

        When Claude Code's Stop hook fires, it writes a signal file to ~/.aline/.signals/.
        This method processes those signals for immediate turn completion detection,
        bypassing the 10-second debounce delay.

        The Stop hook is the authoritative signal that a turn has completed. We pass
        target_turn to _do_commit to ensure the turn count baseline is correctly updated,
        since count_complete_turns() intentionally excludes the last turn (to prevent
        false positives from the polling mechanism).
        """
        try:
            if not self.signal_dir.exists():
                return

            for signal_file in self.signal_dir.glob("*.signal"):
                try:
                    # Read signal data
                    signal_data = json.loads(signal_file.read_text())
                    session_id = signal_data.get("session_id", "")
                    project_dir = signal_data.get("project_dir", "")
                    transcript_path = signal_data.get("transcript_path", "")
                    no_track = bool(signal_data.get("no_track", False))
                    agent_id = signal_data.get("agent_id", "")

                    logger.info(f"Stop signal received for session {session_id}")
                    print(f"[Watcher] Stop signal received for {session_id}", file=sys.stderr)

                    # Find the session file
                    session_file = None
                    if transcript_path and Path(transcript_path).exists():
                        session_file = Path(transcript_path)
                    elif session_id:
                        session_file = self._find_session_by_id(session_id)

                    if session_file and session_file.exists():
                        # Determine project path
                        if project_dir and Path(project_dir).exists():
                            project_path = Path(project_dir)
                        else:
                            project_path = self._extract_project_path(session_file)

                        if project_path:
                            # Calculate the actual turn number that just completed.
                            # For Claude, count_complete_turns intentionally excludes the last turn,
                            # so we use total_turns when available.
                            target_turn = self._get_total_turn_count(session_file)

                            # Enqueue durable job for worker (no LLM work in watcher process).
                            from .db import get_database

                            db = get_database()
                            try:
                                db.enqueue_turn_summary_job(  # type: ignore[attr-defined]
                                    session_file_path=session_file,
                                    workspace_path=project_path,
                                    turn_number=target_turn,
                                    session_type=self._detect_session_type(session_file),
                                    no_track=no_track,
                                    agent_id=agent_id if agent_id else None,
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to enqueue stop-hook job for {session_id}: {e}"
                                )
                                continue

                            logger.info(
                                f"Enqueued turn_summary via Stop hook: {session_id} turn {target_turn} ({project_path.name})"
                            )
                            print(
                                f"[Watcher] Enqueued turn_summary via Stop hook (turn {target_turn})",
                                file=sys.stderr,
                            )
                        else:
                            logger.warning(
                                f"Could not determine project path for session {session_id}"
                            )
                    else:
                        logger.warning(f"Session file not found for {session_id}")

                    # Delete the signal only after enqueue succeeds.
                    signal_file.unlink(missing_ok=True)

                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid signal file {signal_file.name}: {e}")
                    signal_file.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Error processing signal {signal_file.name}: {e}")
                    # Delete corrupted signal files to prevent infinite loops
                    signal_file.unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error checking stop signals: {e}", exc_info=True)

    async def _check_user_prompt_submit_signals(self):
        """Process UserPromptSubmit hook signals for temporary turn titles."""
        try:
            if not self.user_prompt_signal_dir.exists():
                return

            now = time.time()
            for signal_file in self.user_prompt_signal_dir.glob("*.signal"):
                try:
                    signal_data = json.loads(signal_file.read_text())
                except json.JSONDecodeError:
                    signal_file.unlink(missing_ok=True)
                    continue
                except Exception:
                    signal_file.unlink(missing_ok=True)
                    continue

                signal_ts = float(signal_data.get("timestamp") or 0.0)
                if signal_ts and now - signal_ts < 5.0:
                    continue

                session_id = str(signal_data.get("session_id") or "")
                prompt = str(signal_data.get("prompt") or "")
                transcript_path = str(signal_data.get("transcript_path") or "")
                project_dir = str(signal_data.get("project_dir") or "")
                no_track = bool(signal_data.get("no_track", False))
                agent_id = str(signal_data.get("agent_id") or "")

                session_file = None
                if transcript_path and Path(transcript_path).exists():
                    session_file = Path(transcript_path)
                elif session_id:
                    session_file = self._find_session_by_id(session_id)

                if not session_file or not session_file.exists():
                    signal_file.unlink(missing_ok=True)
                    continue
                if not session_id:
                    session_id = session_file.stem

                # Only apply to Claude sessions for now.
                session_type = self._detect_session_type(session_file)
                if session_type != "claude":
                    signal_file.unlink(missing_ok=True)
                    continue

                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._create_temp_turn_title,
                    session_file,
                    session_id,
                    prompt,
                    project_dir,
                    no_track,
                )

                # Link session to agent if agent_id is provided
                if agent_id and session_id:
                    try:
                        from .db import get_database

                        db = get_database()
                        db.update_session_agent_id(session_id, agent_id)
                    except Exception:
                        pass

                signal_file.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error checking user prompt signals: {e}", exc_info=True)

    def _get_total_turn_count(self, session_file: Path) -> int:
        """
        Get the total number of turns in a session file (including the last turn).

        Unlike _count_complete_turns() which excludes the last turn for safety,
        this method counts ALL turns. Used by Stop Hook processing where we have
        authoritative confirmation that the last turn is complete.

        Returns:
            Total number of turns in the session
        """
        try:
            trigger = self._get_trigger_for_session(session_file)
            if not trigger:
                return 0

            # For Claude trigger, use get_detailed_analysis to get total turns
            if hasattr(trigger, "get_detailed_analysis"):
                analysis = trigger.get_detailed_analysis(session_file)
                return analysis.get("total_turns", 0)

            # Fallback: use count_complete_turns + 1 (assuming last turn just completed)
            return trigger.count_complete_turns(session_file) + 1

        except Exception as e:
            logger.debug(f"Error getting total turn count for {session_file.name}: {e}")
            return 0

    def _get_new_completed_turn_numbers(self, session_file: Path) -> list[int]:
        """
        Determine which completed turn numbers are newly observed and should be enqueued.

        Note: for Claude Code, this only covers non-last turns, because
        ClaudeTrigger.count_complete_turns() intentionally excludes the last turn
        to avoid false positives. The last turn is handled by Stop hook or idle fallback.
        """
        session_path = str(session_file)
        session_type = self._detect_session_type(session_file)

        current_count = self._count_complete_turns(session_file)
        last_count = self.last_stop_reason_counts.get(session_path, 0)

        if current_count <= last_count:
            return []

        return list(range(int(last_count) + 1, int(current_count) + 1))

    def _find_session_by_id(self, session_id: str) -> Optional[Path]:
        """
        Find a session file by its ID.

        Args:
            session_id: The session ID (typically UUID or filename stem)

        Returns:
            Path to the session file, or None if not found
        """
        try:
            # Search in Claude Code sessions directory
            claude_base = Path.home() / ".claude" / "projects"
            if claude_base.exists():
                for project_dir in claude_base.iterdir():
                    if project_dir.is_dir():
                        session_file = project_dir / f"{session_id}.jsonl"
                        if session_file.exists():
                            return session_file

            # Also check currently tracked sessions
            for session_path in self.last_session_sizes.keys():
                path = Path(session_path)
                if path.stem == session_id and path.exists():
                    return path

            return None

        except Exception as e:
            logger.debug(f"Error finding session by ID {session_id}: {e}")
            return None

    def _get_session_stats(self) -> tuple[Dict[str, int], Dict[str, float]]:
        """Get (sizes, mtimes) for all active session files.

        For directory-based sessions (e.g., Antigravity), computes:
        - size: sum of all artifact file sizes
        - mtime: max mtime of all artifact files

        This ensures changes to individual artifacts are detected.
        """
        sizes: Dict[str, int] = {}
        mtimes: Dict[str, float] = {}
        try:
            session_files = find_all_active_sessions(self.config, project_path=None)
            for session_file in session_files:
                if not session_file.exists():
                    continue
                path_key = str(session_file)

                # Handle directory-based sessions (e.g., Antigravity brain directories)
                if session_file.is_dir():
                    # Check for Antigravity-style artifacts
                    artifacts = ["task.md", "walkthrough.md", "implementation_plan.md"]
                    total_size = 0
                    max_mtime = 0.0

                    for artifact_name in artifacts:
                        artifact_path = session_file / artifact_name
                        if artifact_path.exists():
                            artifact_stat = artifact_path.stat()
                            total_size += artifact_stat.st_size
                            max_mtime = max(max_mtime, artifact_stat.st_mtime)

                    # Only track if at least one artifact exists
                    if max_mtime > 0:
                        sizes[path_key] = total_size
                        mtimes[path_key] = max_mtime
                else:
                    # Regular file-based session
                    stat = session_file.stat()
                    sizes[path_key] = stat.st_size
                    mtimes[path_key] = stat.st_mtime

            logger.debug(f"Tracked {len(sizes)} session file(s) across all projects")
        except PermissionError as e:
            # macOS permission issue - only log once
            if not hasattr(self, "_permission_error_logged"):
                self._permission_error_logged = True
                logger.error("PERMISSION DENIED: Cannot access Claude Code sessions directory")
                print(
                    "[Watcher] ✗ PERMISSION DENIED: Cannot access ~/.claude/projects/",
                    file=sys.stderr,
                )
                print(
                    "[Watcher] ⓘ Grant Full Disk Access to Acme in System Preferences",
                    file=sys.stderr,
                )
                print(
                    "[Watcher] ⓘ System Preferences → Privacy & Security → Full Disk Access → Add Acme",
                    file=sys.stderr,
                )
        except Exception as e:
            logger.error(f"Error getting session stats: {e}", exc_info=True)
            print(f"[Watcher] Error getting session stats: {e}", file=sys.stderr)
        return sizes, mtimes

    def _get_session_sizes(self) -> Dict[str, int]:
        """Get current sizes of all active session files across all projects."""
        sizes, _ = self._get_session_stats()
        return sizes

    def _get_stop_reason_counts(self) -> Dict[str, int]:
        """Get current count of turn completion markers in all active session files across all projects."""
        counts = {}
        try:
            session_files = find_all_active_sessions(self.config, project_path=None)
            for session_file in session_files:
                if session_file.exists():
                    counts[str(session_file)] = self._count_complete_turns(session_file)
        except Exception as e:
            print(f"[Watcher] Error getting turn counts: {e}", file=sys.stderr)
        return counts

    def _detect_project_path(self) -> Optional[Path]:
        """
        Try to detect the current git repository root.

        Returns None if not inside a git repo (for multi-project mode).
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            repo_path = Path(result.stdout.strip())
            if repo_path.exists():
                return repo_path
        except subprocess.CalledProcessError:
            current_dir = Path.cwd()
            if (current_dir / ".git").exists():
                return current_dir
        except Exception as e:
            logger.debug(f"Could not detect project path: {e}")
        return None

    async def _catch_up_uncommitted_turns(self):
        """
        On startup, attempt to commit any turns that were missed while watcher was offline.

        Uses SQLite (turns table) to know last committed turn.
        Limits catch-up to max_catchup_sessions (default: 3) most recent sessions.
        """
        try:
            session_files = find_all_active_sessions(self.config, project_path=None)
            from .db import get_database

            db = get_database()

            # Sort by mtime descending (newest first)
            session_files.sort(key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)

            # Limit to max_catchup_sessions
            max_sessions = getattr(self.config, "max_catchup_sessions", 3)
            if len(session_files) > max_sessions:
                sessions_to_process = session_files[:max_sessions]
                skipped_count = len(session_files) - max_sessions
                logger.info(
                    f"Limiting catch-up to {max_sessions} most recent sessions, skipping {skipped_count} older sessions"
                )
                print(
                    f"[Watcher] Limiting catch-up to {max_sessions} most recent sessions ({skipped_count} skipped)",
                    file=sys.stderr,
                )
                print(
                    f"[Watcher] Use 'aline watcher session list' to see all sessions",
                    file=sys.stderr,
                )
            else:
                sessions_to_process = session_files

            for session_file in sessions_to_process:
                if not session_file.exists():
                    continue

                project_path = self._extract_project_path(session_file)
                if not project_path:
                    logger.debug(f"Skip catch-up (no project) for {session_file.name}")
                    continue

                session_id = session_file.stem
                session_type = self._detect_session_type(session_file)
                # For catch-up, include last turn for Claude (Stop hook may have been missed).
                if session_type == "claude":
                    current_count = self._get_total_turn_count(session_file)
                else:
                    current_count = self._count_complete_turns(session_file)

                # Get the set of turn numbers that have been committed
                # This detects gaps in turn numbers, not just trailing uncommitted turns
                committed_turns = db.get_committed_turn_numbers(session_id)
                expected_turns = set(range(1, current_count + 1))
                missing_turns = sorted(expected_turns - committed_turns)

                if not missing_turns:
                    # All turns are committed, align in-memory baseline
                    self.last_stop_reason_counts[str(session_file)] = current_count
                    continue

                logger.info(
                    f"Catch-up: {session_file.name} missing {len(missing_turns)} turn(s): {missing_turns}"
                )
                print(
                    f"[Watcher] Catch-up {session_file.name}: {len(missing_turns)} missing turn(s)",
                    file=sys.stderr,
                )

                enqueued = 0
                for turn in missing_turns:
                    try:
                        db.enqueue_turn_summary_job(  # type: ignore[attr-defined]
                            session_file_path=session_file,
                            workspace_path=project_path,
                            turn_number=turn,
                            session_type=session_type,
                        )
                        enqueued += 1
                    except Exception as e:
                        logger.warning(
                            f"Error enqueuing catch-up for {session_file.name} turn {turn}: {e}"
                        )

                if enqueued:
                    # Align baseline for future polling (Claude baseline excludes last turn).
                    self.last_stop_reason_counts[str(session_file)] = self._count_complete_turns(
                        session_file
                    )

        except Exception as e:
            logger.error(f"Catch-up error: {e}", exc_info=True)

    def _get_file_hash(self, session_file: Path) -> Optional[str]:
        """Compute MD5 hash of session file for duplicate detection."""
        try:
            with open(session_file, "rb") as f:
                md5_hash = hashlib.md5()
                while chunk := f.read(8192):
                    md5_hash.update(chunk)
                return md5_hash.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute hash for {session_file.name}: {e}")
            return None

    async def _check_idle_sessions_for_final_commit(self):
        """Check for idle sessions and trigger final commits if needed."""
        try:
            current_time = time.time()
            # Always use multi-project mode (project_path=None)
            session_files = find_all_active_sessions(self.config, project_path=None)

            for session_file in session_files:
                if not session_file.exists():
                    continue

                session_path = str(session_file)

                try:
                    # Get current mtime
                    mtime = session_file.stat().st_mtime

                    # Initialize tracking if first time seeing this session
                    if session_path not in self.last_session_mtimes:
                        self.last_session_mtimes[session_path] = mtime
                        continue

                    last_mtime = self.last_session_mtimes[session_path]

                    # If file was modified, update mtime and skip
                    if mtime > last_mtime:
                        self.last_session_mtimes[session_path] = mtime
                        # Reset final commit attempt time when file changes
                        self.last_final_commit_times.pop(session_path, None)
                        continue

                    # Check if session has been idle long enough
                    time_since_change = current_time - last_mtime
                    if time_since_change >= self.final_commit_idle_timeout:
                        # Check if we've already tried final commit recently
                        last_attempt = self.last_final_commit_times.get(session_path, 0)
                        if current_time - last_attempt < 60:  # Don't try more than once per minute
                            continue

                        from .db import get_database

                        db = get_database()

                        session_id = session_file.stem
                        session_type = self._detect_session_type(session_file)
                        completed_count = self._count_complete_turns(session_file)
                        last_count = self.last_stop_reason_counts.get(session_path, 0)

                        # For Claude, also consider the last turn (not counted in completed_count).
                        last_turn_to_enqueue: Optional[int] = None
                        if session_type == "claude":
                            total_turns = self._get_total_turn_count(session_file)
                            if total_turns > completed_count:
                                existing = db.get_turn_by_number(session_id, int(total_turns))
                                if existing is None:
                                    last_turn_to_enqueue = int(total_turns)
                                else:
                                    existing_status = getattr(existing, "turn_status", None)
                                    if existing_status == "processing":
                                        try:
                                            age_seconds = max(
                                                0.0,
                                                (
                                                    datetime.now()
                                                    - getattr(
                                                        existing, "created_at", datetime.now()
                                                    )
                                                ).total_seconds(),
                                            )
                                        except Exception:
                                            age_seconds = 0.0
                                        if age_seconds >= float(self.processing_turn_ttl_seconds):
                                            last_turn_to_enqueue = int(total_turns)

                        new_turns = []
                        if completed_count > last_count:
                            new_turns.extend(range(int(last_count) + 1, int(completed_count) + 1))
                        if last_turn_to_enqueue and last_turn_to_enqueue > 0:
                            new_turns.append(last_turn_to_enqueue)

                        if not new_turns:
                            logger.debug(
                                f"No new turns in {session_file.name} (count: {completed_count}), skipping idle enqueue"
                            )
                            self.last_final_commit_times[session_path] = current_time
                            continue

                        logger.info(
                            f"Session {session_file.name} idle for {time_since_change:.0f}s, enqueueing turns: {sorted(set(new_turns))}"
                        )
                        print(
                            f"[Watcher] Session idle for {time_since_change:.0f}s - enqueueing final turns",
                            file=sys.stderr,
                        )

                        project_path = self._extract_project_path(session_file)
                        if not project_path:
                            logger.debug(
                                f"Skipping enqueue for {session_file.name}: could not extract project path"
                            )
                            # Mark as attempted to avoid spamming logs
                            self.last_final_commit_times[session_path] = current_time
                            continue

                        enqueued_any = False
                        for turn_number in sorted(set(new_turns)):
                            try:
                                db.enqueue_turn_summary_job(  # type: ignore[attr-defined]
                                    session_file_path=session_file,
                                    workspace_path=project_path,
                                    turn_number=int(turn_number),
                                    session_type=session_type,
                                )
                                enqueued_any = True
                            except Exception as e:
                                logger.warning(
                                    f"Failed to enqueue final turn_summary for {session_file.name} #{turn_number}: {e}"
                                )

                        if enqueued_any:
                            # Baseline follows completed_count (Claude excludes last turn by design).
                            self.last_stop_reason_counts[session_path] = max(
                                self.last_stop_reason_counts.get(session_path, 0),
                                int(completed_count),
                            )

                        self.last_final_commit_times[session_path] = current_time

                except Exception as e:
                    logger.warning(f"Error checking idle status for {session_path}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in idle session check: {e}", exc_info=True)

    def _extract_project_path(self, session_file: Path) -> Optional[Path]:
        """
        Extract project path (cwd) from session file.
        Delegates to the appropriate adapter.
        """
        try:
            # Use AdapterRegistry to find the right adapter
            from .adapters import get_adapter_registry

            registry = get_adapter_registry()

            adapter = registry.auto_detect_adapter(session_file)
            if adapter:
                project_path = adapter.extract_project_path(session_file)
                if project_path:
                    return project_path

            # Fallback for legacy logic if adapter returns None or no adapter found
            # (Keep existing logic as backup if needed, or rely on adapters)

            # Method 3: For Gemini CLI / Antigravity - return a pseudo path if adapter failed
            if ".gemini/" in str(session_file):
                logger.debug(
                    f"Gemini/Antigravity session detected, using home as pseudo project fallback: {session_file.name}"
                )
                return Path.home()

            logger.debug(f"Could not extract project path from {session_file.name}")
            return None

        except Exception as e:
            logger.debug(f"Error extracting project path from {session_file}: {e}")
            return None

    def _detect_session_type(self, session_file: Path) -> SessionType:
        """
        Detect the type of session file.
        """
        try:
            # Delegate to registry logic to ensure consistency
            from .adapters import get_adapter_registry

            registry = get_adapter_registry()
            adapter = registry.auto_detect_adapter(session_file)
            if adapter:
                # Map adapter name to SessionType
                # Adapter names: "claude", "codex", "gemini"
                name = adapter.name
                if name in ["claude", "codex", "gemini"]:
                    return name

            return "unknown"

        except Exception as e:
            print(
                f"[Watcher] Error detecting session type for {session_file.name}: {e}",
                file=sys.stderr,
            )
            return "unknown"

    def _get_trigger_for_session(self, session_file: Path):
        """
        获取或创建session的trigger

        Args:
            session_file: session文件路径

        Returns:
            TurnTrigger实例，如果session类型不支持则返回None
        """
        session_path = str(session_file)

        if session_path not in self._session_triggers:
            # Use registry to get adapter and trigger
            from .adapters import get_adapter_registry

            registry = get_adapter_registry()
            adapter = registry.auto_detect_adapter(session_file)

            if not adapter:
                logger.error(f"Unknown session type for {session_file.name}, cannot select trigger")
                return None

            self._session_triggers[session_path] = adapter.trigger

        return self._session_triggers[session_path]

    def _count_complete_turns(self, session_file: Path) -> int:
        """
        Unified interface to count complete dialogue turns for any session type.

        Returns:
            Number of complete dialogue turns (user request + assistant response)
        """
        trigger = self._get_trigger_for_session(session_file)
        if not trigger:
            return 0

        try:
            return trigger.count_complete_turns(session_file)
        except Exception as e:
            logger.error(f"Trigger error for {session_file.name}: {e}")
            return 0

    async def check_for_changes(self):
        """Check if any session file has been modified."""
        try:
            current_sizes, current_mtimes = self._get_session_stats()

            # Detect changed files
            changed_files = []
            for path, size in current_sizes.items():
                old_size = self.last_session_sizes.get(path)
                old_mtime = self.last_session_mtimes.get(path)
                mtime = current_mtimes.get(path)

                # Consider any file modification as "changed":
                # - Claude Code can compact/rewrite sessions (size can shrink)
                # - Some writes replace content without growing the file
                if old_size is None or old_mtime is None:
                    changed_files.append(Path(path))
                    logger.debug(f"Session file first seen: {Path(path).name} ({size} bytes)")
                    # Best-effort: link newly discovered Codex sessions to an active Codex terminal.
                    try:
                        self._maybe_link_codex_terminal(Path(path))
                    except Exception:
                        pass
                    # Reset idle final-commit attempt tracking for new files
                    self.last_final_commit_times.pop(path, None)
                    continue

                if size != old_size or (mtime is not None and mtime != old_mtime):
                    changed_files.append(Path(path))
                    logger.debug(
                        f"Session file changed: {Path(path).name} (size {old_size} -> {size} bytes)"
                    )
                    # Any activity should reset idle final-commit attempts
                    self.last_final_commit_times.pop(path, None)

            if changed_files:
                # Accumulate changed files instead of cancelling pending task
                # This fixes the bug where continuous activity prevents commits
                for f in changed_files:
                    self._pending_changed_files.add(str(f))

                # Only create new task if no pending task or previous one completed
                if not self.pending_commit_task or self.pending_commit_task.done():
                    logger.info(
                        f"Scheduling commit check for {len(self._pending_changed_files)} session file(s)"
                    )
                    self.pending_commit_task = asyncio.create_task(
                        self._debounced_commit_accumulated()
                    )
                else:
                    logger.debug(
                        f"Accumulated {len(changed_files)} file(s), total pending: {len(self._pending_changed_files)}"
                    )

            # Update tracked sizes
            self.last_session_sizes = current_sizes
            # Update tracked mtimes for change + idle detection
            self.last_session_mtimes = current_mtimes

        except Exception as e:
            logger.error(f"Error checking for changes: {e}", exc_info=True)
            print(f"[Watcher] Error checking for changes: {e}", file=sys.stderr)

    async def _debounced_commit_accumulated(self):
        """Wait for debounce period, then enqueue jobs for accumulated changed files."""
        try:
            # Wait for debounce period
            await asyncio.sleep(self.debounce_delay)

            # Grab and clear the accumulated files atomically
            changed_files = [Path(p) for p in self._pending_changed_files]
            self._pending_changed_files.clear()

            if not changed_files:
                return

            logger.info(f"Processing {len(changed_files)} accumulated session file(s)")

            # Check all changed files for new completed turns
            sessions_to_enqueue: list[tuple[Path, list[int]]] = []
            for session_file in changed_files:
                if not session_file.exists():
                    continue
                # Best-effort: keep terminal bindings fresh (especially after watcher restarts).
                try:
                    self._maybe_link_codex_terminal(session_file)
                except Exception:
                    pass
                new_turns = self._get_new_completed_turn_numbers(session_file)
                if new_turns:
                    sessions_to_enqueue.append((session_file, new_turns))

            if not sessions_to_enqueue:
                return

            # Prefer processing the most recently modified sessions first
            try:
                sessions_to_enqueue.sort(
                    key=lambda it: it[0].stat().st_mtime if it[0].exists() else 0,
                    reverse=True,
                )
            except Exception:
                pass

            from .db import get_database

            db = get_database()

            for session_file, new_turns in sessions_to_enqueue:
                logger.info(f"New completed turns detected in {session_file.name}: {new_turns}")
                print(
                    f"[Watcher] New completed turns detected in {session_file.name}: {new_turns}",
                    file=sys.stderr,
                )

                project_path = self._extract_project_path(session_file)
                if not project_path:
                    logger.debug(
                        f"Could not determine project path for {session_file.name}, skipping enqueue"
                    )
                    continue

                enqueued_any = False
                for turn_number in new_turns:
                    try:
                        db.enqueue_turn_summary_job(  # type: ignore[attr-defined]
                            session_file_path=session_file,
                            workspace_path=project_path,
                            turn_number=turn_number,
                            session_type=self._detect_session_type(session_file),
                        )
                        enqueued_any = True
                    except Exception as e:
                        logger.warning(
                            f"Failed to enqueue turn_summary for {session_file.name} #{turn_number}: {e}"
                        )

                if enqueued_any:
                    session_path = str(session_file)
                    self.last_stop_reason_counts[session_path] = max(
                        self.last_stop_reason_counts.get(session_path, 0), max(new_turns)
                    )

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in debounced enqueue: {e}", exc_info=True)
            print(f"[Watcher] Error in debounced enqueue: {e}", file=sys.stderr)

    async def _debounced_commit(self, changed_files: list):
        """Wait for debounce period, then enqueue jobs for changed files.

        DEPRECATED: Use _debounced_commit_accumulated instead.
        Kept for backwards compatibility.
        """
        try:
            # Wait for debounce period
            await asyncio.sleep(self.debounce_delay)

            from .db import get_database

            db = get_database()

            for session_file in changed_files:
                if not isinstance(session_file, Path):
                    session_file = Path(str(session_file))
                if not session_file.exists():
                    continue

                new_turns = self._get_new_completed_turn_numbers(session_file)
                if not new_turns:
                    continue

                project_path = self._extract_project_path(session_file)
                if not project_path:
                    continue

                for turn_number in new_turns:
                    try:
                        db.enqueue_turn_summary_job(  # type: ignore[attr-defined]
                            session_file_path=session_file,
                            workspace_path=project_path,
                            turn_number=turn_number,
                            session_type=self._detect_session_type(session_file),
                        )
                    except Exception:
                        continue

                session_path = str(session_file)
                self.last_stop_reason_counts[session_path] = max(
                    self.last_stop_reason_counts.get(session_path, 0), max(new_turns)
                )

        except asyncio.CancelledError:
            # Task was cancelled because a newer change was detected
            pass
        except Exception as e:
            print(f"[Watcher] Error in debounced enqueue: {e}", file=sys.stderr)

    async def _check_if_turn_complete(self, session_file: Path) -> bool:
        """
        Check if the session file has at least 1 new complete dialogue turn since last check.

        Supports both Claude Code and Codex formats:
        - Claude Code: Count user messages by timestamp
        - Codex: Uses token_count events (no deduplication needed)

        Each complete dialogue round consists of:
        1. User message/request
        2. Assistant response
        3. Turn completion marker (format-specific)

        Note: This method does NOT update last_stop_reason_counts.
        The count will be updated in _do_commit() after successful commit.
        """
        try:
            return bool(self._get_new_completed_turn_numbers(session_file))

        except Exception as e:
            logger.error(f"Error checking turn completion: {e}", exc_info=True)
            print(f"[Watcher] Error checking turn completion: {e}", file=sys.stderr)
            return False

    async def _do_commit(
        self,
        project_path: Path,
        session_file: Path,
        target_turn: Optional[int] = None,
        turn_content: Optional[str] = None,
        user_message_override: Optional[str] = None,
        from_catchup: bool = False,
        quiet: bool = False,
        debug_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        skip_dedup: bool = False,
    ) -> bool:
        """
        Async wrapper for committing a turn to the shadow git repository.

        Args:
            project_path: Path to the project directory
            session_file: Session file that triggered the commit
            target_turn: If provided, commit this specific turn number (catch-up)
            turn_content: Optional pre-extracted turn content
            user_message_override: Optional pre-extracted user message
            from_catchup: If True, indicates catch-up mode
            quiet: If True, suppress console output
        """
        try:
            # Delegate to synchronous commit method (runs in executor to avoid blocking)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._run_realign_commit,
                project_path,
                session_file,
                target_turn,
                turn_content,
                user_message_override,
                quiet,  # Pass quiet parameter
                debug_callback,  # Pass debug_callback
                skip_dedup,  # Pass skip_dedup
            )

            if result:
                logger.info(f"✓ Committed to {project_path.name}")
                if not quiet:
                    print(f"[Watcher] ✓ Auto-committed to {project_path.name}", file=sys.stderr)
                # Update last commit time for this project
                self.last_commit_times[str(project_path)] = time.time()

                # Update turn count baseline ONLY after successful commit
                # This prevents double-counting if commit fails
                session_path = str(session_file)
                current_count = self._count_complete_turns(session_file)
                if target_turn:
                    current_count = max(current_count, target_turn)
                self.last_stop_reason_counts[session_path] = current_count
                logger.debug(
                    f"Updated turn count baseline for {session_file.name}: {current_count}"
                )
            else:
                logger.warning(f"Commit failed for {project_path.name}")

            return bool(result)

        except Exception as e:
            logger.error(f"Error during commit for {project_path}: {e}", exc_info=True)
            print(f"[Watcher] Error during commit for {project_path}: {e}", file=sys.stderr)
            return False

    def _run_realign_commit(
        self,
        project_path: Path,
        session_file: Optional[Path] = None,
        target_turn: Optional[int] = None,
        turn_content: Optional[str] = None,
        user_message_override: Optional[str] = None,
        quiet: bool = False,
        debug_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        skip_dedup: bool = False,
        skip_session_summary: bool = False,
        no_track: bool = False,
    ) -> bool:
        """
        Execute commit with DB-backed lease locking to prevent cross-process races.

        Args:
            project_path: Path to the project directory
            quiet: If True, suppress console output

        Returns:
            True if commit was created, False otherwise

        The method will:
        - Acquire a DB lease lock to prevent concurrent commits across processes
        - Generate LLM-powered semantic commit message
        - Create DB record
        """
        try:
            from .db import get_database
            from .db.locks import lease_lock, lock_key_for_project_commit

            db = get_database()
            lock_key = lock_key_for_project_commit(project_path)

            with lease_lock(
                db,
                lock_key,
                owner=self.lock_owner,
                ttl_seconds=30 * 60,  # 30 minutes
                wait_timeout_seconds=5.0,
            ) as acquired:
                if not acquired:
                    print(
                        f"[Watcher] Another process is committing to {project_path.name}, skipping",
                        file=sys.stderr,
                    )
                    return False

                return self._do_commit_locked(
                    project_path,
                    session_file=session_file,
                    target_turn=target_turn,
                    turn_content=turn_content,
                    user_message_override=user_message_override,
                    quiet=quiet,
                    debug_callback=debug_callback,
                    skip_dedup=skip_dedup,
                    skip_session_summary=skip_session_summary,
                    no_track=no_track,
                )
        except Exception as e:
            print(f"[Watcher] Commit error: {e}", file=sys.stderr)
            return False

    def _do_commit_locked(
        self,
        project_path: Path,
        session_file: Optional[Path] = None,
        target_turn: Optional[int] = None,
        turn_content: Optional[str] = None,
        user_message_override: Optional[str] = None,
        quiet: bool = False,
        debug_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        skip_dedup: bool = False,
        skip_session_summary: bool = False,
        no_track: bool = False,
    ) -> bool:
        """
        Perform the actual commit operation to SQLite database.

        This method:
        1. Finds the latest session file for the project
        2. Redacts sensitive information from the session
        3. Generates LLM-powered semantic commit message
        4. Creates DB record

        Args:
            project_path: Path to the project directory
            session_file: Target session file (if None, will locate latest)
            target_turn: If provided, commit this specific turn
            turn_content: Optional precomputed turn content
            user_message_override: Optional precomputed user message
            quiet: If True, suppress console output

        Returns:
            True if commit was created, False otherwise
        """
        try:
            # Find the latest session file for this project if not provided
            if not session_file:
                session_file = self._find_latest_session(project_path)

            if not session_file:
                logger.warning("No session file found for commit")
                return False

            # Redact sensitive information from session file before committing
            session_file = self._handle_session_redaction(session_file, project_path, quiet=quiet)

            # Extract session information
            session_id = session_file.stem  # e.g., "minhao_claude_abc123"
            turn_number = target_turn or self._get_current_turn_number(session_file)
            user_message = user_message_override or self._extract_user_message_for_turn(
                session_file, turn_number
            )

            # V9: Get user identity for creator tracking
            from .config import ReAlignConfig

            config = ReAlignConfig.load()

            # Compute hash of current turn content (not the whole session file)
            if not turn_content:
                turn_content = self._extract_turn_content_by_number(session_file, turn_number)

            turn_hash = hashlib.md5((turn_content or "").encode("utf-8")).hexdigest()

            # SQLite Storage (authoritative): dedupe by (session_id, turn_number)
            from .db import get_database
            from .db.base import TurnRecord
            import uuid

            db = get_database()

            file_stat = session_file.stat()
            file_created = datetime.fromtimestamp(
                getattr(file_stat, "st_birthtime", file_stat.st_ctime)
            )
            session = db.get_or_create_session(
                session_id=session_id,
                session_file_path=session_file,
                session_type=self._detect_session_type(session_file),
                started_at=file_created,
                workspace_path=str(project_path) if project_path else None,
            )

            # Check no_track from parameter or existing session metadata (polling path)
            is_no_track = no_track
            if not is_no_track and session:
                session_meta = getattr(session, "metadata", None) or {}
                is_no_track = bool(session_meta.get("no_track", False))

            # Store no_track flag in session metadata if applicable
            if is_no_track:
                try:
                    db.update_session_metadata_flag(session_id, "no_track", True)
                except Exception:
                    pass

            takeover_attempt = False
            existing_turn = db.get_turn_by_number(session_id, turn_number)
            if existing_turn and not skip_dedup:
                existing_status = getattr(existing_turn, "turn_status", None)
                if existing_status in (None, "completed"):
                    logger.info(f"Turn already exists in DB: {session_id} #{turn_number}, skipping")
                    return False

                if existing_status == "processing":
                    # If a processing placeholder exists, avoid duplicate LLM calls unless it's stale.
                    try:
                        age_seconds = max(
                            0.0,
                            (
                                datetime.now()
                                - getattr(existing_turn, "created_at", datetime.now())
                            ).total_seconds(),
                        )
                    except Exception:
                        age_seconds = 0.0

                    if age_seconds < float(self.processing_turn_ttl_seconds):
                        logger.info(
                            f"Turn is already processing in DB: {session_id} #{turn_number} ({age_seconds:.0f}s), skipping"
                        )
                        return False

                    logger.warning(
                        f"Processing turn appears stale: {session_id} #{turn_number} ({age_seconds:.0f}s), taking over"
                    )
                    takeover_attempt = True

                if existing_status == "failed":
                    logger.warning(f"Turn previously failed: {session_id} #{turn_number}, skipping")
                    return False

            # Insert a processing placeholder BEFORE calling LLM so we can reflect runtime status
            # and avoid duplicate work in crash/restart scenarios.
            placeholder_hash = hashlib.md5(
                f"processing:{session_id}:{turn_number}:{time.time()}".encode("utf-8")
            ).hexdigest()
            processing_created_at = datetime.now()
            processing_turn = TurnRecord(
                id=str(uuid.uuid4()),
                session_id=session_id,
                turn_number=turn_number,
                user_message=user_message,
                assistant_summary=None,
                turn_status="processing",
                llm_title="running...",
                llm_description=None,
                model_name=None,
                if_last_task="unknown",
                satisfaction="unknown",
                content_hash=placeholder_hash,
                timestamp=processing_created_at,
                created_at=processing_created_at,
                git_commit_hash=None,
            )
            try:
                db.create_turn(processing_turn, content="")
            except Exception as e:
                # If we fail to store processing state, continue anyway (best-effort).
                logger.debug(f"Failed to write processing placeholder: {e}")

            try:
                # Skip LLM call for no-track mode
                if is_no_track:
                    llm_result = ("No Track", None, "No Track", "no", "fine")
                    logger.info(f"No-track mode: skipping LLM for {session_id} turn {turn_number}")
                else:
                    # Generate LLM summary with fallback for errors
                    llm_result = self._generate_llm_summary(
                        session_file,
                        turn_number=turn_number,
                        turn_content=turn_content,
                        user_message=user_message,
                        debug_callback=debug_callback,
                    )

                if not llm_result:
                    # LLM summary failed, use error marker to continue commit
                    logger.warning(
                        f"LLM summary generation failed for {session_file.name} turn {turn_number} - using error marker"
                    )
                    print(
                        f"[Watcher] ⚠ LLM API unavailable - using error marker for commit",
                        file=sys.stderr,
                    )

                    # Check if it's an API key problem
                    from .hooks import get_last_llm_error

                    last_error = get_last_llm_error()
                    if last_error:
                        if "API_KEY not set" in last_error or "api_key" in last_error.lower():
                            print(
                                f"[Watcher] ⓘ Configure API keys in Acme Settings to enable LLM summaries",
                                file=sys.stderr,
                            )
                        else:
                            print(f"[Watcher] ⓘ LLM Error: {last_error[:100]}", file=sys.stderr)

                    # Use explicit error marker
                    title = "⚠ LLM API Error - Summary unavailable"
                    model_name = "error-fallback"
                    description = f"LLM API failed. Error: {last_error[:200] if last_error else 'Unknown error'}"
                    if_last_task = "unknown"
                    satisfaction = "unknown"

                    llm_result = (title, model_name, description, if_last_task, satisfaction)

                title, model_name, description, if_last_task, satisfaction = llm_result

                # Validate title - reject if it's empty, too short, or looks like truncated JSON
                if not title or len(title.strip()) < 2:
                    logger.error(f"Invalid LLM title generated: '{title}' - skipping commit")
                    print(f"[Watcher] ✗ Invalid commit message title: '{title}'", file=sys.stderr)
                    raise RuntimeError(f"Invalid LLM title: {title!r}")

                if (
                    title.strip() in ["{", "}", "[", "]"]
                    or title.startswith("{")
                    and not title.endswith("}")
                ):
                    logger.error(f"Title appears to be truncated JSON: '{title}' - skipping commit")
                    print(f"[Watcher] ✗ Truncated JSON in title: '{title}'", file=sys.stderr)
                    raise RuntimeError(f"Truncated JSON title: {title!r}")

                logger.info(f"Committing turn {turn_number} for session {session_id}")
                new_turn = TurnRecord(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    turn_number=turn_number,
                    user_message=user_message,
                    assistant_summary=description,
                    turn_status="completed",
                    llm_title=title,
                    llm_description=description,
                    model_name=model_name,
                    if_last_task=if_last_task,
                    satisfaction=satisfaction,
                    content_hash=turn_hash,
                    timestamp=datetime.now(),
                    created_at=datetime.now(),
                    git_commit_hash=None,
                )
                db.create_turn(
                    new_turn,
                    content=turn_content or "",
                    skip_session_summary=skip_session_summary,
                )
                logger.info(f"✓ Saved turn {turn_number} to SQLite DB")
                print(f"[Watcher] ✓ Saved turn {turn_number} to SQLite DB", file=sys.stderr)
                return True
            except Exception as e:
                # If we were taking over a stale processing turn, a failure here should stop further retries.
                if takeover_attempt:
                    logger.error(
                        f"Takeover attempt failed for {session_id} #{turn_number}: {e}",
                        exc_info=True,
                    )
                    failed_turn = TurnRecord(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        turn_number=turn_number,
                        user_message=user_message,
                        assistant_summary=None,
                        turn_status="failed",
                        llm_title="failed",
                        llm_description=str(e)[:2000],
                        model_name=None,
                        if_last_task="unknown",
                        satisfaction="unknown",
                        content_hash=placeholder_hash,
                        timestamp=datetime.now(),
                        created_at=processing_created_at,
                        git_commit_hash=None,
                    )
                    try:
                        db.create_turn(
                            failed_turn,
                            content="",
                            skip_session_summary=skip_session_summary,
                        )
                    except Exception:
                        pass

                logger.error(f"Failed to write to SQLite DB: {e}", exc_info=True)
                print(f"[Watcher] ⚠ Failed to write to SQLite DB: {e}", file=sys.stderr)
                return False

        except Exception as e:
            logger.error(f"Commit error for {project_path.name}: {e}", exc_info=True)
            print(f"[Watcher] Commit error for {project_path.name}: {e}", file=sys.stderr)
            return False

    def _find_latest_session(self, project_path: Path) -> Optional[Path]:
        """Find the most recently modified session file for this project."""
        try:
            session_files = find_all_active_sessions(self.config, project_path)
            if not session_files:
                return None

            # Return most recently modified session
            return max(session_files, key=lambda f: f.stat().st_mtime)
        except Exception as e:
            logger.error(f"Failed to find latest session: {e}")
            return None

    def _handle_session_redaction(
        self, session_file: Path, project_path: Path, quiet: bool = False
    ) -> Path:
        """Check and redact sensitive information from session file.

        Args:
            session_file: Path to the session file
            project_path: Path to the project directory
            quiet: If True, suppress console output

        Returns:
            Path to the (possibly modified) session file
        """
        if not self.config.redact_on_match:
            return session_file

        try:
            from .redactor import check_and_redact_session, save_original_session

            content = session_file.read_text(encoding="utf-8")
            redacted_content, has_secrets, secrets = check_and_redact_session(
                content, redact_mode="auto", quiet=quiet
            )

            if has_secrets:
                logger.warning(f"Secrets detected: {len(secrets)} secret(s)")
                backup_path = save_original_session(session_file, project_path)
                session_file.write_text(redacted_content, encoding="utf-8")
                logger.info(f"Session redacted, original saved to {backup_path}")

            return session_file

        except Exception as e:
            logger.error(f"Failed to redact session: {e}")
            # Return original session file on error
            return session_file

    def _get_current_turn_number(self, session_file: Path) -> int:
        """Get the current turn number from a session file."""
        # Count the number of complete turns in the session
        return self._count_complete_turns(session_file)

    def _extract_last_user_message(self, session_file: Path) -> str:
        """
        Extract the user message for the current turn being committed.

        This is called AFTER a new user message arrives (which triggers the commit),
        so we need to extract the SECOND-TO-LAST valid user message, not the last one.
        The last user message belongs to the next turn that hasn't been processed yet.
        """
        from .hooks import clean_user_message

        try:
            user_messages = []

            with open(session_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        # Check for user message
                        if data.get("type") == "user":
                            message = data.get("message", {})
                            content = message.get("content", "")

                            extracted_text = None

                            if isinstance(content, str):
                                extracted_text = content
                            elif isinstance(content, list):
                                # Extract text from content blocks
                                text_parts = []
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        text_parts.append(item.get("text", ""))

                                # Only add if we found actual text content
                                # Skip entries that only contain tool_result items
                                if text_parts:
                                    extracted_text = "\n".join(text_parts)

                            if extracted_text:
                                # Clean the message (remove IDE tags, etc.)
                                cleaned_text = clean_user_message(extracted_text)

                                # Skip empty messages after cleaning
                                if not cleaned_text.strip():
                                    continue

                                # Skip continuation messages
                                if cleaned_text.startswith("This session is being continued"):
                                    continue

                                user_messages.append(cleaned_text)

                    except json.JSONDecodeError:
                        continue

            # Return second-to-last message if available, otherwise last message
            # This is because the commit is triggered by a new user message,
            # so the last message is for the NEXT turn, not the current one being committed
            if len(user_messages) >= 2:
                return user_messages[-2]
            elif len(user_messages) == 1:
                return user_messages[0]
            else:
                return "No user message found"

        except Exception as e:
            logger.error(f"Failed to extract user message: {e}")
            return "Error extracting message"

    def _create_temp_turn_title(
        self,
        session_file: Path,
        session_id: str,
        prompt: str,
        project_dir: str,
        no_track: bool = False,
    ) -> None:
        """Generate and store a temporary turn title for a newly submitted user prompt."""
        try:
            if not self.config.enable_temp_turn_titles:
                return
            if not session_file.exists():
                return

            trigger = self._get_trigger_for_session(session_file)
            analysis = trigger.get_detailed_analysis(session_file) if trigger else {}
            groups = analysis.get("groups", []) if isinstance(analysis, dict) else []
            if not groups:
                return

            group = groups[-1]
            try:
                turn_number = int(group.get("turn_number") or 0)
            except Exception:
                turn_number = 0
            if turn_number <= 0:
                return

            from .hooks import clean_user_message

            user_message = clean_user_message(prompt) if prompt else ""
            if not user_message:
                user_message = str(group.get("user_message") or "")

            # Skip LLM call for no-track mode
            if no_track:
                title = "No Track"
                model_name = None
                description = "No Track"
                if_last_task = "no"
                satisfaction = "fine"
            else:
                turn_content = self._extract_turn_content_by_number(session_file, turn_number)
                result = self._generate_llm_summary(
                    session_file,
                    turn_number=turn_number,
                    turn_content=turn_content,
                    user_message=user_message or None,
                    session_id=session_id or session_file.stem,
                )
                if not result:
                    return

                title, model_name, description, if_last_task, satisfaction = result
                if not title:
                    return

            from .db import get_database
            from .db.base import TurnRecord
            from .config import ReAlignConfig
            import uuid

            db = get_database()

            file_stat = session_file.stat()
            file_created = datetime.fromtimestamp(
                getattr(file_stat, "st_birthtime", file_stat.st_ctime)
            )

            project_path = None
            if project_dir:
                try:
                    candidate = Path(project_dir)
                    if candidate.exists():
                        project_path = candidate
                except Exception:
                    project_path = None
            if project_path is None:
                project_path = self._extract_project_path(session_file)
            db.get_or_create_session(
                session_id=session_id or session_file.stem,
                session_file_path=session_file,
                session_type=self._detect_session_type(session_file),
                started_at=file_created,
                workspace_path=str(project_path) if project_path else None,
            )

            existing = db.get_turn_by_number(session_id or session_file.stem, turn_number)
            if existing:
                existing_status = getattr(existing, "turn_status", None)
                if existing_status in (None, "completed", "processing"):
                    return

            config = ReAlignConfig.load()
            content_hash = hashlib.md5(
                (turn_content or user_message or title).encode("utf-8")
            ).hexdigest()
            now = datetime.now()

            temp_turn = TurnRecord(
                id=str(uuid.uuid4()),
                session_id=session_id or session_file.stem,
                turn_number=turn_number,
                user_message=user_message or None,
                assistant_summary=None,
                turn_status="temp",
                llm_title=title,
                temp_title=title,
                llm_description=description or None,
                model_name=model_name,
                if_last_task=if_last_task,
                satisfaction=satisfaction,
                content_hash=content_hash,
                timestamp=now,
                created_at=now,
                git_commit_hash=None,
            )
            db.create_turn(temp_turn, content=turn_content or "", skip_session_summary=True)
        except Exception as e:
            logger.debug(f"Failed to create temp turn title: {e}")

    def _extract_user_message_for_turn(self, session_file: Path, turn_number: int) -> str:
        """Extract user message for a specific turn using the active trigger."""
        try:
            trigger = self._get_trigger_for_session(session_file)
            info = trigger.extract_turn_info(session_file, turn_number)
            if info and info.user_message:
                return info.user_message
        except Exception as e:
            logger.error(f"Failed to extract user message for turn {turn_number}: {e}")
        return "No user message found"

    def _extract_turn_content_by_number(self, session_file: Path, turn_number: int) -> str:
        """Extract content for a specific turn (supports JSONL and JSON formats)."""
        try:
            trigger = self._get_trigger_for_session(session_file)
            analysis = trigger.get_detailed_analysis(session_file)
            group = None
            for g in analysis.get("groups", []):
                if g.get("turn_number") == turn_number:
                    group = g
                    break
            if not group:
                return ""

            # For non-JSONL formats (e.g., Gemini JSON), use extract_turn_info
            session_format = analysis.get("format", "")
            if session_format in ("gemini_json", "gemini"):
                turn_info = trigger.extract_turn_info(session_file, turn_number)
                if turn_info and turn_info.get("turn_content"):
                    return turn_info["turn_content"]
                # Fallback: construct content from group data
                return json.dumps(
                    {
                        "turn_number": turn_number,
                        "user_message": group.get("user_message", ""),
                        "assistant_response": group.get("summary_message", ""),
                    },
                    ensure_ascii=False,
                    indent=2,
                )

            # For JSONL formats, extract by line numbers
            start_line = group.get("start_line") or (group.get("lines") or [None])[0]
            end_line = group.get("end_line") or (group.get("lines") or [None])[-1]
            if not start_line or not end_line:
                return ""

            lines = []
            with open(session_file, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f, 1):
                    if start_line <= idx <= end_line:
                        lines.append(line)
                    if idx > end_line:
                        break
            return "".join(lines)
        except Exception as e:
            logger.error(f"Failed to extract turn content for turn {turn_number}: {e}")
            print(f"[Debug] Failed to extract turn content: {e}", file=sys.stderr)
            return ""

    def _extract_assistant_summary(self, session_file: Path) -> str:
        """Extract a summary of the assistant's response from session file."""
        try:
            if session_file.is_dir():
                # For directory sessions (Antigravity), we don't have a simple way to extract assistant summary
                # from a single file scan. Return generic message or use trigger if possible.
                return "Antigravity Session State"

            summary = self._find_latest_structured_summary(session_file)
            if summary:
                summary = summary.strip()
                return summary[:300] + ("..." if len(summary) > 300 else "")
        except Exception as e:
            logger.debug(f"Structured summary extraction failed: {e}")

        try:
            # Extract last assistant response text
            assistant_text = ""

            if session_file.is_dir():
                return "Antigravity Session"

            with open(session_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        if data.get("type") == "assistant":
                            message = data.get("message", {})
                            content = message.get("content", [])

                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        assistant_text = item.get("text", "")

                    except json.JSONDecodeError:
                        continue

            # Truncate to reasonable length
            if assistant_text:
                # Take first 300 characters as summary
                summary = assistant_text[:300]
                if len(assistant_text) > 300:
                    summary += "..."
                return summary
            else:
                return "Assistant response"

        except Exception as e:
            logger.error(f"Failed to extract assistant summary: {e}")
            return "Error extracting summary"

    def _find_latest_structured_summary(self, session_file: Path) -> Optional[str]:
        """
        Find the latest agent-authored summary block in the session.

        Claude Code emits dedicated summary records (`{\"type\":\"summary\",\"summary\":\"...\"}`)
        after each turn. We scan from the end to pick the most recent one, which keeps the
        summary aligned with the turn that just finished.
        """
        try:
            if session_file.is_dir():
                return None

            with open(session_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if data.get("type") == "summary":
                    summary = data.get("summary") or ""
                    if summary and summary.strip():
                        return summary.strip()

            return None

        except Exception as e:
            logger.error(f"Failed to find structured summary: {e}")
            return None

    def _extract_current_turn_content(self, session_file: Path) -> str:
        """
        Extract only the content for the current turn being committed.

        Since commit is triggered by a new user message (Turn N+1), we need to extract
        the content from the PREVIOUS turn (Turn N), which includes:
        - The second-to-last user message
        - All assistant responses after that user message
        - But BEFORE the last user message (which belongs to Turn N+1)

        Returns:
            JSONL content for the current turn only
        """
        try:
            lines = []
            user_message_indices = []

            lines = []
            user_message_indices = []

            if session_file.is_dir():
                # For directory sessions, delegate to extract_turn_content_by_number (via trigger)
                # We don't support partial "current turn" extraction for Antigravity yet
                # as it treats the whole state as one turn.
                # Just return an empty string or the full content if needed.
                # But _extract_current_turn_content is usually used for diffing?
                # or extracting just the User Message to identify intent.
                trigger = self._get_trigger_for_session(session_file)
                if trigger:
                    # Get current turn number
                    turn = self._get_current_turn_number(session_file)
                    info = trigger.extract_turn_info(session_file, turn)
                    if info:
                        return info.user_message
                return ""

            # Read all lines and track user message positions
            with open(session_file, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    lines.append(line)
                    try:
                        data = json.loads(line.strip())
                        if data.get("type") == "user":
                            message = data.get("message", {})
                            content = message.get("content", "")

                            # Check if this is a real user message (not tool result, IDE notification, etc.)
                            is_real_message = False
                            if isinstance(content, str):
                                if not content.startswith(
                                    "This session is being continued"
                                ) and not content.startswith("<ide_opened_file>"):
                                    is_real_message = True
                            elif isinstance(content, list):
                                text_parts = [
                                    item.get("text", "")
                                    for item in content
                                    if isinstance(item, dict) and item.get("type") == "text"
                                ]
                                if text_parts:
                                    combined_text = "\n".join(text_parts)
                                    if not combined_text.startswith(
                                        "This session is being continued"
                                    ) and not combined_text.startswith("<ide_opened_file>"):
                                        is_real_message = True

                            if is_real_message:
                                user_message_indices.append(idx)
                    except json.JSONDecodeError:
                        continue

            # Determine the range for current turn
            if len(user_message_indices) >= 2:
                # Extract from second-to-last user message up to (but not including) last user message
                start_idx = user_message_indices[-2]
                end_idx = user_message_indices[-1]
                turn_lines = lines[start_idx:end_idx]
            elif len(user_message_indices) == 1:
                # First turn: from first user message to end
                start_idx = user_message_indices[0]
                turn_lines = lines[start_idx:]
            else:
                # No valid user messages
                return ""

            return "".join(turn_lines)

        except Exception as e:
            logger.error(f"Failed to extract current turn content: {e}", exc_info=True)
            return ""

    def _generate_llm_summary(
        self,
        session_file: Optional[Path],
        turn_number: Optional[int] = None,
        turn_content: Optional[str] = None,
        user_message: Optional[str] = None,
        debug_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        session_id: Optional[str] = None,
    ) -> Optional[tuple[str, str, str, str, str]]:
        """
        Generate LLM-powered summary for the CURRENT TURN only.

        Priority:
        1. MCP Sampling API (if enabled and available)
        2. Direct Claude/OpenAI API calls (existing fallback)

        Returns:
            Tuple of (title, model_name, description, if_last_task, satisfaction), or None if LLM is disabled or fails
        """
        try:
            if not self.config.use_LLM:
                logger.debug("LLM summary disabled in config")
                return None

            if turn_number is None and session_file is not None:
                turn_number = self._get_current_turn_number(session_file)

            # Resolve session_id from file or parameter
            resolved_session_id = session_id
            if resolved_session_id is None and session_file is not None:
                resolved_session_id = session_file.stem

            recent_ctx = ""
            previous_records = []
            previous_commit_title = None
            try:
                # Get recent turns from database for context
                from .db import get_database

                db = get_database()
                session_id = resolved_session_id
                recent_turns = db.get_turns_for_session(session_id)
                if recent_turns:
                    # Get last 5 turn titles
                    for turn in recent_turns[-5:]:
                        if turn.llm_title:
                            previous_records.append(turn.llm_title)
                    # Get the most recent title
                    if previous_records:
                        previous_commit_title = previous_records[-1]
                        recent_ctx = "Recent turns:\n" + "\n".join(
                            f"- {t}" for t in previous_records
                        )
            except Exception:
                recent_ctx = ""
                previous_records = []

            # Extract full turn content first (includes all messages, thinking, etc.)
            if turn_content is None and session_file is not None:
                turn_content = self._extract_turn_content_by_number(session_file, turn_number)

            # Prefer trigger-derived fields: user_message + assistant summary + turn_status
            group = None
            if session_file is not None:
                try:
                    trigger = self._get_trigger_for_session(session_file)
                    analysis = trigger.get_detailed_analysis(session_file)
                    group = next(
                        (
                            g
                            for g in analysis.get("groups", [])
                            if g.get("turn_number") == turn_number
                        ),
                        None,
                    )
                except Exception:
                    group = None

            assistant_summary = None
            turn_status = "unknown"

            if group:
                if not user_message:
                    user_message = group.get("user_message") or user_message
                assistant_summary = group.get("summary_message") or assistant_summary
                turn_status = group.get("turn_status") or turn_status

            # Robust fallback for directory sessions (Antigravity) if group lookup failed
            if (
                session_file is not None
                and session_file.is_dir()
                and (not user_message or not assistant_summary)
            ):
                logger.info("Using fallback extraction for Antigravity directory session")
                print(
                    f"[Debug] Antigravity fallback: user_message={bool(user_message)}, assistant_summary={bool(assistant_summary)}",
                    file=sys.stderr,
                )
                if not user_message:
                    # For Antigravity, turn_content is essentially the user message (full state)
                    user_message = turn_content
                    print(
                        f"[Debug] Set user_message from turn_content: {len(user_message) if user_message else 0} chars",
                        file=sys.stderr,
                    )
                if not assistant_summary:
                    assistant_summary = "Antigravity Session State"
                turn_status = "completed"

            print(
                f"[Debug] Before LLM call: user_message={len(user_message) if user_message else 0} chars, assistant_summary={bool(assistant_summary)}",
                file=sys.stderr,
            )
            if user_message and assistant_summary:
                from .hooks import generate_summary_with_llm_from_turn_context

                # Pass full turn content to include all messages (user, assistant text, thinking)
                # but exclude tool use and code changes (handled by filter_session_content)
                title, model_name, description, if_last_task, satisfaction = (
                    generate_summary_with_llm_from_turn_context(
                        user_message=user_message,
                        assistant_summary=assistant_summary,
                        turn_status=turn_status,
                        recent_commit_context=recent_ctx,
                        provider=self.config.llm_provider,
                        previous_commit_title=previous_commit_title,
                        full_turn_content=turn_content,  # Pass full turn content
                        previous_records=previous_records,  # Pass extracted records from git history
                        debug_callback=debug_callback,  # Pass debug callback
                    )
                )

                if title:
                    logger.info(f"Generated LLM summary from turn context using {model_name}")
                    print(
                        f"[Watcher] ✓ Generated summary from turn context ({model_name})",
                        file=sys.stderr,
                    )
                    return (
                        title,
                        model_name or "unknown",
                        description or "",
                        if_last_task,
                        satisfaction,
                    )

                if session_file is not None and session_file.is_dir():
                    # Fallback if LLM fails for Antigravity
                    print(
                        f"[Watcher] ⚠ LLM summary failed/empty, using generic fallback for Antigravity",
                        file=sys.stderr,
                    )
                    return (
                        "Update Antigravity Brain",
                        "fallback",
                        "Automatic update of brain artifacts",
                        "yes",
                        "fine",
                    )

            # Fallback: Extract turn content and use the legacy pipeline
            if turn_content is None and session_file is not None:
                turn_content = self._extract_turn_content_by_number(session_file, turn_number)
            if not turn_content:
                logger.warning("No content found for current turn")
                return None

            if recent_ctx:
                try:
                    recent_line = json.dumps(
                        {
                            "type": "assistant",
                            "message": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Recent commit context:\n{recent_ctx}",
                                    }
                                ]
                            },
                        },
                        ensure_ascii=False,
                    )
                    if not turn_content.endswith("\n"):
                        turn_content += "\n"
                    turn_content += recent_line + "\n"
                except Exception:
                    pass

            # Use direct API calls for LLM summary
            from .hooks import generate_summary_with_llm

            title, model_name, description, if_last_task, satisfaction = generate_summary_with_llm(
                turn_content,
                max_chars=500,
                provider=self.config.llm_provider,
                previous_commit_title=previous_commit_title,
                debug_callback=debug_callback,
            )

            if title:
                if model_name:
                    logger.info(f"Generated LLM summary using {model_name}")
                    print(f"[Watcher] ✓ Generated LLM summary using {model_name}", file=sys.stderr)
                return (
                    title,
                    model_name or "unknown",
                    description or "",
                    if_last_task,
                    satisfaction,
                )
            else:
                logger.warning("LLM summary generation returned empty result")

                if session_file is not None and session_file.is_dir():
                    # Fallback if LLM fails for Antigravity (generic path)
                    print(
                        f"[Watcher] ⚠ LLM summary returned empty, using fallback for Antigravity",
                        file=sys.stderr,
                    )
                    return (
                        "Update Antigravity Brain",
                        "fallback",
                        "Automatic update of brain artifacts",
                        "yes",
                        "fine",
                    )

                return None

        except Exception as e:
            logger.error(f"Failed to generate LLM summary: {e}", exc_info=True)
            print(f"[Watcher] Failed to generate LLM summary: {e}", file=sys.stderr)

            # Record the error for later use in fallback logic
            from .hooks import set_last_llm_error

            set_last_llm_error(str(e))

            # Robust fallback for Antigravity directory sessions if anything fails
            if session_file is not None and session_file.is_dir():
                print(
                    f"[Watcher] ⚠ Using generic fallback after exception for Antigravity",
                    file=sys.stderr,
                )
                return (
                    "Update Antigravity Brain",
                    "fallback",
                    "Automatic update of brain artifacts",
                    "yes",
                    "fine",
                )

            return None

    @staticmethod
    def _extract_latest_commit_title(context: str) -> Optional[str]:
        """
        Parse the most recent commit title from a textual recent-commit context block.
        """
        if not context:
            return None

        for line in context.splitlines():
            stripped = line.strip()
            if not stripped or stripped.lower().startswith("recent commits"):
                continue
            if stripped.startswith("-"):
                payload = stripped[1:].strip()
                if not payload:
                    continue
                parts = payload.split(" ", 1)
                if len(parts) == 2:
                    return parts[1].strip() or None
                return parts[0].strip() or None
        return None

    def _get_session_start_time(self, session_file: Path) -> Optional[float]:
        """
        Get the session start time from the first message timestamp.

        Returns:
            Unix timestamp (float) or None if not found
        """
        try:
            if session_file.is_dir():
                # For directories, just use creation time
                try:
                    stat = session_file.stat()
                    return getattr(stat, "st_birthtime", stat.st_ctime)
                except:
                    return session_file.stat().st_ctime

            with open(session_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        # Look for timestamp field in various formats
                        timestamp_str = data.get("timestamp")
                        if timestamp_str:
                            # Parse ISO 8601 timestamp
                            from datetime import datetime

                            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                            return dt.timestamp()

                    except (json.JSONDecodeError, ValueError, KeyError):
                        continue

            # Fallback: use session file's creation time
            return session_file.stat().st_ctime

        except Exception as e:
            logger.error(f"Failed to get session start time: {e}")
            return None

    async def auto_init_projects(self):
        """
        Ensure global Aline config and database exist.
        """
        try:
            if is_aline_initialized():
                return

            from .commands.init import init_global

            result = await asyncio.get_event_loop().run_in_executor(None, init_global, False)
            if result.get("success"):
                logger.info("✓ Global Aline initialization ready")
            else:
                logger.error(f"✗ Global init failed: {result.get('message')}")

        except Exception as e:
            logger.error(f"Error in auto_init_projects: {e}", exc_info=True)

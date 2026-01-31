"""
Background worker for durable jobs queue.

This process consumes jobs from the SQLite `jobs` table:
- turn_summary: generate/store a turn (LLM + content snapshot)
- session_summary: aggregate session title/summary from turns
- agent_description: regenerate agent description from session summaries
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .db.sqlite_db import SQLiteDatabase
from .db.locks import make_lock_owner

logger = logging.getLogger(__name__)


class PermanentJobError(RuntimeError):
    """Non-retryable job failure."""


def _backoff_seconds(attempts: int, *, base: float = 2.0, cap: float = 300.0) -> float:
    n = max(0, int(attempts))
    return float(min(cap, base * math.pow(2.0, min(n, 8))))


def _max_attempts() -> int:
    """
    Maximum retry attempts before marking a job as failed.

    Set via REALIGN_JOB_MAX_ATTEMPTS (default: 10).
    """
    raw = os.getenv("REALIGN_JOB_MAX_ATTEMPTS", "10")
    try:
        v = int(raw)
        return max(1, v)
    except Exception:
        return 10


class AlineWorker:
    def __init__(self, db: SQLiteDatabase, *, poll_interval_seconds: float = 0.5):
        self.db = db
        self.poll_interval_seconds = float(poll_interval_seconds)
        self.worker_id = make_lock_owner("worker")
        self.running = False

        # Reuse the existing commit pipeline (LLM turn creation) implemented on DialogueWatcher.
        # We instantiate it without starting its polling loop.
        from .watcher_core import DialogueWatcher

        self._watcher = DialogueWatcher()

    async def start(self) -> None:
        self.running = True
        logger.info(f"Worker started: id={self.worker_id}")

        while self.running:
            try:
                job = self.db.claim_next_job(
                    worker_id=self.worker_id,
                    kinds=["turn_summary", "session_summary", "agent_description"],
                )
                if not job:
                    await asyncio.sleep(self.poll_interval_seconds)
                    continue

                await self._process_job(job)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info("Worker stopped")

    async def stop(self) -> None:
        self.running = False

    async def _process_job(self, job: Dict[str, Any]) -> None:
        job_id = str(job.get("id"))
        kind = str(job.get("kind"))
        payload = job.get("payload") or {}

        try:
            if kind == "turn_summary":
                await self._process_turn_summary_job(payload)
                # Always enqueue a session_summary job after a successful turn job.
                # This ensures session summaries update even if the turn already existed in DB
                # (i.e. the turn job was effectively a validation/no-op).
                try:
                    session_id = str(payload.get("session_id") or "")
                    if session_id:
                        self.db.enqueue_session_summary_job(session_id=session_id)
                except Exception as e:
                    logger.warning(f"Failed to enqueue session summary after turn job: {e}")
                    print(
                        f"[Worker] ⚠ Failed to enqueue session summary job for session_id={session_id}: {e}",
                        file=sys.stderr,
                    )
                self.db.finish_job(job_id=job_id, worker_id=self.worker_id, success=True)
                return

            if kind == "session_summary":
                ok = await self._process_session_summary_job(payload)
                if ok:
                    self.db.finish_job(job_id=job_id, worker_id=self.worker_id, success=True)
                else:
                    attempts = int(job.get("attempts") or 0)
                    next_attempt = attempts + 1
                    if next_attempt >= _max_attempts():
                        self.db.finish_job(
                            job_id=job_id,
                            worker_id=self.worker_id,
                            success=False,
                            error="session summary failed (max attempts reached)",
                            permanent_fail=True,
                        )
                    else:
                        delay = _backoff_seconds(attempts)
                        self.db.finish_job(
                            job_id=job_id,
                            worker_id=self.worker_id,
                            success=False,
                            error="session summary failed",
                            retry_after_seconds=delay,
                        )
                return

            if kind == "agent_description":
                await self._process_agent_description_job(payload)
                self.db.finish_job(job_id=job_id, worker_id=self.worker_id, success=True)
                return

            # Unknown job kind: mark as permanently failed to avoid infinite loops.
            self.db.finish_job(
                job_id=job_id,
                worker_id=self.worker_id,
                success=False,
                error=f"Unknown job kind: {kind}",
                permanent_fail=True,
            )
        except PermanentJobError as e:
            logger.warning(f"Permanent job failure: {kind} id={job_id} err={e}")
            self.db.finish_job(
                job_id=job_id,
                worker_id=self.worker_id,
                success=False,
                error=str(e),
                permanent_fail=True,
            )
        except Exception as e:
            attempts = int(job.get("attempts") or 0)
            next_attempt = attempts + 1
            if next_attempt >= _max_attempts():
                logger.warning(
                    f"Job failed (max attempts reached): {kind} id={job_id} err={e}",
                    exc_info=True,
                )
                self.db.finish_job(
                    job_id=job_id,
                    worker_id=self.worker_id,
                    success=False,
                    error=f"{e} (max attempts reached)",
                    permanent_fail=True,
                )
                return
            delay = _backoff_seconds(attempts)
            logger.warning(f"Job failed: {kind} id={job_id} err={e}", exc_info=True)
            self.db.finish_job(
                job_id=job_id,
                worker_id=self.worker_id,
                success=False,
                error=str(e),
                retry_after_seconds=delay,
            )

    async def _process_turn_summary_job(self, payload: Dict[str, Any]) -> None:
        session_id = str(payload.get("session_id") or "")
        turn_number = int(payload.get("turn_number") or 0)
        session_file_path = Path(str(payload.get("session_file_path") or ""))
        workspace_path_raw = payload.get("workspace_path")
        skip_session_summary = bool(payload.get("skip_session_summary") or False)
        expected_turns_raw = payload.get("expected_turns")
        expected_turns = int(expected_turns_raw) if expected_turns_raw is not None else None
        skip_dedup = bool(payload.get("skip_dedup") or False)
        no_track = bool(payload.get("no_track") or False)
        agent_id = str(payload.get("agent_id") or "")

        if not session_id or turn_number <= 0 or not session_file_path:
            raise ValueError(f"Invalid turn_summary payload: {payload}")

        if not session_file_path.exists():
            raise FileNotFoundError(f"Session file not found: {session_file_path}")

        project_path: Optional[Path] = None
        if isinstance(workspace_path_raw, str) and workspace_path_raw.strip():
            project_path = Path(workspace_path_raw.strip())
            if not project_path.exists():
                project_path = None
        if project_path is None:
            project_path = self._watcher._extract_project_path(session_file_path)

        if not project_path:
            raise RuntimeError(f"Could not determine project path for session {session_id}")

        # Run the existing commit pipeline (writes turn record + content).
        created = self._watcher._run_realign_commit(
            project_path,
            session_file=session_file_path,
            target_turn=turn_number,
            quiet=True,
            skip_session_summary=skip_session_summary,
            skip_dedup=skip_dedup,
            no_track=no_track,
        )

        # Link session to agent after commit ensures session exists in DB
        if agent_id and session_id:
            try:
                self.db.update_session_agent_id(session_id, agent_id)
            except Exception:
                pass

        if created:
            if expected_turns:
                self._enqueue_session_summary_if_complete(session_id, expected_turns)
            return

        # If no new turn was created, decide if this job is actually complete.
        existing = self.db.get_turn_by_number(session_id, turn_number)
        if existing is None:
            raise RuntimeError(
                f"Turn not created and not present in DB: {session_id} #{turn_number}"
            )

        status = getattr(existing, "turn_status", None)
        if status in (None, "completed"):
            if expected_turns:
                self._enqueue_session_summary_if_complete(session_id, expected_turns)
            return
        if status == "processing":
            # Another worker may be processing; retry shortly.
            raise RuntimeError(f"Turn is processing: {session_id} #{turn_number}")
        if status == "failed":
            raise PermanentJobError(f"Turn failed previously: {session_id} #{turn_number}")

    def _enqueue_session_summary_if_complete(self, session_id: str, expected_turns: int) -> None:
        try:
            completed = self.db.get_completed_turn_count(session_id, up_to=int(expected_turns))
            if completed >= int(expected_turns):
                self.db.enqueue_session_summary_job(session_id=session_id)
        except Exception as e:
            logger.warning(f"Failed to enqueue session summary after import for {session_id}: {e}")

    async def _process_session_summary_job(self, payload: Dict[str, Any]) -> bool:
        session_id = str(payload.get("session_id") or "")
        if not session_id:
            raise ValueError(f"Invalid session_summary payload: {payload}")

        from .events.session_summarizer import update_session_summary_now

        return bool(update_session_summary_now(self.db, session_id))

    async def _process_agent_description_job(self, payload: Dict[str, Any]) -> None:
        agent_id = str(payload.get("agent_id") or "")
        if not agent_id:
            raise ValueError(f"Invalid agent_description payload: {payload}")

        from .events.agent_summarizer import force_update_agent_description

        force_update_agent_description(self.db, agent_id)

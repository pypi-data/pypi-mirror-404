#!/usr/bin/env python3
"""
Sync agent command - Bidirectional sync for shared agents.

Pull remote sessions, merge locally (union of sessions, dedup by content_hash),
push merged result back. Uses optimistic locking via sync_version.

Sync works with unencrypted shares only.
"""

import json
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from ..logging_config import setup_logger

logger = setup_logger("realign.commands.sync_agent", "sync_agent.log")

MAX_SYNC_RETRIES = 3


def sync_agent_command(
    agent_id: str,
    backend_url: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Sync an agent's sessions with the remote share.

    Algorithm:
    1. Load local state (agent_info, sessions, content hashes)
    2. Pull remote state (full download via export endpoint)
    3. Merge: union of sessions deduped by content_hash, last-write-wins for name/desc
    4. Push merged state via PUT with optimistic locking
    5. Update local sync metadata

    Args:
        agent_id: The agent_info ID to sync
        backend_url: Backend server URL (uses config default if None)
        progress_callback: Optional callback for progress updates

    Returns:
        {"success": True, "sessions_pulled": N, "sessions_pushed": N, ...} on success
        {"success": False, "error": str} on failure
    """
    def _progress(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    if not HTTPX_AVAILABLE:
        return {"success": False, "error": "httpx package not installed"}

    # Get backend URL
    if backend_url is None:
        from ..config import ReAlignConfig

        config = ReAlignConfig.load()
        backend_url = config.share_backend_url or "https://realign-server.vercel.app"

    # Get database
    from ..db import get_database

    db = get_database()

    # 1. Load local state
    _progress("Loading local agent data...")

    # Support prefix matching for agent_id
    agent_info = db.get_agent_info(agent_id)
    if not agent_info:
        # Try prefix match
        all_agents = db.list_agent_info()
        matches = [a for a in all_agents if a.id.startswith(agent_id)]
        if len(matches) == 1:
            agent_info = matches[0]
            agent_id = agent_info.id
        elif len(matches) > 1:
            return {"success": False, "error": f"Ambiguous agent_id prefix '{agent_id}' matches {len(matches)} agents"}
        else:
            return {"success": False, "error": f"Agent not found: {agent_id}"}

    if not agent_info.share_id or not agent_info.share_url:
        return {"success": False, "error": "Agent has no share metadata (not shared yet)"}

    token = agent_info.share_admin_token or agent_info.share_contributor_token
    if not token:
        return {"success": False, "error": "No token available for sync (need admin or contributor token)"}

    share_id = agent_info.share_id
    local_sync_version = agent_info.sync_version or 0

    # Repair: backfill agent_id on sessions linked via windowlink but missing agent_id.
    # This handles Claude sessions where the watcher created the session before the
    # agent_id was known (race between polling and stop-hook signals).
    try:
        conn = db._get_connection()
        unlinked = conn.execute(
            """SELECT DISTINCT w.session_id
               FROM windowlink w
               JOIN sessions s ON s.id = w.session_id
               WHERE w.agent_id = ?
                 AND (s.agent_id IS NULL OR s.agent_id = '')""",
            (agent_id,),
        ).fetchall()
        for row in unlinked:
            sid = row[0]
            if sid:
                db.update_session_agent_id(sid, agent_id)
                logger.info(f"Sync repair: linked session {sid} to agent {agent_id}")
        if unlinked:
            _progress(f"Repaired {len(unlinked)} unlinked session(s)")
    except Exception as e:
        logger.warning(f"Session repair step failed (non-fatal): {e}")

    local_sessions = db.get_sessions_by_agent_id(agent_id)
    local_content_hashes = db.get_agent_content_hashes(agent_id)

    logger.info(
        f"Sync: agent={agent_id}, share={share_id}, "
        f"local_sessions={len(local_sessions)}, local_hashes={len(local_content_hashes)}"
    )

    # 2. Pull remote state
    _progress("Pulling remote data...")

    remote_data = _pull_remote(backend_url, share_id)
    if not remote_data.get("success"):
        return {"success": False, "error": f"Failed to pull remote: {remote_data.get('error')}"}

    conversation_data = remote_data["data"]
    remote_sync_meta = conversation_data.get("sync_metadata", {})
    remote_sync_version = remote_sync_meta.get("sync_version", 0)

    remote_sessions_data = conversation_data.get("sessions", [])
    remote_event = conversation_data.get("event", {})

    # 3. Merge
    _progress("Merging sessions...")

    # Collect remote content hashes
    remote_content_hashes = set()
    for session_data in remote_sessions_data:
        for turn_data in session_data.get("turns", []):
            h = turn_data.get("content_hash")
            if h:
                remote_content_hashes.add(h)

    # Import new remote sessions/turns locally
    sessions_pulled = 0
    from .import_shares import import_session_with_turns

    for session_data in remote_sessions_data:
        session_id = session_data.get("session_id", "")
        session_turns = session_data.get("turns", [])

        # Check if any turns in this session are new to THIS AGENT (not globally)
        new_turns = [
            t for t in session_turns
            if t.get("content_hash") and t["content_hash"] not in local_content_hashes
        ]

        # Check if session exists and whether it's linked to this agent
        existing_session = db.get_session_by_id(session_id)
        session_is_new = existing_session is None
        session_needs_linking = existing_session and existing_session.agent_id != agent_id

        # Import if: new turns, or session is new, or session needs linking
        if not new_turns and not session_is_new and not session_needs_linking:
            continue

        # Import the session (import_session_with_turns handles dedup by content_hash)
        should_count = session_is_new or session_needs_linking
        try:
            # Suppress auto-summaries during sync
            os.environ["REALIGN_DISABLE_AUTO_SUMMARIES"] = "1"
            import_result = import_session_with_turns(
                session_data, f"agent-{agent_id}", agent_info.share_url, db, force=False
            )
            # Count as pulled if: created new session/turns, or session was new/needed linking
            if (import_result.get("sessions", 0) > 0 or import_result.get("turns", 0) > 0
                    or should_count):
                sessions_pulled += 1
        except Exception as e:
            logger.error(f"Failed to import remote session {session_id}: {e}")
            # Still count if we intended to import this session
            if should_count:
                sessions_pulled += 1

        # Always link session to agent (even if import was skipped)
        try:
            db.update_session_agent_id(session_id, agent_id)
        except Exception as e:
            logger.error(f"Failed to link session {session_id} to agent: {e}")

    # Merge name/description: last-write-wins by updated_at
    description_updated = False
    remote_updated_at = remote_event.get("updated_at")
    if remote_updated_at:
        try:
            remote_dt = datetime.fromisoformat(remote_updated_at.replace("Z", "+00:00"))
            local_dt = agent_info.updated_at
            if hasattr(local_dt, "tzinfo") and local_dt.tzinfo is None:
                local_dt = local_dt.replace(tzinfo=timezone.utc)
            if remote_dt > local_dt:
                remote_name = remote_event.get("title")
                remote_desc = remote_event.get("description")
                updates = {}
                if remote_name and remote_name != agent_info.name:
                    updates["name"] = remote_name
                if remote_desc is not None and remote_desc != agent_info.description:
                    updates["description"] = remote_desc
                if updates:
                    db.update_agent_info(agent_id, **updates)
                    description_updated = True
                    agent_info = db.get_agent_info(agent_id)
        except Exception as e:
            logger.warning(f"Failed to compare timestamps for name/desc merge: {e}")

    # 4. Build merged data and push
    _progress("Pushing merged data...")

    # Reload local state after merge
    local_sessions = db.get_sessions_by_agent_id(agent_id)
    local_content_hashes = db.get_agent_content_hashes(agent_id)

    # Count sessions pushed (local sessions with turns not in remote)
    sessions_pushed = 0
    for session in local_sessions:
        turns = db.get_turns_for_session(session.id)
        new_local_turns = [t for t in turns if t.content_hash not in remote_content_hashes]
        if new_local_turns:
            sessions_pushed += 1

    # Build full conversation data for push
    merged_conversation = _build_merged_conversation_data(
        agent_info=agent_info,
        agent_id=agent_id,
        sessions=local_sessions,
        db=db,
        contributor_token=agent_info.share_contributor_token,
    )

    # Push with optimistic locking + retry
    from .export_shares import _update_share_content

    new_version = remote_sync_version
    for attempt in range(MAX_SYNC_RETRIES):
        try:
            push_result = _update_share_content(
                backend_url=backend_url,
                share_id=share_id,
                token=token,
                conversation_data=merged_conversation,
                expected_version=new_version,
            )
            new_version = push_result.get("version", new_version + 1)
            break
        except Exception as e:
            error_str = str(e)
            if "409" in error_str and attempt < MAX_SYNC_RETRIES - 1:
                _progress(f"Version conflict, retrying ({attempt + 2}/{MAX_SYNC_RETRIES})...")
                # Re-pull and retry
                remote_data = _pull_remote(backend_url, share_id)
                if remote_data.get("success"):
                    conv = remote_data["data"]
                    new_version = conv.get("sync_metadata", {}).get("sync_version", 0)
                continue
            else:
                logger.error(f"Push failed after {attempt + 1} attempts: {e}")
                return {"success": False, "error": f"Push failed: {e}"}

    # 5. Update local sync metadata
    now_iso = datetime.now(timezone.utc).isoformat()
    db.update_agent_sync_metadata(
        agent_id,
        last_synced_at=now_iso,
        sync_version=new_version,
    )

    _progress("Sync complete!")

    return {
        "success": True,
        "sessions_pulled": sessions_pulled,
        "sessions_pushed": sessions_pushed,
        "description_updated": description_updated,
        "new_sync_version": new_version,
    }


def _pull_remote(backend_url: str, share_id: str) -> dict:
    """Pull remote share data via the download_share_data helper."""
    try:
        from .import_shares import download_share_data

        share_url = f"{backend_url}/share/{share_id}"
        return download_share_data(share_url, password=None)
    except Exception as e:
        return {"success": False, "error": str(e)}


def _build_merged_conversation_data(
    agent_info,
    agent_id: str,
    sessions,
    db,
    contributor_token: Optional[str] = None,
) -> dict:
    """
    Build a full conversation data dict from local agent state.

    Mirrors the structure of build_enhanced_conversation_data but works
    directly from DB records without ExportableSession wrappers.
    """
    import json as json_module

    event_data = {
        "event_id": f"agent-{agent_id}",
        "title": agent_info.name or "Agent Sessions",
        "description": agent_info.description or "",
        "event_type": "agent",
        "status": "active",
        "created_at": agent_info.created_at.isoformat() if agent_info.created_at else None,
        "updated_at": agent_info.updated_at.isoformat() if agent_info.updated_at else None,
    }

    sessions_data = []
    for session in sessions:
        turns = db.get_turns_for_session(session.id)
        turns_data = []
        for turn in turns:
            turn_content = db.get_turn_content(turn.id)
            messages = []
            if turn_content:
                for line in turn_content.strip().split("\n"):
                    if line.strip():
                        try:
                            messages.append(json_module.loads(line))
                        except Exception:
                            continue

            turns_data.append({
                "turn_id": turn.id,
                "turn_number": turn.turn_number,
                "content_hash": turn.content_hash,
                "timestamp": turn.timestamp.isoformat() if turn.timestamp else None,
                "llm_title": turn.llm_title or "",
                "llm_description": turn.llm_description,
                "user_message": turn.user_message,
                "assistant_summary": turn.assistant_summary,
                "model_name": turn.model_name,
                "git_commit_hash": turn.git_commit_hash,
                "messages": messages,
            })

        sessions_data.append({
            "session_id": session.id,
            "session_type": session.session_type or "unknown",
            "workspace_path": session.workspace_path,
            "session_title": session.session_title,
            "session_summary": session.session_summary,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
            "created_by": session.created_by,
            "shared_by": session.shared_by,
            "turns": turns_data,
        })

    username = os.environ.get("USER") or os.environ.get("USERNAME") or "anonymous"

    result = {
        "version": "2.1",
        "username": username,
        "time": datetime.now(timezone.utc).isoformat(),
        "event": event_data,
        "sessions": sessions_data,
        "ui_metadata": {
            "agent_name": agent_info.name,
        },
    }

    if contributor_token:
        result["sync_metadata"] = {
            "contributor_token": contributor_token,
            "sync_version": agent_info.sync_version or 0,
        }

    return result

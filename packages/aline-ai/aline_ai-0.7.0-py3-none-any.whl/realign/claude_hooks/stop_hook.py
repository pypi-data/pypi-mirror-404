#!/usr/bin/env python3
"""
Claude Code Stop Hook - 通知 watcher turn 已完成

当 Claude Code agent 完成响应时，此脚本被调用。
它会写入一个信号文件，让 watcher 立即检测到 turn 完成。

使用方式:
    此脚本通过 Claude Code 的 Stop hook 机制调用，
    接收 stdin JSON 和环境变量。

环境变量:
    CLAUDE_PROJECT_DIR - 项目根目录路径

stdin JSON 格式:
    {
        "session_id": "...",
        "transcript_path": "...",
        "cwd": "...",
        "hook_event_name": "Stop"
    }
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

try:
    from terminal_state import update_terminal_mapping  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    update_terminal_mapping = None


def get_signal_dir() -> Path:
    """获取信号文件目录"""
    signal_dir = Path.home() / ".aline" / ".signals"
    signal_dir.mkdir(parents=True, exist_ok=True)
    return signal_dir


def main():
    """主函数"""
    try:
        # 读取 stdin JSON
        stdin_data = sys.stdin.read()
        try:
            data = json.loads(stdin_data) if stdin_data.strip() else {}
        except json.JSONDecodeError:
            data = {}

        session = data.get("session") or {}
        session_id = session.get("id") or data.get("session_id") or data.get("sessionId") or ""
        transcript_path = (
            session.get("transcript_path")
            or data.get("transcript_path")
            or data.get("transcriptPath")
            or ""
        )
        cwd = data.get("cwd") or ""

        # From environment
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", cwd)
        terminal_id = os.environ.get("ALINE_TERMINAL_ID", "")
        inner_socket = os.environ.get("ALINE_INNER_TMUX_SOCKET", "")
        inner_session = os.environ.get("ALINE_INNER_TMUX_SESSION", "")
        agent_id = os.environ.get("ALINE_AGENT_ID", "")

        if not terminal_id:
            try:
                terminal_id = (
                    subprocess.run(
                        ["tmux", "display-message", "-p", "#{@aline_terminal_id}"],
                        text=True,
                        capture_output=True,
                        check=False,
                    ).stdout
                    or ""
                ).strip()
            except Exception:
                terminal_id = terminal_id

        # 如果没有 session_id，尝试从 transcript_path 提取
        if not session_id and transcript_path:
            # transcript_path 通常是 ~/.claude/projects/<project>/<session_id>.jsonl
            transcript_file = Path(transcript_path)
            if transcript_file.suffix == ".jsonl":
                session_id = transcript_file.stem

        # 如果仍然没有 session_id，生成一个临时的
        if not session_id:
            session_id = f"unknown_{int(time.time() * 1000)}"

        # 写入信号文件
        signal_dir = get_signal_dir()
        timestamp_ms = int(time.time() * 1000)
        signal_file = signal_dir / f"{session_id}_{timestamp_ms}.signal"
        tmp_file = signal_dir / f"{session_id}_{timestamp_ms}.signal.tmp"

        # Check for no-track mode
        no_track = os.environ.get("ALINE_NO_TRACK", "") == "1"

        signal_data = {
            "session_id": session_id,
            "terminal_id": terminal_id,
            "agent_id": agent_id,
            "project_dir": project_dir,
            "transcript_path": transcript_path,
            "cwd": cwd,
            "timestamp": time.time(),
            "hook_event": "Stop",
        }
        if no_track:
            signal_data["no_track"] = True

        # Write atomically to avoid watcher reading a partial JSON file.
        tmp_file.write_text(json.dumps(signal_data, indent=2))
        tmp_file.replace(signal_file)

        # Best-effort: tag the tmux "terminal tab" with the Claude session id.
        try:
            if terminal_id and inner_socket and inner_session and session_id:
                proc = subprocess.run(
                    [
                        "tmux",
                        "-L",
                        inner_socket,
                        "list-windows",
                        "-t",
                        inner_session,
                        "-F",
                        "#{window_id}\t#{@aline_terminal_id}",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                for line in (proc.stdout or "").splitlines():
                    parts = line.split("\t", 1)
                    if len(parts) != 2:
                        continue
                    window_id, win_terminal_id = parts
                    if win_terminal_id == terminal_id:
                        subprocess.run(
                            [
                                "tmux",
                                "-L",
                                inner_socket,
                                "set-option",
                                "-w",
                                "-t",
                                window_id,
                                "@aline_provider",
                                "claude",
                            ],
                            check=False,
                        )
                        subprocess.run(
                            [
                                "tmux",
                                "-L",
                                inner_socket,
                                "set-option",
                                "-w",
                                "-t",
                                window_id,
                                "@aline_session_type",
                                "claude",
                            ],
                            check=False,
                        )
                        subprocess.run(
                            [
                                "tmux",
                                "-L",
                                inner_socket,
                                "set-option",
                                "-w",
                                "-t",
                                window_id,
                                "@aline_session_id",
                                session_id,
                            ],
                            check=False,
                        )
                        # Set attention state to notify dashboard
                        subprocess.run(
                            [
                                "tmux",
                                "-L",
                                inner_socket,
                                "set-option",
                                "-w",
                                "-t",
                                window_id,
                                "@aline_attention",
                                "stop",
                            ],
                            check=False,
                        )
                        # Set no-track flag if applicable
                        if no_track:
                            subprocess.run(
                                [
                                    "tmux",
                                    "-L",
                                    inner_socket,
                                    "set-option",
                                    "-w",
                                    "-t",
                                    window_id,
                                    "@aline_no_track",
                                    "1",
                                ],
                                check=False,
                            )
                        if transcript_path:
                            subprocess.run(
                                [
                                    "tmux",
                                    "-L",
                                    inner_socket,
                                    "set-option",
                                    "-w",
                                    "-t",
                                    window_id,
                                    "@aline_transcript_path",
                                    transcript_path,
                                ],
                                check=False,
                            )
                        break
            elif session_id:
                window_id = (
                    subprocess.run(
                        ["tmux", "display-message", "-p", "#{window_id}"],
                        text=True,
                        capture_output=True,
                        check=False,
                    ).stdout
                    or ""
                ).strip()
                should_tag = bool(terminal_id)
                if not should_tag:
                    try:
                        context_id = (
                            subprocess.run(
                                ["tmux", "display-message", "-p", "#{@aline_context_id}"],
                                text=True,
                                capture_output=True,
                                check=False,
                            ).stdout
                            or ""
                        ).strip()
                        should_tag = bool(context_id)
                    except Exception:
                        should_tag = False

                if window_id and should_tag:
                    subprocess.run(
                        [
                            "tmux",
                            "set-option",
                            "-w",
                            "-t",
                            window_id,
                            "@aline_provider",
                            "claude",
                        ],
                        check=False,
                    )
                    subprocess.run(
                        [
                            "tmux",
                            "set-option",
                            "-w",
                            "-t",
                            window_id,
                            "@aline_session_type",
                            "claude",
                        ],
                        check=False,
                    )
                    subprocess.run(
                        [
                            "tmux",
                            "set-option",
                            "-w",
                            "-t",
                            window_id,
                            "@aline_session_id",
                            session_id,
                        ],
                        check=False,
                    )
                    # Set attention state to notify dashboard
                    subprocess.run(
                        [
                            "tmux",
                            "set-option",
                            "-w",
                            "-t",
                            window_id,
                            "@aline_attention",
                            "stop",
                        ],
                        check=False,
                    )
                    # Set no-track flag if applicable
                    if no_track:
                        subprocess.run(
                            [
                                "tmux",
                                "set-option",
                                "-w",
                                "-t",
                                window_id,
                                "@aline_no_track",
                                "1",
                            ],
                            check=False,
                        )
                    if transcript_path:
                        subprocess.run(
                            [
                                "tmux",
                                "set-option",
                                "-w",
                                "-t",
                                window_id,
                                "@aline_transcript_path",
                                transcript_path,
                            ],
                            check=False,
                        )
        except Exception:
            pass

        # Best-effort: persist mapping to ~/.aline/terminal.json to survive tmux restarts.
        try:
            if update_terminal_mapping and terminal_id and session_id:
                update_terminal_mapping(
                    terminal_id=terminal_id,
                    provider="claude",
                    session_type="claude",
                    session_id=session_id,
                    transcript_path=transcript_path,
                    cwd=cwd,
                    project_dir=project_dir,
                    source="Stop",
                    agent_id=agent_id if agent_id else None,
                )
        except Exception:
            pass

        # 可选：输出调试信息到 stderr（不会显示给用户）
        # print(f"[Aline Stop Hook] Signal written: {signal_file.name}", file=sys.stderr)

        # Exit 0 表示成功，不阻止 Claude 停止
        sys.exit(0)

    except Exception as e:
        # 出错时静默失败，不影响 Claude Code 的正常运行
        # print(f"[Aline Stop Hook] Error: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()

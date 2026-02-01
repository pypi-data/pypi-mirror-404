"""ReAlign init command - Initialize ReAlign tracking system."""

import shutil
import sys
from typing import Annotated, Any, Dict, Optional, Tuple
from pathlib import Path
import re
import typer
from rich.console import Console

from ..config import (
    ReAlignConfig,
    get_default_config_content,
    generate_random_username,
)

console = Console()


# tmux config template for Aline-managed dashboard sessions.
# Stored at ~/.aline/tmux/tmux.conf and sourced by the dashboard tmux bootstrap.
# Bump this version when the tmux config changes to trigger auto-update on `aline init`.
_TMUX_CONFIG_VERSION = 8


def _get_tmux_config() -> str:
    """Generate tmux config with Type-to-Exit bindings."""
    conf = f"# Aline tmux config (v{_TMUX_CONFIG_VERSION})\n"
    conf += r"""#
# Goal: make mouse selection copy to the system clipboard (macOS Terminal friendly).
# - Drag-select text with the mouse; when you release, it is copied to the clipboard.
# - Paste anywhere with Cmd+V.
#
# Note: Cmd+C inside tmux is still SIGINT (Terminal behavior).

set -g mouse on

# Pane border styling - use double lines for wider, more visible borders (tmux 3.2+).
# This helps users identify the resizable border area more easily.
set -g pane-border-lines double
set -g pane-border-style "fg=brightblack"
set -g pane-active-border-style "fg=blue"

# Add a small indicator showing where the border is (tmux 3.2+).
# This creates a visual "dead zone" that's more obvious for resizing.
set -g pane-border-indicators arrows

# Disable paste-time detection so key bindings work during paste.
set -g assume-paste-time 0

# Fast escape time so ESC is processed immediately (helps with paste detection).
set -s escape-time 0

# Better scrolling: enter copy-mode with -e so scrolling to bottom exits it.
bind-key -n WheelUpPane if-shell -F -t = "#{mouse_any_flag}" "send-keys -M" "if -Ft= '#{pane_in_mode}' 'send-keys -M' 'copy-mode -e -t ='"

# macOS clipboard: copy selection to clipboard when drag ends.
# Use copy-pipe-no-clear to preserve selection highlight after copying.
bind -T copy-mode-vi MouseDragEnd1Pane send -X copy-pipe-no-clear "pbcopy"
bind -T copy-mode    MouseDragEnd1Pane send -X copy-pipe-no-clear "pbcopy"

# MouseDrag1Pane: Clear old selection and start new one when dragging begins.
# This ensures selection only clears when starting a NEW drag, not on click.
bind -T copy-mode-vi MouseDrag1Pane select-pane \; send -X clear-selection \; send -X begin-selection
bind -T copy-mode    MouseDrag1Pane select-pane \; send -X clear-selection \; send -X begin-selection

# MouseDown1Pane: Click clears selection but stays in copy-mode (no scroll).
# To exit copy-mode: scroll to bottom (auto-exit) or press q/Escape.
bind -T copy-mode-vi MouseDown1Pane select-pane \; send -X clear-selection
bind -T copy-mode    MouseDown1Pane select-pane \; send -X clear-selection

# Escape key: exit copy-mode (also use this before Cmd+V paste in copy-mode).
bind -T copy-mode-vi Escape send -X cancel
bind -T copy-mode    Escape send -X cancel

# Type-to-Exit: Typing any alphanumeric character exits copy-mode and sends the key.
"""
    def _tmux_quote(value: str) -> str:
        # tmux config treats `#` as a comment delimiter; quote args so keys like `#` don't disappear.
        # Note: `~` is special in tmux config parsing; use an escaped form instead of quotes.
        if value == "~":
            return r"\~"
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def _bind_cancel_and_send(key: str) -> str:
        key_token = _tmux_quote(key)
        return (
            f"bind -T copy-mode-vi {key_token} send -X cancel \\; send-keys -- {key_token}\n"
            f"bind -T copy-mode    {key_token} send -X cancel \\; send-keys -- {key_token}\n"
        )

    # Generate bindings for common characters.
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.@/!#$%^&*()+=,<>?[]{}|~`;\\\"'"
    for c in chars:
        conf += _bind_cancel_and_send(c)

    # Space: use tmux key name.
    conf += "bind -T copy-mode-vi Space send -X cancel \\; send-keys Space\n"
    conf += "bind -T copy-mode    Space send -X cancel \\; send-keys Space\n"

    # Cmd+V (paste): exit copy-mode when paste is detected.
    # Different terminals handle Cmd+V differently:
    # - Some send M-v (Meta+V)
    # - Some use bracketed paste mode and send the content directly
    # Since we bind all printable chars above, pasting text starting with a letter/number will exit.
    # For other cases, bind Enter to also exit (multiline paste often starts with newline).
    conf += "bind -T copy-mode-vi M-v send -X cancel \\; run 'sleep 0.05' \\; send-keys M-v\n"
    conf += "bind -T copy-mode    M-v send -X cancel \\; run 'sleep 0.05' \\; send-keys M-v\n"

    return conf


_TMUX_CONF_REPAIR_TILDE_KEY_RE = re.compile(
    r'^(bind(?:-key)?\s+-T\s+copy-mode(?:-vi)?\s+)(?:"~"|~)(\s+send\s+-X\s+cancel\s+\\;\s+send-keys\s+)(?:"~"|~)\s*$',
    re.MULTILINE,
)

_TMUX_CONF_REPAIR_KEY_NEEDS_QUOTE_RE = re.compile(
    r"^(bind(?:-key)?\s+-T\s+copy-mode(?:-vi)?\s+)([#{}])(\s+send\s+-X\s+cancel\s+\\;\s+send-keys\s+)\2\s*$",
    re.MULTILINE,
)

_TMUX_CONF_REPAIR_SEND_KEYS_DASHDASH_RE = re.compile(
    r"^(bind(?:-key)?\s+-T\s+copy-mode(?:-vi)?\s+.+\s+send\s+-X\s+cancel\s+\\;\s+send-keys\s+)(?!--\s)(.+)$",
    re.MULTILINE,
)


# Prompt templates for ~/.aline/prompts/
PROMPT_README = """# Custom Prompts for ReAlign

This directory allows you to customize the LLM prompts used by ReAlign for various summarization and classification tasks.

## Usage

1. Copy the example files and remove the `.example` extension:
   ```bash
   cp metadata.md.example metadata.md
   cp commit_message.md.example commit_message.md
   cp session_summary.md.example session_summary.md
   cp event_summary.md.example event_summary.md
   cp share_ui_metadata.md.example share_ui_metadata.md
   ```

2. Edit the `.md` files to customize the prompts according to your needs

3. ReAlign will automatically use your custom prompts when they exist

## Available Prompts

### Turn-Level (Git Hooks)
- **metadata.md** - Classifies task metadata (if_last_task, satisfaction) for each turn
- **commit_message.md** - Generates commit messages (title + description) for each turn

### Session-Level (Watcher)
- **session_summary.md** - Generates session title and summary from multiple turns

### Event-Level (Watcher)
- **event_summary.md** - Generates event title and description from multiple sessions

### Share Export (aline share export)
- **share_ui_metadata.md** - Generates preset questions and Slack message for shared conversations

## Prompt Hierarchy

```
Event (highest level)
  ├── Event Summary (event_summary.md)
  ├── Share UI Metadata (share_ui_metadata.md) - for sharing
  │
  ├── Session 1
  │   ├── Session Summary (session_summary.md)
  │   ├── Turn 1 (commit message + metadata)
  │   ├── Turn 2 (commit message + metadata)
  │   └── ...
  ├── Session 2
  │   └── ...
  └── ...
```

## Fallback Behavior

If custom prompts are not found or fail to load, ReAlign will fall back to:
1. Built-in prompts from `tools/commit_message_prompts/` (if they exist)
2. Hardcoded default prompts

## Tips

- Keep prompts concise and focused on their specific task
- Test your custom prompts with real sessions to ensure they work well
- You can temporarily rename a custom prompt to disable it (e.g., `metadata.md.bak`)
- Review generated outputs in logs: `~/.aline/.logs/hooks.log` and `~/.aline/.logs/watcher.log`
"""

PROMPT_METADATA_EXAMPLE = """You are a metadata classifier for AI-assisted git commits.

Each prompt only provides three pieces of context:
1. The previous commit's summary title (or `(none)` if unavailable)
2. The user's latest request text
3. The current commit's summary title generated by the LLM

Using only those, decide:
- `if_last_task`: `"yes"` if the user is continuing or referring to the same task as the previous request; `"no"` if the user is starting a new, different task.
- `satisfaction`: `"good"` if the user appears satisfied, successful, or is naturally moving on; `"fine"`  if progress is partial, mixed, `"bad"` if the user reports failure, progress stuck, or dissatisfaction.

Return only these two fields, with no explanations or extra text.

Guidelines:
- Rely on the user's latest wording to gauge satisfaction.
- Compare the current vs. previous titles, and the user request to detect continuity.
- If signals are unclear, default to `"yes"` and `"bad"`.

Return STRICT JSON with exactly these fields:
```json
{
  "if_last_task": "yes|no",
  "satisfaction": "good|fine|bad"
}
```

Continuity rules (`if_last_task`):
- `"yes"` when the user is following up on the previous change (e.g., "still broken", "fix that again", "continue …").
- `"no"` when the user requests an new feature/change.

Satisfaction rules:
- `"bad"` for strong negatives: "no", "nothing changed", "still…", "doesn't work", "broken", "failed", etc.
- `"fine"` for mixed/partial feedback: "better, but…", "almost…".
- `"good"` for positive/complete signals: "great", "works", "perfect", "cool", or when shifting to a new task without complaints.

Respond with JSON only—no explanations or extra text.
"""

PROMPT_COMMIT_MESSAGE_EXAMPLE = """You are a progress record generator.

Your job is to use all previous records and turn this turn's agent work into a follow-up progress record that continues from what has already been written, instead of starting a new, standalone record.

Each record should read like one more sentence or paragraph added to an ongoing note, not a fresh entry. Write as if the reader has already read all previous records. Do not repeat wording, structure, or phrasing used before. Focus only on what is new, different, or newly discovered in this turn

Follow this order:
\t1.\tStart with the agent's understanding of the user's request based on the previous records.
\t2.\tAdd only the new information introduced this turn
\t3.\tEnd with what the agent did this time
  4.  Do not write generic outcome claims such as "now it's properly implemented" or "it fits user expectations." Ending with factual details of what the agent did is enough.


Critical rule (this is the core)
\t•\tReject all fluff. Describe only concrete facts. The shorter the better. Maximize signal-to-noise. Keep the language sharp and focused.
\t•\tBased on the given previous records, write the follow-up record as if you are adding one more line to the existing records

Input will include:
\t•\tUser requests
\t•\tThis turns' agent thinking process and response.
\t• The last 5 records (record from earlier turns)
Treat previous records as already said.

Generate ONLY the structured summary (metadata is handled separately). Respond with JSON:
{
  "record": "A follow-up progress record. Typically 50–100 words, but fewer words are acceptable if sufficient."
}

Examples:
{
  "record": "The user was unhappy with current unified metadata system, so a New Implementation of metadata system (Two-Stage Approach) is implemented:
  Stage 1: Generate title + description (focused on what happened)
  Stage 2: Separate metadata classification with minimal context:
  - Previous commit title
  - User request
  - Current commit title."
}

{
  "record": "The user still cannot see the layout. The agent found the issue:
  1. Line 1047 had a hardcoded instruction \\"Return JSON with exactly two fields: title and description\\" that overrode your default.md prompt
  2. Lines 1062-1065 only parsed title and description, not the new record field

  the agent fixed both issues and added backwards compatibility so it can handle both formats."
}

{
  "record": "The user asked to revert back to the last commit. now done it."
}


Return JSON only, no other text.
"""

PROMPT_SESSION_SUMMARY_EXAMPLE = """You are summarizing a coding session that contains multiple conversation turns.

Your task:
1. Generate a concise SESSION TITLE (max 80 characters) that captures the main goal or theme of the entire session.
2. Generate a SESSION SUMMARY (2-5 sentences) that describes what was accomplished across all turns.

Output in English.

Output STRICT JSON only with this schema (no extra text, no markdown):
{
  "session_title": "string (max 80 chars)",
  "session_summary": "string (2-5 sentences)"
}

Rules:
- The title should be concise and descriptive, capturing the overall goal.
- The summary should highlight key accomplishments, not just list each turn.
- If the session involves multiple unrelated tasks, focus on the most significant ones.
- Prefer action-oriented language (e.g., "Implement X", "Fix Y", "Refactor Z").
"""

PROMPT_EVENT_SUMMARY_EXAMPLE = """You are summarizing a development event that spans multiple coding sessions.

Your task:
1. Generate a concise EVENT TITLE (max 100 characters) that captures the main goal or theme across all sessions.
2. Generate an EVENT DESCRIPTION (3-6 sentences) that synthesizes what was accomplished across all sessions.

Output in English.

Output STRICT JSON only with this schema (no extra text, no markdown):
{
  "event_title": "string (max 100 chars)",
  "event_description": "string (3-6 sentences)"
}

Rules:
- The title should be high-level and describe the overall objective or feature.
- The description should highlight key accomplishments, not just list each session.
- Focus on the outcome and impact, not the process.
- Use action-oriented language (e.g., "Implemented X", "Refactored Y", "Fixed Z").
"""

PROMPT_SHARE_UI_METADATA_EXAMPLE = """You are a conversation interface copy generator for a general-purpose conversation assistant.

Your task is to analyze a given conversation history (with title and description provided) and generate
personalized content for sharing and exploring that conversation.

The conversation title and description are already provided. You only need to generate:
1. Four preset questions
2. A Slack share message

Return the result strictly in JSON format:

{
  "preset_questions": [
    "Question 1: About high-level summary (15–30 characters)",
    "Question 2: About technical or implementation details (15–30 characters)",
    "Question 3: About decision-making or reasoning (15–30 characters)",
    "Question 4: About results, impact, or follow-up (15–30 characters)"
  ],

  "slack_message": "A friendly, casual Slack message sharing your work update with the team.

                    Style Guidelines:
                    - Tone: Casual, friendly, conversational (like chatting with teammates)
                    - Length: 3-8 sentences depending on conversation complexity
                    - Emoji: Use 1-3 relevant emojis to add personality (don't overdo it)
                    - Technical depth: Mention key technologies but avoid unnecessary jargon
                    - Clarity: Team members should understand the impact without deep technical knowledge

                    Content Structure:
                    1. Start with context - Give an overview of what you've been working on
                    2. Highlight accomplishments - What did you achieve? (use casual language)
                    3. Mention key details - Important technical decisions or challenges overcome
                    4. End with status/next steps - What's the current state or what's coming next?

                    Example Good Messages:
                    - '🎉 Just wrapped up the session summary feature! Built a new command that automatically generates event summaries from recent commits - both short emotional messages and detailed reports. Had to fix a bunch of commit parsing quirks along the way, but it\\\\'s solid now. Next up: testing the UI expand/collapse to make sure everything feels smooth.'
                    - '🚀 Big update, team! Been cranking on several fronts: First, got the vertical split terminal feature live - you can now split, resize, and close terminal panes as needed. Also revamped the onboarding flow and share dialog to be more compact and user-friendly. Fixed a bunch of UI quirks along the way. Next up: making sure multi-event sharing works seamlessly! 💪'

                    Bad Examples to Avoid:
                    - Too formal: 'I have successfully completed the implementation...'
                    - Too technical: 'Implemented event summarization via LLM-driven clustering...'"
}

Requirements:
1. Preset questions must be based on the actual conversation content, concrete, and useful from the specified angles.
2. The Slack message should be casual, friendly, and share your work progress like you're updating teammates.
3. All text must be in English or Chinese, depending on the conversation language.
4. Output JSON only. Do not include any additional explanation or text.
"""

PROMPT_SLACK_SHARE_REVISE_EXAMPLE = """You are helping revise a Slack message about a development session/event.

You will receive:
1. The original event summary
2. The previously generated Slack message
3. User's revision instructions

Your task is to revise the Slack message according to the user's instructions while maintaining the casual, team-friendly tone and keeping the original event context in mind.

## Guidelines

1. **Follow the user's revision instructions** - This is the primary goal
2. **Maintain context** - Keep the revision aligned with the original event summary
3. **Preserve tone** - Keep the casual, approachable style unless instructed otherwise
4. **Keep it concise** - Maintain 3-6 sentences unless the user requests a different length
5. **Use emojis appropriately** - 1-2 emojis, not excessive

## Output Format

Return ONLY a JSON object with this structure:
```json
{
  "message": "The revised Slack message text here"
}
```

## Example

**Original Event Summary:**
```
Title: Bug Fix Session
Description: Fixed authentication timeout issues
Tags: bug-fix, authentication
Commits: 3
```

**Previous Message:**
```
🔧 Just wrapped up fixing those pesky auth timeout issues! Turns out the session tokens were expiring too quickly. Made 3 commits to adjust the timeout logic and add better error handling. Everything's solid now - users should have a much smoother login experience.
```

**Revision Request:**
```
Make it shorter and mention that we also added tests
```

**Expected Output:**
```json
{
  "message": "🔧 Fixed auth timeout issues - tokens were expiring too quickly. Added timeout logic fixes and test coverage in 3 commits. Users should see smoother logins now!"
}
```

Remember: Focus on what the user wants changed while keeping the message grounded in the original event context.
"""


def _initialize_prompts_directory() -> None:
    """
    Initialize ~/.aline/prompts/ directory with example prompt files.

    Creates the prompts directory and example files if they don't exist.
    Does not overwrite existing files.
    """
    prompts_dir = Path.home() / ".aline" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    # Define all prompt files
    prompt_files = {
        "README.md": PROMPT_README,
        "metadata.md.example": PROMPT_METADATA_EXAMPLE,
        "commit_message.md.example": PROMPT_COMMIT_MESSAGE_EXAMPLE,
        "session_summary.md.example": PROMPT_SESSION_SUMMARY_EXAMPLE,
        "event_summary.md.example": PROMPT_EVENT_SUMMARY_EXAMPLE,
        "share_ui_metadata.md.example": PROMPT_SHARE_UI_METADATA_EXAMPLE,
        "slack_share_revise.md.example": PROMPT_SLACK_SHARE_REVISE_EXAMPLE,
    }

    # Create files if they don't exist
    for filename, content in prompt_files.items():
        file_path = prompts_dir / filename
        if not file_path.exists():
            file_path.write_text(content, encoding="utf-8")


def _get_tmux_config_version(content: str) -> int:
    """Extract version number from tmux config content. Returns 0 if not found."""
    # Look for "# Aline tmux config (vN)" pattern
    match = re.search(r"# Aline tmux config \(v(\d+)\)", content)
    if match:
        return int(match.group(1))
    # Old configs without version marker are version 1
    if "# Aline tmux config" in content:
        return 1
    return 0


def _initialize_tmux_config() -> Path:
    """Initialize ~/.aline/tmux/tmux.conf with auto-update on version change."""
    tmux_conf_path = Path.home() / ".aline" / "tmux" / "tmux.conf"
    tmux_conf_path.parent.mkdir(parents=True, exist_ok=True)

    if not tmux_conf_path.exists():
        tmux_conf_path.write_text(_get_tmux_config(), encoding="utf-8")
        return tmux_conf_path

    # Check existing config
    try:
        existing = tmux_conf_path.read_text(encoding="utf-8")
    except Exception:
        return tmux_conf_path

    # Only manage Aline-generated configs
    if "# Aline tmux config" not in existing:
        return tmux_conf_path

    # Check version and update if outdated
    existing_version = _get_tmux_config_version(existing)
    if existing_version < _TMUX_CONFIG_VERSION:
        # Auto-update to latest config
        tmux_conf_path.write_text(_get_tmux_config(), encoding="utf-8")
        return tmux_conf_path

    # Best-effort repair for older Aline-generated configs that used unquoted `#` keys.
    # tmux parses `#` as a comment delimiter, turning `bind ... # ...` into `bind ...` (invalid).
    repaired = existing
    repaired = _TMUX_CONF_REPAIR_TILDE_KEY_RE.sub(r"\1\\~\2\\~", repaired)
    repaired = _TMUX_CONF_REPAIR_KEY_NEEDS_QUOTE_RE.sub(r'\1"\2"\3"\2"', repaired)
    repaired = _TMUX_CONF_REPAIR_SEND_KEYS_DASHDASH_RE.sub(r"\1-- \2", repaired)
    if repaired != existing:
        tmux_conf_path.write_text(repaired, encoding="utf-8")
    return tmux_conf_path


def _detect_existing_global_state() -> Tuple[bool, bool]:
    """
    Detect whether global config and DB existed *before* `aline init`.

    Returns:
        (config_existed, db_existed)
    """
    config_path = Path.home() / ".aline" / "config.yaml"
    config_existed = config_path.exists()

    # Best-effort: determine DB path without requiring config to exist.
    try:
        if config_existed:
            db_path = Path(ReAlignConfig.load(config_path).sqlite_db_path).expanduser()
        else:
            db_path = Path(ReAlignConfig().sqlite_db_path).expanduser()
    except Exception:
        db_path = Path(ReAlignConfig().sqlite_db_path).expanduser()

    return config_existed, db_path.exists()


def _should_start_watcher(
    start_watcher: Optional[bool],
    *,
    config_existed: bool,
    db_existed: bool,
) -> bool:
    """
    Decide whether `aline init` should start the watcher.

    Default behavior (start_watcher=None):
      - Auto-start only on first init (when config/db didn't exist yet)
    """
    if start_watcher is not None:
        return bool(start_watcher)
    return (not config_existed) or (not db_existed)


def _initialize_skills() -> Path:
    """Initialize Claude Code skills (best-effort, no overwrite).

    Returns:
        Path to the skills root directory
    """
    from .add import add_skills_command

    add_skills_command(force=False)
    return Path.home() / ".claude" / "skills"


def _initialize_claude_hooks() -> Tuple[bool, list]:
    """Initialize Claude Code hooks (Stop, UserPromptSubmit, PermissionRequest).

    Installs all Aline hooks to the global Claude Code settings.
    Does not overwrite existing hooks.

    Returns:
        (all_success, list of installed hook names)
    """
    installed_hooks = []
    all_success = True

    try:
        from ..claude_hooks.stop_hook_installer import ensure_stop_hook_installed

        if ensure_stop_hook_installed(quiet=True):
            installed_hooks.append("Stop")
        else:
            all_success = False
    except Exception:
        all_success = False

    try:
        from ..claude_hooks.user_prompt_submit_hook_installer import (
            ensure_user_prompt_submit_hook_installed,
        )

        if ensure_user_prompt_submit_hook_installed(quiet=True):
            installed_hooks.append("UserPromptSubmit")
        else:
            all_success = False
    except Exception:
        all_success = False

    try:
        from ..claude_hooks.permission_request_hook_installer import (
            ensure_permission_request_hook_installed,
        )

        if ensure_permission_request_hook_installed(quiet=True):
            installed_hooks.append("PermissionRequest")
        else:
            all_success = False
    except Exception:
        all_success = False

    return all_success, installed_hooks


def init_global(
    force: bool = False,
) -> Dict[str, Any]:
    """
    Core global initialization logic (non-interactive).

    Args:
        force: Overwrite the global config with defaults

    Returns:
        Dictionary with initialization results and metadata
    """
    result = {
        "success": False,
        "config_path": None,
        "db_path": None,
        "prompts_dir": None,
        "tmux_conf": None,
        "skills_path": None,
        "hooks_installed": None,
        "message": "",
        "errors": [],
    }

    try:
        # Initialize global config if not exists
        global_config_path = Path.home() / ".aline" / "config.yaml"
        if force or not global_config_path.exists():
            global_config_path.parent.mkdir(parents=True, exist_ok=True)
            global_config_path.write_text(
                get_default_config_content(), encoding="utf-8"
            )
        result["config_path"] = str(global_config_path)

        # Load config
        config = ReAlignConfig.load()

        # User identity setup (V17: uid from Supabase login)
        if not config.uid:
            console.print("\n[bold blue]═══ User Identity Setup ═══[/bold blue]")
            console.print(
                "Aline requires login for user identification.\n"
            )
            console.print(
                "[yellow]Run 'aline login' to authenticate with your account.[/yellow]\n"
            )
            # If user_name is also not set, generate a temporary one
            if not config.user_name:
                config.user_name = generate_random_username()
                config.save()
                console.print(
                    f"Auto-generated username: [yellow]{config.user_name}[/yellow] (will update on login)\n"
                )

        # Initialize database
        db_path = Path(config.sqlite_db_path).expanduser()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        result["db_path"] = str(db_path)

        # Create/upgrade database schema
        from ..db.sqlite_db import SQLiteDatabase

        db = SQLiteDatabase(str(db_path))
        db.initialize()
        db.close()

        # Initialize prompts directory with example files
        _initialize_prompts_directory()
        prompts_dir = Path.home() / ".aline" / "prompts"
        result["prompts_dir"] = str(prompts_dir)

        tmux_conf = _initialize_tmux_config()
        result["tmux_conf"] = str(tmux_conf)

        # Initialize Claude Code skills
        skills_path = _initialize_skills()
        result["skills_path"] = str(skills_path)

        # Initialize Claude Code hooks (Stop, UserPromptSubmit, PermissionRequest)
        hooks_success, hooks_installed = _initialize_claude_hooks()
        result["hooks_installed"] = hooks_installed
        if not hooks_success:
            result["errors"].append("Some Claude Code hooks failed to install")

        result["success"] = True
        result["message"] = (
            "Aline initialized successfully (global config + database + prompts + tmux + skills + hooks ready)"
        )

    except Exception as e:
        result["errors"].append(f"Initialization failed: {e}")
        result["message"] = f"Failed to initialize: {e}"

    return result


def init_command(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite global config with defaults"),
    doctor: Annotated[
        bool,
        typer.Option(
            "--doctor/--no-doctor",
            help="Run 'aline doctor' after init (best for upgrades)",
        ),
    ] = False,
    install_tmux: Annotated[
        bool,
        typer.Option(
            "--install-tmux/--no-install-tmux",
            help="Auto-install tmux via Homebrew if missing (macOS only)",
        ),
    ] = True,
    start_watcher: Optional[bool] = typer.Option(
        None,
        "--start-watcher/--no-start-watcher",
        help="Start watcher daemon after init (default: auto on first init)",
    ),
):
    """Initialize Aline global config and SQLite database.

    Initializes the global config/database (in `~/.aline/`). Project/workspace context
    is inferred automatically when sessions are imported/processed.
    """
    config_existed, db_existed = _detect_existing_global_state()

    result = init_global(
        force=force,
    )

    # First-time UX: tmux is required for the default dashboard experience (tmux mode).
    # Only attempt on macOS; on other platforms, leave it to user.
    if (
        result.get("success")
        and install_tmux
        and result.get("tmux_conf")
        and sys.platform == "darwin"
        and shutil.which("tmux") is None
    ):
        console.print("\n[bold]tmux not found. Installing via Homebrew...[/bold]")
        try:
            from . import add as add_cmd

            rc = add_cmd.add_tmux_command(install_brew=True)
            if rc != 0:
                result["errors"] = (result.get("errors") or []) + [
                    "tmux install failed (required for the default tmux dashboard)",
                    "Tip: set ALINE_TERMINAL_MODE=native to run without tmux",
                ]
        except Exception as e:
            result["errors"] = (result.get("errors") or []) + [
                f"tmux install failed: {e}",
                "Tip: set ALINE_TERMINAL_MODE=native to run without tmux",
            ]

    if doctor and result.get("success"):
        # Run doctor in "safe" mode: restart only if already running, and keep init fast.
        try:
            from . import doctor as doctor_cmd

            restart_daemons = start_watcher is not False
            doctor_exit = doctor_cmd.run_doctor(
                restart_daemons=restart_daemons,
                start_if_not_running=False,
                verbose=False,
                clear_cache=False,
            )
            if doctor_exit != 0:
                result["success"] = False
                result["errors"] = (result.get("errors") or []) + [
                    "aline doctor failed (see output above)"
                ]
                result["message"] = f"{result.get('message', '').strip()} (doctor failed)".strip()
        except Exception as e:
            result["success"] = False
            result["errors"] = (result.get("errors") or []) + [f"aline doctor failed: {e}"]
            result["message"] = f"{result.get('message', '').strip()} (doctor failed)".strip()

    watcher_started: Optional[bool] = None
    watcher_start_exit: Optional[int] = None
    worker_started: Optional[bool] = None
    worker_start_exit: Optional[int] = None
    should_start = False

    if result.get("success"):
        should_start = _should_start_watcher(
            start_watcher,
            config_existed=config_existed,
            db_existed=db_existed,
        )
        if should_start:
            try:
                from . import watcher as watcher_cmd

                watcher_start_exit = watcher_cmd.watcher_start_command()
                watcher_started = watcher_start_exit == 0
            except Exception:
                watcher_started = False
                watcher_start_exit = 1

            # Start worker daemon alongside watcher (durable job queue consumer).
            try:
                from . import worker as worker_cmd

                worker_start_exit = worker_cmd.worker_start_command()
                worker_started = worker_start_exit == 0
            except Exception:
                worker_started = False
                worker_start_exit = 1

    # Print detailed results
    console.print("\n[bold blue]═══ Aline Initialization ═══[/bold blue]\n")

    if result["success"]:
        console.print("[bold green]✓ Status: SUCCESS[/bold green]\n")
    else:
        console.print("[bold red]✗ Status: FAILED[/bold red]\n")

    # Print all parameters and results
    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Config: [cyan]{result.get('config_path', 'N/A')}[/cyan]")
    console.print(f"  Database: [cyan]{result.get('db_path', 'N/A')}[/cyan]")
    console.print(f"  Prompts: [cyan]{result.get('prompts_dir', 'N/A')}[/cyan]")
    console.print(f"  Tmux: [cyan]{result.get('tmux_conf', 'N/A')}[/cyan]")
    console.print(f"  Skills: [cyan]{result.get('skills_path', 'N/A')}[/cyan]")

    hooks_installed = result.get("hooks_installed") or []
    if hooks_installed:
        console.print(f"  Hooks: [cyan]{', '.join(hooks_installed)}[/cyan]")
    else:
        console.print("  Hooks: [yellow]None installed[/yellow]")

    if result.get("success") and should_start:
        console.print("\n[bold]Watcher:[/bold]")
        if watcher_started:
            console.print("  Status: [green]STARTED[/green]")
            console.print("  Check: [cyan]aline watcher status[/cyan]", style="dim")
        else:
            console.print("  Status: [red]FAILED TO START[/red]")
            console.print("  Try: [cyan]aline watcher start[/cyan]", style="dim")
            console.print(
                "  Logs: [cyan]~/.aline/.logs/watcher_*.log[/cyan]", style="dim"
            )

        console.print("\n[bold]Worker:[/bold]")
        if worker_started:
            console.print("  Status: [green]STARTED[/green]")
            console.print("  Check: [cyan]aline worker status[/cyan]", style="dim")
        else:
            console.print("  Status: [red]FAILED TO START[/red]")
            console.print("  Try: [cyan]aline worker start[/cyan]", style="dim")
            console.print(
                "  Logs: [cyan]~/.aline/.logs/worker_*.log[/cyan]", style="dim"
            )

    if result.get("errors"):
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result["errors"]:
            console.print(f"  • {error}", style="red")

    console.print(f"\n[bold]Result:[/bold] {result['message']}\n")

    if result["success"]:
        console.print("[bold]Next steps:[/bold]")
        console.print(
            "  1. Start Claude Code or Codex - sessions are tracked automatically",
            style="dim",
        )
        console.print(
            "  2. Search history with: [cyan]aline search <query>[/cyan]", style="dim"
        )
        console.print(
            "  3. Customize prompts (optional): [cyan]~/.aline/prompts/[/cyan]",
            style="dim",
        )

        # If the user explicitly asked to start the watcher, failing to do so should fail init too.
        if start_watcher is True and watcher_start_exit not in (0, None):
            raise typer.Exit(1)
    else:
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(init_command)

"""Install optional local tooling for Aline."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()

# Aline skill definition for Claude Code
# Installed to ~/.claude/skills/aline/SKILL.md
ALINE_SKILL_MD = """---
name: aline
description: Search for past conversations, discussions, events, and code changes in Aline history. Use this when user asks about existing objects (function, feature, variable), debug with some issues, find related information about certain objects that maybe existed in the past chat, or wants to explore project deeply. Uses a "Broad to Deep" exploration path (Event -> Session -> Turn -> Content).
---

# Aline Skill

This skill provides unified search across your project's Aline history, optimized for AI agents to navigate and explore context efficiently.

## Core Philosophy: Broad to Deep Exploration

Aline search is designed as a **navigation map**, not just a keyword matcher. Follow this hierarchical path to understand history:

1.  **Event** (`-t event`): High-level activity groupings (e.g., "Feature X development").
2.  **Session** (`-t session`): Specific tool-usage sessions (e.g., "Bug fix session for X").
3.  **Turn** (`-t turn`): Individual assistant/user exchanges (Summaries/Titles).
4.  **Content** (`-t content`): The "source of truth" - full raw dialogue JSONL.

## Usage Strategy

### 1. Default Mode: Regex (Grep-style)
`aline search` **defaults to regex mode** (`-E`). It replaces `grep` for all history searches.

```bash
# Broad pattern matching (Default Regex)
aline search "sqlite.*migration"

# Targeted type search (all = event + session + turn)
aline search "refactor" -t session
```

### 2. The "Content" Barrier
The default `all` type **does NOT search `content`** (raw dialogue) because it can be slow.
- Use `-t content` explicitly when you need to find code snippets or specific tool call details.

### 3. Navigation via IDs & Prefixes
Use the ID prefixes found in search results to narrow down your next command. All filter flags support **short ID prefixes**.

```bash
# Search only within a specific session (prefix supported)
aline search "error" -s abc123de

# Deep dive into raw content for a specific turn
aline search -t content "api_key" --turns t789
```

## When to Use This Skill

Invoke this skill when the user asks to:
- Find when a feature was discussed or implemented
- Research the history of a component or decision
- Research "why" a specific code change happened.
- Locate previous implementations or feature discussions.
- Perform pattern matching across history (replacing `grep`).

## Exploration Workflow for Agents

1.  **Step 1: Broad Search** (`aline search "<query>"`): Locate the general area of interest.
2.  **Step 2: Narrow Scope** (`aline search -s <prefix> -t turn`): Zoom into a specific session's turn summaries.
3.  **Step 3: Deep Dive** (`aline search -t content --turns <turn_id>` or `aline watcher session show <session_id>`): Read the actual dialogue and technical details.
4.  **Step 4: Event Context**: If an event is identified, use `aline watcher event show <event_id>` to see all related sessions.

## Command Reference

| Command | Use For |
|---------|---------|
| `aline search "pattern"` | **Regex search (default)** across events, turns, sessions |
| `aline search "query" --no-regex` | Exact keyword matching |
| `aline search -t content "pattern"`| **Deep search** in raw dialogue history |
| `aline search -s <id>` | Filter results to specific sessions |
| `aline search -e <id>` | Filter results to sessions within specific events |

## Important Notes

- **Case Sensitivity**: Default is **insensitive**.
- **ID Prefixes**: You only need the first 8-12 characters of an ID (e.g., `abc12`) for filtering.
- **Next Steps**: The command output automatically suggests the best follow-up commands (e.g., `aline watcher session/event show`).
"""

# Aline Share skill definition for Claude Code
# Installed to ~/.claude/skills/aline-share/SKILL.md
ALINE_SHARE_SKILL_MD = """---
name: aline-share
description: Create shareable links from conversation history. Use when users want to share work, create share links, or export conversations for team communication.
---

# Aline Share Skill

This skill guides you through creating shareable links from Aline conversation history. Follow this interactive workflow to search sessions, generate events, and export share links.

## Workflow Overview

```
Search Sessions → User Selection → Generate Event → Preview → Export Share Link
```

## Step-by-Step Guide

### Step 1: Search Sessions

Start by searching for relevant sessions using the user's query:

```bash
aline search "<user_query>" -t session
```

Example:
```bash
aline search "authentication refactor" -t session
```

### Step 2: Interactive Session Selection

Present the search results to the user and ask which sessions to include using `AskUserQuestion`:

```json
{
  "questions": [{
    "header": "Sessions",
    "question": "Which sessions should I include in the share?",
    "options": [
      {"label": "All listed", "description": "Include all sessions from search results"},
      {"label": "Select specific", "description": "I'll specify which sessions by index"},
      {"label": "Search again", "description": "Refine the search with different terms"}
    ],
    "multiSelect": false
  }]
}
```

If user selects "Select specific", ask for the session indices:
```json
{
  "questions": [{
    "header": "Indices",
    "question": "Which session indices? (e.g., 1,3,5 or 1-3)",
    "options": [
      {"label": "Enter indices", "description": "I'll type the specific indices"},
      {"label": "Go back", "description": "Show me the list again"}
    ],
    "multiSelect": false
  }]
}
```

### Step 3: Generate Event

Once sessions are selected, generate an event using the selector:

```bash
# Using comma-separated indices
aline watcher event generate 1,3,5

# Using range
aline watcher event generate 1-3

# Using UUID prefix
aline watcher event generate abc123
```

The command will output event details including an index number.

### Step 4: Confirm Share Creation

Show the event summary and ask if user wants a shareable link:

```json
{
  "questions": [{
    "header": "Share?",
    "question": "Create a shareable link for this event?",
    "options": [
      {"label": "Yes", "description": "Generate encrypted shareable link"},
      {"label": "No", "description": "Keep the event locally only"}
    ],
    "multiSelect": false
  }]
}
```

### Step 5: Export Share Link

If user confirms, export the share link:

```bash
aline share export -i <event_index> --json --no-preview
```

Example:
```bash
aline share export -i 0 --json --no-preview
```

This outputs JSON with the share URL and a formatted Slack message.

### Step 6: Present Results

Parse the JSON output and present to the user:
- **Share URL**: The shareable link
- **Slack Message**: Pre-formatted message ready to paste in Slack

## Command Reference

| Command | Purpose |
|---------|---------|
| `aline search "<query>" -t session` | Search for sessions matching a pattern |
| `aline watcher event generate <selector>` | Create an event from selected sessions |
| `aline watcher event show <event_id>` | View event details |
| `aline share export -i <index> --json --no-preview` | Export share link as JSON |
| `aline share export -i <index>` | Export share link with browser preview |

## Session Selector Syntax

The `event generate` command accepts flexible selectors:

| Syntax | Example | Description |
|--------|---------|-------------|
| Single index | `1` | Session at index 1 |
| Multiple indices | `1,3,5` | Sessions at indices 1, 3, and 5 |
| Range | `1-5` | Sessions from index 1 to 5 |
| UUID prefix | `abc123` | Session with matching UUID prefix |
| Mixed | `1,3-5,abc` | Combination of indices, ranges, and prefixes |

## Error Handling

- **No sessions found**: Suggest broadening the search query or using regex patterns
- **Invalid selector**: Explain the selector syntax and ask user to retry
- **Event generation fails**: Check if sessions exist and are accessible
- **Share export fails**: Verify event index is valid using `aline watcher event list`

## When to Use This Skill

Use this skill when the user wants to:
- Share conversation history with teammates
- Create a link to specific coding sessions
- Export work for documentation or review
- Send Slack updates about completed work
"""

# Aline Import History Sessions skill definition for Claude Code
# Installed to ~/.claude/skills/aline-import-history-sessions/SKILL.md
ALINE_IMPORT_HISTORY_SESSIONS_SKILL_MD = """---
name: aline-import-history-sessions
description: Guide users through importing Claude Code session history into Aline database. Use this for first-time setup, onboarding new users, or when users want to selectively import historical sessions. Provides interactive workflow with progress checking.
---

# Aline Import History Sessions Skill

This skill guides users through the process of importing Claude Code session history into Aline's database. It provides an interactive, step-by-step workflow to help users discover, select, and import their historical sessions.

## Workflow Overview

```
Analyze Unimported Sessions → Present Summary → User Selection → Import Sessions → Verify Success → Continue or Finish
```

## Step-by-Step Guide

### Step 1: Analyze Current Status

First, list all sessions to understand what hasn't been imported yet:

```bash
aline watcher session list --detect-turns
```

**Internal analysis (do NOT expose status terminology to user):**
- Count sessions with status `new` → these are "unimported sessions"
- Count sessions with status `partial` → these have "updates available"
- Count sessions with status `tracked` → these are "already imported"

Parse the output to extract:
- Total number of unimported sessions
- Their session IDs (use these for import, NOT index numbers)
- Project paths they belong to

### Step 2: Present Summary to User

Present a user-friendly summary WITHOUT mentioning internal status labels:

Example:
> "I found **47 sessions** in your Claude Code history:
> - **12 sessions** haven't been imported yet
> - **3 sessions** have updates since last import
> - **32 sessions** are already fully imported
>
> The unimported sessions span these projects:
> - `/Users/you/Projects/ProjectA` (5 sessions)
> - `/Users/you/Projects/ProjectB` (7 sessions)"

### Step 3: Ask User Import Preferences

Use `AskUserQuestion` to understand what the user wants to import:

```json
{
  "questions": [{
    "header": "Import scope",
    "question": "Which sessions would you like to import?",
    "options": [
      {"label": "All unimported (Recommended)", "description": "Import all 12 sessions that haven't been imported yet"},
      {"label": "Include updates", "description": "Import unimported sessions + update 3 sessions with new content"},
      {"label": "Select by project", "description": "Choose which project's sessions to import"},
      {"label": "Select specific", "description": "I'll review and pick individual sessions"}
    ],
    "multiSelect": false
  }]
}
```

### Step 4: Handle User Selection

#### If "All unimported":
Confirm the import with session count:
```json
{
  "questions": [{
    "header": "Confirm",
    "question": "Ready to import 12 sessions. Proceed?",
    "options": [
      {"label": "Yes, import", "description": "Start importing all unimported sessions"},
      {"label": "Let me review first", "description": "Show me the session list to review"}
    ],
    "multiSelect": false
  }]
}
```

#### If "Select by project":
List the projects with unimported sessions and ask:
```json
{
  "questions": [{
    "header": "Project",
    "question": "Which project's sessions should I import?",
    "options": [
      {"label": "ProjectA", "description": "5 unimported sessions"},
      {"label": "ProjectB", "description": "7 unimported sessions"},
      {"label": "Current directory", "description": "Import sessions from the current working directory"}
    ],
    "multiSelect": true
  }]
}
```

#### If "Select specific":
Show the session list with details (project path, turn count, last modified) and let user specify which ones. When user provides selection, map their choice back to session IDs.

### Step 5: Execute Import

**IMPORTANT: Always use session_id for imports, NOT index numbers.** Index numbers can change between list operations and cause wrong sessions to be imported.

```bash
# Import by session ID (PREFERRED - always use this)
aline watcher session import abc12345-6789-...

# Import multiple by session ID
aline watcher session import abc12345,def67890,ghi11111

# With force flag (re-import already tracked)
aline watcher session import abc12345 --force

# With regenerate flag (update summaries)
aline watcher session import abc12345 --regenerate

# Synchronous import to wait for completion
aline watcher session import abc12345 --sync
```

For importing multiple sessions, collect all the session IDs from your analysis and pass them comma-separated.

### Step 6: Verify Import Success

After import, check the status again:

```bash
aline watcher session list --detect-turns
```

Verify:
- Previously unimported sessions should now show as imported
- Check for any errors in the import output
- Report success/failure count to user

### Step 7: Ask If User Is Satisfied

```json
{
  "questions": [{
    "header": "Continue?",
    "question": "Successfully imported X sessions. What would you like to do next?",
    "options": [
      {"label": "Import more", "description": "Select additional sessions to import"},
      {"label": "View imported", "description": "Show details of imported sessions"},
      {"label": "Done", "description": "Finish the import process"}
    ],
    "multiSelect": false
  }]
}
```

If user wants to import more, loop back to Step 1.

### Step 8: Final Summary

When the user is done, provide a summary:
- Total sessions imported in this session
- Sessions that were updated
- Any errors encountered
- Next steps: suggest `aline search` to explore their imported history

## Command Reference

| Command | Purpose |
|---------|---------|
| `aline watcher session list` | List all discovered sessions with status |
| `aline watcher session list --detect-turns` | Include turn counts in listing |
| `aline watcher session list -p N -n M` | Paginate: page N with M items per page |
| `aline watcher session import <session_id>` | Import by session ID (recommended) |
| `aline watcher session import <id1>,<id2>` | Import multiple sessions by ID |
| `aline watcher session import <id> -f` | Force re-import |
| `aline watcher session import <id> -r` | Regenerate LLM summaries |
| `aline watcher session import <id> --sync` | Synchronous import (wait for completion) |
| `aline watcher session show <session_id>` | View details of a specific session |

## Important: Use Session IDs, Not Index Numbers

**Always use session_id (UUID) for import operations.**

Why:
- Index numbers are assigned dynamically and can change between list commands
- Using wrong index could import unintended sessions
- Session IDs are stable and unique identifiers

Example session ID format: `e58f67bf-ebba-47bd-9371-5ef9e06697d3`

You can use UUID prefix for convenience: `e58f67bf` (first 8 characters)

## Error Handling

- **No sessions found**: Check if Claude Code history exists at `~/.claude/projects/`. Suggest running some Claude Code sessions first.
- **Import fails**: Check disk space, database permissions at `~/.aline/db/aline.db`
- **Partial import**: Some sessions may fail due to corrupted JSONL files. Report specific errors and suggest `--force` retry.
- **Watcher not running**: If async import doesn't complete, suggest `aline watcher start` or use `--sync` flag.

## Tips for Large Imports

- For many sessions (50+), import in batches to track progress
- Use `--sync` flag to see real-time progress for smaller batches
- Check `~/.aline/.logs/watcher.log` for detailed import logs

## When to Use This Skill

Use this skill when:
- User is setting up Aline for the first time
- User wants to import historical Claude Code sessions
- User asks "how do I import my history?" or similar
- User wants to selectively import specific project sessions
- User needs to re-import or update existing sessions
"""

# Registry of all skills to install
SKILLS_REGISTRY: dict[str, str] = {
    "aline": ALINE_SKILL_MD,
    "aline-share": ALINE_SHARE_SKILL_MD,
    "aline-import-history-sessions": ALINE_IMPORT_HISTORY_SESSIONS_SKILL_MD,
}


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=False, check=False)


def _source_aline_tmux_conf(tmux_conf: Path) -> None:
    """Best-effort apply the config to Aline-managed tmux servers."""
    if shutil.which("tmux") is None:
        return

    for socket in ("aline_dash", "aline_term"):
        try:
            _run(["tmux", "-L", socket, "source-file", str(tmux_conf)])
        except Exception:
            continue


def _find_brew() -> str | None:
    brew = shutil.which("brew")
    return brew


def _prompt_install_homebrew() -> bool:
    if not sys.stdin.isatty():
        console.print("[red]Homebrew not found.[/red]")
        console.print("[dim]Install from https://brew.sh and retry.[/dim]")
        return False

    console.print("[yellow]Homebrew not found.[/yellow]")
    console.print("[dim]Aline can install tmux automatically via Homebrew.[/dim]\n")
    try:
        answer = console.input("Install Homebrew now? ([green]y[/green]/[yellow]n[/yellow]): ").strip()
    except (EOFError, KeyboardInterrupt):
        return False
    if answer.lower() not in ("y", "yes"):
        console.print("[dim]Skipped Homebrew install.[/dim]")
        console.print("[dim]Install from https://brew.sh and retry.[/dim]")
        return False

    console.print("\n[bold]Installing Homebrew (official script)...[/bold]")
    console.print(
        "[dim]Tip: if this fails, follow the manual steps at https://brew.sh[/dim]\n"
    )
    # Official install script (see https://brew.sh).
    proc = subprocess.run(
        [
            "/bin/bash",
            "-c",
            "curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | /bin/bash",
        ],
        text=True,
        capture_output=False,
        check=False,
    )
    if proc.returncode != 0:
        console.print(f"[red]Failed:[/red] Homebrew install (exit {proc.returncode})")
        return False
    return True


def add_tmux_command(*, install_brew: bool = False) -> int:
    """Install tmux (via Homebrew) and set up Aline's tmux config."""
    brew = _find_brew()
    if brew is None:
        if sys.platform == "darwin" and install_brew:
            if not _prompt_install_homebrew():
                return 1
            brew = _find_brew()
        if brew is None:
            console.print("[red]Homebrew not found.[/red] Install from https://brew.sh and retry.")
            return 1

    console.print("[dim]Running: brew install tmux[/dim]")
    proc = _run([brew, "install", "tmux"])
    if proc.returncode != 0:
        console.print(f"[red]Failed:[/red] brew install tmux (exit {proc.returncode})")
        return int(proc.returncode or 1)

    from .init import _initialize_tmux_config

    tmux_conf = _initialize_tmux_config()
    _source_aline_tmux_conf(tmux_conf)

    console.print(f"[green]✓[/green] tmux installed and config ready: [cyan]{tmux_conf}[/cyan]")
    console.print(
        "[dim]Tip: in the Aline dashboard tmux session, mouse drag will copy to clipboard.[/dim]"
    )
    return 0


def _ensure_symlink(target_link: Path, source_file: Path, force: bool = False) -> bool:
    """Create a symlink at target_link pointing to source_file.

    Args:
        target_link: The path where the symlink should be created (e.g., ~/.claude/skills/aline/SKILL.md)
        source_file: The actual file to link to (e.g., ~/.aline/skills/aline/SKILL.md)
        force: Whether to overwrite existing files/links

    Returns:
        True if a new link was created or updated, False if skipped (already exists)
    """
    if target_link.exists() or target_link.is_symlink():
        if not force:
            # Check if it already points to the right place
            try:
                if target_link.is_symlink() and target_link.resolve() == source_file.resolve():
                    return False  # Already correct
            except Exception:
                pass
            return False  # Exists and not forced

        # Force: remove existing
        if target_link.is_dir() and not target_link.is_symlink():
            shutil.rmtree(target_link)
        else:
            target_link.unlink()

    target_link.parent.mkdir(parents=True, exist_ok=True)
    target_link.symlink_to(source_file)
    return True


def _ensure_copy(target_file: Path, source_file: Path, force: bool = False) -> bool:
    """Copy source_file to target_file.

    Returns:
        True if target was created/updated, False if skipped.
    """
    if target_file.exists() or target_file.is_symlink():
        if not force:
            return False
        if target_file.is_dir() and not target_file.is_symlink():
            shutil.rmtree(target_file)
        else:
            target_file.unlink()

    target_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, target_file)
    return True


def add_skills_command(force: bool = False) -> int:
    """Install Aline skills for Claude Code and Codex.

    1. Writes built-in skills to ~/.aline/skills/
    2. Creates symlinks in ~/.claude/skills/ and ~/.codex/skills/

    Args:
        force: Overwrite existing skills if they exist

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    aline_skill_root = Path.home() / ".aline" / "skills"
    codex_home_env = os.environ.get("CODEX_HOME", "").strip()
    codex_home = Path.home() / ".codex"
    if codex_home_env:
        env_path = Path(codex_home_env).expanduser()
        # Avoid installing into per-terminal isolated CODEX_HOME dirs.
        if ".aline/codex_homes" not in str(env_path):
            codex_home = env_path
    targets = [
        ("Claude", Path.home() / ".claude" / "skills", "symlink"),
        # Codex skills are safer as real files: some environments/tools ignore symlinks.
        ("Codex", codex_home / "skills", "copy"),
        ("OpenCode", Path.home() / ".config" / "opencode" / "skill", "symlink"),
    ]

    installed_skills: list[str] = []
    skipped_skills: list[str] = []
    failed_skills: list[tuple[str, str]] = []

    for skill_name, skill_content in SKILLS_REGISTRY.items():
        # 1. Update master copy in ~/.aline/skills
        master_path = aline_skill_root / skill_name / "SKILL.md"
        try:
            master_path.parent.mkdir(parents=True, exist_ok=True)
            master_path.write_text(skill_content, encoding="utf-8")
        except Exception as e:
            failed_skills.append((f"{skill_name} (storage)", str(e)))
            continue

        # 2. Link to targets
        for tool_name, tool_root, mode in targets:
            dest_path = tool_root / skill_name / "SKILL.md"

            try:
                if mode == "copy":
                    updated = _ensure_copy(dest_path, master_path, force)
                else:
                    updated = _ensure_symlink(dest_path, master_path, force)
                if updated:
                    installed_skills.append(f"{tool_name}/{skill_name}")
                else:
                    skipped_skills.append(f"{tool_name}/{skill_name}")
            except Exception as e:
                failed_skills.append((f"{tool_name}/{skill_name}", str(e)))

    # Report results
    for item in installed_skills:
        console.print(f"[green]✓[/green] Installed: [cyan]{item}[/cyan]")

    for item in skipped_skills:
        console.print(f"[yellow]⊘[/yellow] Already exists: [dim]{item}[/dim]")

    for item, error in failed_skills:
        console.print(f"[red]✗[/red] Failed to install {item}: {error}")

    if skipped_skills and not installed_skills:
        console.print("[dim]Use --force to overwrite existing skills[/dim]")
    elif installed_skills:
        console.print("[dim]Restart your AI tools to activate new skills[/dim]")

    return 1 if failed_skills else 0


def add_skills_dev_command(force: bool = False) -> int:
    """Install developer skills from skill-dev/ directory.

    Symlinks skills from ./skill-dev/ to ~/.claude/skills/ and ~/.codex/skills/

    Args:
        force: Overwrite existing skills if they exist

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Find skill-dev directory relative to this file's package location
    package_root = Path(__file__).parent.parent.parent.parent
    skill_dev_dir = package_root / "skill-dev"

    if not skill_dev_dir.exists():
        console.print(f"[red]skill-dev/ directory not found at:[/red] {skill_dev_dir}")
        console.print("[dim]This command is for developer use only.[/dim]")
        return 1

    targets = [
        ("Claude", Path.home() / ".claude" / "skills"),
        ("Codex", Path.home() / ".codex" / "skills"),
        ("OpenCode", Path.home() / ".config" / "opencode" / "skill"),
    ]

    installed_skills: list[str] = []
    skipped_skills: list[str] = []
    failed_skills: list[tuple[str, str]] = []

    # Scan skill-dev for directories containing SKILL.md
    for skill_dir in skill_dev_dir.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        skill_name = skill_dir.name

        for tool_name, tool_root in targets:
            dest_path = tool_root / skill_name / "SKILL.md"

            try:
                updated = _ensure_symlink(dest_path, skill_file, force)
                if updated:
                    installed_skills.append(f"{tool_name}/{skill_name}")
                else:
                    skipped_skills.append(f"{tool_name}/{skill_name}")
            except Exception as e:
                failed_skills.append((f"{tool_name}/{skill_name}", str(e)))

    if not installed_skills and not skipped_skills and not failed_skills:
        console.print("[yellow]No skills found in skill-dev/[/yellow]")
        return 0

    # Report results
    for item in installed_skills:
        console.print(f"[green]✓[/green] Linked: [cyan]{item}[/cyan]")

    for item in skipped_skills:
        console.print(f"[yellow]⊘[/yellow] Already exists: [dim]{item}[/dim]")

    for item, error in failed_skills:
        console.print(f"[red]✗[/red] Failed to install {item}: {error}")

    if skipped_skills and not installed_skills:
        console.print("[dim]Use --force to overwrite existing skills[/dim]")
    elif installed_skills:
        console.print("[dim]Restart your AI tools to activate new skills[/dim]")

    return 1 if failed_skills else 0

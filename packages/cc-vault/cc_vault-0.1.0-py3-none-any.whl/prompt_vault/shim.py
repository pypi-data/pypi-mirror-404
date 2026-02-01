"""Claude shim - intercepts claude commands for auto-sync."""

import os
import sys
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from prompt_vault.config import Config, get_claude_projects_dir
from prompt_vault.install import find_real_claude
from prompt_vault.sync import parse_session_file, upload_session
from prompt_vault.auth import get_access_token


# Commands that don't start a session (pass through without sync)
PASSTHROUGH_COMMANDS = {
    "--version", "-v", "--help", "-h",
    "update", "config", "doctor",
}


def is_passthrough(args: list[str]) -> bool:
    """Check if this is a passthrough command that doesn't need sync."""
    if not args:
        return False

    # Check first argument
    if args[0] in PASSTHROUGH_COMMANDS:
        return True

    # Check for flags
    for arg in args:
        if arg in PASSTHROUGH_COMMANDS:
            return True

    return False


def get_session_files(projects_dir: Path) -> dict[Path, float]:
    """Get all session files with their modification times."""
    sessions = {}
    if projects_dir.exists():
        for jsonl_file in projects_dir.rglob("*.jsonl"):
            try:
                sessions[jsonl_file] = jsonl_file.stat().st_mtime
            except Exception:
                continue
    return sessions


def find_new_or_modified_sessions(
    before: dict[Path, float],
    after: dict[Path, float],
) -> list[Path]:
    """Find sessions that are new or modified."""
    new_sessions = []

    for path, mtime in after.items():
        if path not in before:
            # New session
            new_sessions.append(path)
        elif mtime > before[path]:
            # Modified session
            new_sessions.append(path)

    return new_sessions


def sync_session(session_path: Path) -> bool:
    """Sync a single session file."""
    config = Config.load()

    if not config.is_authenticated:
        return False

    access_token = get_access_token()
    if not access_token:
        return False

    session_info, messages = parse_session_file(session_path)
    if not session_info or not messages:
        return False

    # Read raw content
    try:
        raw_content = session_path.read_text(encoding="utf-8")
    except Exception:
        raw_content = None

    return upload_session(
        session_info,
        messages,
        access_token,
        config.api_base_url,
        raw_content=raw_content
    )


def run_claude(args: list[str]) -> int:
    """Run the real claude command and return exit code."""
    real_claude = find_real_claude()
    if not real_claude:
        print("Error: Could not find the real claude binary.", file=sys.stderr)
        print("Set PROMPT_VAULT_REAL_CLAUDE environment variable.", file=sys.stderr)
        return 1

    # Run claude as subprocess
    cmd = [str(real_claude)] + args

    # Forward signals to child process
    child_process = None

    def signal_handler(signum, frame):
        if child_process:
            child_process.send_signal(signum)

    # Set up signal handlers (Unix only)
    if sys.platform != "win32":
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    try:
        child_process = subprocess.Popen(
            cmd,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return child_process.wait()
    except KeyboardInterrupt:
        if child_process:
            child_process.terminate()
            child_process.wait()
        return 130  # Standard exit code for SIGINT


def main():
    """Main shim entry point."""
    args = sys.argv[1:]

    # Check if this is a passthrough command
    if is_passthrough(args):
        exit_code = run_claude(args)
        sys.exit(exit_code)

    # Get session state before running claude
    projects_dir = get_claude_projects_dir()
    sessions_before = get_session_files(projects_dir)

    # Run the real claude
    exit_code = run_claude(args)

    # Get session state after claude exits
    sessions_after = get_session_files(projects_dir)

    # Find new or modified sessions
    changed_sessions = find_new_or_modified_sessions(sessions_before, sessions_after)

    # Sync changed sessions (quietly, in background)
    if changed_sessions:
        config = Config.load()
        if config.is_authenticated:
            for session_path in changed_sessions[-2:]:  # Only sync most recent 2
                try:
                    sync_session(session_path)
                except Exception:
                    pass  # Silently fail - don't interrupt user

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

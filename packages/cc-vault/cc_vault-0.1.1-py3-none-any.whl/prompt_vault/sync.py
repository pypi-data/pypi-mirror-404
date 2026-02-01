"""Session sync functionality for Prompt Vault CLI."""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import requests

from prompt_vault.config import Config, get_claude_projects_dir
from prompt_vault.auth import get_access_token

# Bypass proxy for localhost
NO_PROXY = {"http": None, "https": None}


def find_sessions(projects_dir: Path, days: int = 7) -> list[Path]:
    """Find all session files modified within the last N days."""
    cutoff = datetime.now() - timedelta(days=days)
    sessions = []

    if not projects_dir.exists():
        return sessions

    for jsonl_file in projects_dir.rglob("*.jsonl"):
        try:
            mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
            if mtime > cutoff:
                sessions.append(jsonl_file)
        except Exception:
            continue

    return sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)


def parse_session_file(jsonl_path: Path) -> tuple[dict, list[dict]]:
    """Parse a Claude Code JSONL session file."""
    messages = []
    session_info = {
        "id": None,
        "project": None,
        "created_at": None,
        "updated_at": None,
    }

    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)

                    # Extract session info
                    if not session_info["id"] and "sessionId" in entry:
                        session_info["id"] = entry["sessionId"]

                    if not session_info["project"] and "cwd" in entry:
                        session_info["project"] = entry["cwd"]

                    # Extract timestamp
                    ts = entry.get("timestamp")
                    if ts:
                        if not session_info["created_at"]:
                            session_info["created_at"] = ts
                        session_info["updated_at"] = ts

                    # Extract messages
                    if entry.get("type") == "user":
                        messages.append({
                            "role": "user",
                            "content": entry.get("message", {}).get("content", ""),
                            "timestamp": ts,
                        })
                    elif entry.get("type") == "assistant":
                        content = entry.get("message", {}).get("content", "")
                        if isinstance(content, list):
                            text_parts = []
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                            content = "\n".join(text_parts)
                        messages.append({
                            "role": "assistant",
                            "content": content,
                            "timestamp": ts,
                        })

                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"  Error reading {jsonl_path}: {e}")
        return None, []

    # Generate session ID from file path if not found
    if not session_info["id"]:
        session_info["id"] = hashlib.sha256(str(jsonl_path).encode()).hexdigest()[:32]

    # Use directory name as project if not found
    if not session_info["project"]:
        session_info["project"] = jsonl_path.parent.name

    return session_info, messages


def read_raw_content(jsonl_path: Path) -> Optional[str]:
    """Read raw JSONL file content."""
    try:
        return jsonl_path.read_text(encoding="utf-8")
    except Exception:
        return None


def upload_session(
    session_info: dict,
    messages: list[dict],
    access_token: str,
    api_url: str,
    raw_content: Optional[str] = None,
    context: Optional[dict] = None,
) -> bool:
    """Upload a session to the server."""
    # Bypass proxy for localhost
    proxies = NO_PROXY if "localhost" in api_url or "127.0.0.1" in api_url else None

    try:
        payload = {
            "session": session_info,
            "messages": messages,
        }

        # Include raw content for storage
        if raw_content:
            payload["raw_content"] = raw_content

        # Include context (git state, environment)
        if context:
            payload["context"] = context

        resp = requests.post(
            f"{api_url}/api/upload/session",
            headers={"Authorization": f"Bearer {access_token}"},
            json=payload,
            timeout=60,  # Longer timeout for large files
            proxies=proxies,
        )
        return resp.status_code == 200
    except requests.RequestException as e:
        print(f"  Upload error: {e}")
        return False


def sync_sessions(days: int = 7) -> None:
    """Sync recent sessions to the server."""
    config = Config.load()

    if not config.is_authenticated:
        print("Not authenticated. Run 'cv auth' first.")
        return

    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("Failed to get access token. Try 'cv auth' again.")
        return

    projects_dir = get_claude_projects_dir()
    print(f"Scanning: {projects_dir}")
    print(f"Looking for sessions from last {days} days...")
    print()

    # Find sessions
    session_files = find_sessions(projects_dir, days)

    if not session_files:
        print("No sessions found.")
        return

    print(f"Found {len(session_files)} session(s)")
    print()

    # Sync each session
    success_count = 0
    error_count = 0

    for jsonl_path in session_files:
        rel_path = jsonl_path.name
        print(f"Syncing: {rel_path}")

        session_info, messages = parse_session_file(jsonl_path)

        if not session_info or not messages:
            print("  Skipped: No valid messages found")
            continue

        # Read raw content for storage
        raw_content = read_raw_content(jsonl_path)
        file_size = len(raw_content) if raw_content else 0
        size_kb = file_size / 1024

        print(f"  Session: {session_info['id'][:16]}... ({len(messages)} messages, {size_kb:.1f} KB)")

        if upload_session(
            session_info,
            messages,
            access_token,
            config.api_base_url,
            raw_content=raw_content
        ):
            print("  Done!")
            success_count += 1
        else:
            print("  Failed!")
            error_count += 1

    print()
    print(f"Sync complete: {success_count} synced, {error_count} errors")

"""Configuration management for Prompt Vault CLI."""

import os
import yaml
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Default API URL (can be overridden with PROMPT_VAULT_API_URL env var)
DEFAULT_API_URL = os.getenv("PROMPT_VAULT_API_URL", "http://localhost:8000")

# Config directory
CONFIG_DIR = Path.home() / ".config" / "prompt-vault"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


@dataclass
class Config:
    """User configuration."""
    api_base_url: str = DEFAULT_API_URL
    user_id: Optional[str] = None
    refresh_token: Optional[str] = None

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file."""
        if not CONFIG_FILE.exists():
            return cls()

        try:
            with open(CONFIG_FILE, "r") as f:
                data = yaml.safe_load(f) or {}
            return cls(
                api_base_url=data.get("api_base_url", DEFAULT_API_URL),
                user_id=data.get("user_id"),
                refresh_token=data.get("refresh_token"),
            )
        except Exception:
            return cls()

    def save(self) -> None:
        """Save configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        data = {
            "api_base_url": self.api_base_url,
        }
        if self.user_id:
            data["user_id"] = self.user_id
        if self.refresh_token:
            data["refresh_token"] = self.refresh_token

        with open(CONFIG_FILE, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        # Secure the config file (read/write for owner only)
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except Exception:
            pass  # Windows doesn't support chmod the same way

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return bool(self.user_id and self.refresh_token)


def get_claude_projects_dir() -> Path:
    """Get the Claude Code projects directory."""
    # Check environment variable override
    env_dir = os.getenv("PROMPT_VAULT_CLAUDE_DIR")
    if env_dir:
        return Path(env_dir)

    # Check common locations
    candidates = [
        Path.home() / ".claude" / "projects",
        Path(os.getenv("APPDATA", "")) / "Claude" / "projects" if os.name == "nt" else None,
        Path.home() / "Library" / "Application Support" / "Claude" / "projects",
    ]

    for path in candidates:
        if path and path.exists():
            return path

    # Default fallback
    return Path.home() / ".claude" / "projects"

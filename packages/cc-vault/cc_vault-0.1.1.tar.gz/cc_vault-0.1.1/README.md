# CC-Vault

Automatic Claude Code session backup and search. Your conversations, synced and searchable.

## Installation

```bash
pip install cc-vault
```

## Quick Start

### 1. Authenticate

```bash
cv auth
```

Opens your browser for GitHub login. Once approved, the CLI stores a refresh token locally.

### 2. Enable Auto-Sync

```bash
cv install && source ~/.bashrc
```

This installs a shim that automatically uploads sessions after each `claude` command.

### 3. Use Claude Normally

```bash
claude
```

Sessions are automatically synced when you exit.

## CLI Commands

| Command | Description |
|---------|-------------|
| `cv auth` | Authenticate with GitHub |
| `cv sync` | Manually sync recent sessions (last 7 days) |
| `cv sync --days 30` | Sync sessions from last 30 days |
| `cv install` | Install claude shim for auto-sync |
| `cv uninstall` | Remove the claude shim |
| `cv status` | Show authentication and shim status |

## How It Works

### Authentication

1. Run `cv auth`
2. Browser opens for GitHub login
3. Approve the device code shown in terminal
4. CLI saves token to `~/.config/prompt-vault/config.yaml`

### Auto-Sync

1. `cv install` creates a shim that wraps the `claude` command
2. When you run `claude`, the shim runs the real Claude CLI
3. After Claude exits, new/modified sessions are uploaded automatically

## Configuration

Config is stored at `~/.config/prompt-vault/config.yaml`:

```yaml
api_base_url: https://your-backend-url.com
refresh_token: eyJ...
user_id: user_abc123
```

## Claude Code Data Location

Sessions are read from:
- **Windows**: `%LOCALAPPDATA%\claude\projects\`
- **Mac/Linux**: `~/.claude/projects/`

## License

MIT

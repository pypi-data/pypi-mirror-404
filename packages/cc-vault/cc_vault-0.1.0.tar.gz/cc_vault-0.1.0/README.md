# Prompt Vault

Automatic Claude Code session backup and search. Your conversations, synced and searchable.

## Features

- **Auto-Sync**: Automatically uploads sessions after each `claude` command
- **Manual Sync**: Bulk sync recent sessions with `pv sync`
- **Full-Text Search**: Search across all your conversations
- **Web Dashboard**: Browse and view sessions from any device
- **Multi-User**: Each user's data is isolated with Row Level Security
- **Raw File Storage**: Complete session files stored in Supabase Storage

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Claude Shim    │────▶│   FastAPI       │────▶│   Supabase      │
│  (Auto-upload)  │     │   Backend       │     │   PostgreSQL    │
└─────────────────┘     └─────────────────┘     │   + Storage     │
                               ▲                └─────────────────┘
                               │
┌─────────────────┐            │
│   Next.js       │────────────┘
│   Frontend      │
└─────────────────┘
```

## Quick Start

### 1. Install CLI

```bash
git clone https://github.com/rstar327/prompt-vault.git
cd prompt-vault
pip install -e .
```

### 2. Authenticate

```bash
pv auth
```

This opens your browser for GitHub login. Once approved, the CLI stores a refresh token locally.

### 3. Enable Auto-Sync

```bash
pv install
```

This installs a shim that intercepts `claude` commands and automatically uploads sessions when they complete.

### 4. Use Claude Normally

```bash
claude
```

Sessions are automatically synced after each conversation.

## CLI Commands

| Command | Description |
|---------|-------------|
| `pv auth` | Authenticate with GitHub via device flow |
| `pv sync` | Manually sync recent sessions (last 7 days) |
| `pv sync --days 30` | Sync sessions from last 30 days |
| `pv install` | Install the claude shim for auto-sync |
| `pv uninstall` | Remove the claude shim |
| `pv status` | Show authentication and shim status |

## Web Dashboard

Visit your deployed frontend to:

- Browse all synced sessions
- Search across conversations
- View full message threads
- Filter by project

## Project Structure

```
prompt-vault/
├── src/prompt_vault/       # Python CLI package
│   ├── cli.py              # CLI commands (pv)
│   ├── auth.py             # Device flow authentication
│   ├── sync.py             # Session parsing and upload
│   ├── shim.py             # Claude command interceptor
│   ├── install.py          # Shim installation
│   └── config.py           # Config management
├── backend/
│   ├── app.py              # FastAPI server
│   ├── storage.py          # Supabase Storage integration
│   ├── store.py            # Device flow token management
│   └── supabase_client.py  # Database operations
├── frontend/
│   ├── app/                # Next.js App Router
│   ├── components/         # React components
│   └── lib/                # API client
├── database/
│   ├── schema.sql          # Main database schema
│   └── add_storage_path.sql # Storage path migration
├── scripts/
│   ├── install.sh          # One-line installer
│   └── uninstall.sh        # Uninstaller
└── pyproject.toml          # Python package config
```

## Deployment

### Prerequisites

- [Supabase](https://supabase.com) account (free tier)
- [Clerk](https://clerk.com) account (free tier)
- [Vercel](https://vercel.com) account (free tier)
- [Render](https://render.com) account (free tier)

### 1. Supabase Setup

1. Create a new project
2. Run `database/schema.sql` in SQL Editor
3. Run `database/add_storage_path.sql` for storage support
4. Create a Storage bucket named `sessions`
5. Get your project URL and keys from Settings > API

### 2. Clerk Setup

1. Create a new application
2. Enable GitHub OAuth
3. Get your publishable key and secret key

### 3. Backend (Render)

Deploy as a Web Service with these environment variables:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
CLERK_SECRET_KEY=sk_live_...
JWT_SECRET=your-random-secret-for-cli-tokens
```

### 4. Frontend (Vercel)

Deploy with these environment variables:

```env
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
```

## How It Works

### Device Flow Authentication

1. User runs `pv auth`
2. CLI requests a device code from backend
3. Browser opens to approval page
4. User logs in with GitHub via Clerk
5. CLI polls for approval, receives refresh token
6. Refresh token stored in `~/.config/prompt-vault/config.yaml`

### Auto-Sync (Shim)

1. `pv install` creates a shim script in `~/.local/bin/claude`
2. Shim records session files before running real claude
3. After claude exits, shim detects new/modified sessions
4. Sessions are silently uploaded in background

### Data Storage

- **PostgreSQL**: Session metadata and searchable messages
- **Supabase Storage**: Raw JSONL files for complete history

## Configuration

CLI config is stored at `~/.config/prompt-vault/config.yaml`:

```yaml
api_base_url: https://your-backend.onrender.com
refresh_token: eyJ...
user_id: user_abc123
```

## Claude Code Data Location

Sessions are read from:
- **Windows**: `%LOCALAPPDATA%\claude\projects\`
- **Mac/Linux**: `~/.claude/projects/`

## License

MIT

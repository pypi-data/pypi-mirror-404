"""Main CLI entry point for Prompt Vault."""

import argparse
import sys

from prompt_vault import __version__
from prompt_vault.config import Config


def cmd_auth(args):
    """Authenticate with Prompt Vault."""
    from prompt_vault.auth import device_flow_auth
    device_flow_auth(args.api_url)


def cmd_sync(args):
    """Manually sync sessions."""
    from prompt_vault.sync import sync_sessions
    sync_sessions(days=args.days)


def cmd_install(args):
    """Install the claude shim."""
    from prompt_vault.install import install_shim
    install_shim(force=args.force)


def cmd_uninstall(args):
    """Uninstall the claude shim."""
    from prompt_vault.install import uninstall_shim
    uninstall_shim()


def cmd_status(args):
    """Show current status."""
    config = Config.load()

    print("Prompt Vault Status")
    print("=" * 40)
    print(f"Version: {__version__}")
    print(f"API URL: {config.api_base_url}")

    if config.is_authenticated:
        print(f"User: {config.user_id}")
        print("Status: Authenticated")
    else:
        print("Status: Not authenticated")
        print("Run 'cv auth' to login")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="cv",
        description="CC-Vault - Automatic Claude Code session sync",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # auth command
    auth_parser = subparsers.add_parser("auth", help="Authenticate with Prompt Vault")
    auth_parser.add_argument(
        "--api-url",
        help="API URL (default: auto-detect from config)",
    )
    auth_parser.set_defaults(func=cmd_auth)

    # sync command
    sync_parser = subparsers.add_parser("sync", help="Manually sync sessions")
    sync_parser.add_argument(
        "--days", "-d",
        type=int,
        default=7,
        help="Sync sessions from last N days (default: 7)",
    )
    sync_parser.set_defaults(func=cmd_sync)

    # install command
    install_parser = subparsers.add_parser("install", help="Install claude shim for auto-sync")
    install_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force reinstall",
    )
    install_parser.set_defaults(func=cmd_install)

    # uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall claude shim")
    uninstall_parser.set_defaults(func=cmd_uninstall)

    # status command
    status_parser = subparsers.add_parser("status", help="Show current status")
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Installation utilities for the claude shim."""

import os
import sys
import stat
from pathlib import Path
from typing import Optional

# Shim installation directory
if sys.platform == "win32":
    SHIM_DIR = Path.home() / ".prompt-vault" / "bin"
else:
    SHIM_DIR = Path.home() / ".local" / "bin"

SHIM_NAME = "claude" if sys.platform != "win32" else "claude.cmd"
SHIM_PATH = SHIM_DIR / SHIM_NAME


def find_real_claude() -> Optional[Path]:
    """Find the real claude binary."""
    # Check environment variable first
    env_claude = os.getenv("PROMPT_VAULT_REAL_CLAUDE")
    if env_claude:
        path = Path(env_claude)
        if path.exists():
            return path

    # Search PATH, excluding our shim directory
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    shim_dir_str = str(SHIM_DIR)

    for dir_path in path_dirs:
        if dir_path == shim_dir_str:
            continue

        if sys.platform == "win32":
            candidates = ["claude.exe", "claude.cmd", "claude.bat"]
        else:
            candidates = ["claude"]

        for name in candidates:
            full_path = Path(dir_path) / name
            if full_path.exists() and full_path.is_file():
                return full_path

    return None


def get_shim_script() -> str:
    """Generate the shim script content."""
    if sys.platform == "win32":
        # Windows batch script
        return '''@echo off
setlocal

REM Prompt Vault Claude Shim
REM This wraps the real claude command to enable auto-sync

REM Find python and run the shim module
python -m prompt_vault.shim %*
'''
    else:
        # Unix shell script
        return '''#!/usr/bin/env bash
# Prompt Vault Claude Shim
# This wraps the real claude command to enable auto-sync

exec python3 -m prompt_vault.shim "$@"
'''


def install_shim(force: bool = False) -> bool:
    """Install the claude shim."""
    from prompt_vault.config import Config

    config = Config.load()
    if not config.is_authenticated:
        print("Not authenticated. Run 'cv auth' first.")
        return False

    # Check for real claude
    real_claude = find_real_claude()
    if not real_claude:
        print("Could not find the real claude binary.")
        print("Make sure Claude Code CLI is installed first.")
        return False

    print(f"Found claude at: {real_claude}")

    # Check if shim already exists
    if SHIM_PATH.exists() and not force:
        print(f"Shim already installed at: {SHIM_PATH}")
        print("Use --force to reinstall.")
        return False

    # Create shim directory
    SHIM_DIR.mkdir(parents=True, exist_ok=True)

    # Write shim script
    shim_content = get_shim_script()
    SHIM_PATH.write_text(shim_content)

    # Make executable (Unix only)
    if sys.platform != "win32":
        SHIM_PATH.chmod(SHIM_PATH.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"Shim installed at: {SHIM_PATH}")
    print()

    # Check if shim dir is in PATH
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    shim_dir_str = str(SHIM_DIR)

    # Normalize paths for comparison
    normalized_path_dirs = [os.path.normpath(p) for p in path_dirs]
    shim_in_path = os.path.normpath(shim_dir_str) in normalized_path_dirs

    if not shim_in_path:
        # Try to auto-add to shell config
        added_to_config = add_to_shell_config()

        if added_to_config:
            print(f"Added {SHIM_DIR} to your shell config.")
            print()
            # Automatically source bashrc by printing eval-able command
            print("PATH updated. Run this to activate now:")
            print()
            print("    source ~/.bashrc")
            print()
            print("Or use this one-liner next time:")
            print("    pv install && source ~/.bashrc")
            print()
        else:
            print("Add this directory to your PATH:")
            print(f"  {SHIM_DIR}")
            print()
            if sys.platform == "win32":
                print("For Windows, add to your PATH environment variable.")
            else:
                print("Add to your ~/.bashrc or ~/.zshrc:")
                print(f'  export PATH="{SHIM_DIR}:$PATH"')
        print()

    print("Installation complete!")
    print("Now when you run 'claude', sessions will auto-sync to Prompt Vault.")
    return True


def add_to_shell_config() -> bool:
    """Add shim directory to shell config file."""
    if sys.platform == "win32":
        # For Windows with Git Bash/MINGW
        shell_configs = [
            Path.home() / ".bashrc",
            Path.home() / ".bash_profile",
        ]
    else:
        # Check which shell is being used
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            shell_configs = [Path.home() / ".zshrc"]
        else:
            shell_configs = [
                Path.home() / ".bashrc",
                Path.home() / ".bash_profile",
            ]

    # Use Unix-style path for shell config
    if sys.platform == "win32":
        shim_path_str = str(SHIM_DIR).replace("\\", "/")
        # Convert Windows path to Unix-style for Git Bash
        if shim_path_str[1] == ":":
            shim_path_str = "/" + shim_path_str[0].lower() + shim_path_str[2:]
        export_line = f'export PATH="{shim_path_str}:$PATH"'
    else:
        export_line = f'export PATH="{SHIM_DIR}:$PATH"'

    marker = "# Prompt Vault shim"
    full_line = f"\n{marker}\n{export_line}\n"

    for config_file in shell_configs:
        try:
            # Check if already added
            if config_file.exists():
                content = config_file.read_text()
                if marker in content:
                    return True  # Already added

            # Append to config file
            with open(config_file, "a") as f:
                f.write(full_line)
            return True
        except Exception:
            continue

    return False


def uninstall_shim() -> bool:
    """Uninstall the claude shim."""
    if not SHIM_PATH.exists():
        print("Shim is not installed.")
        return False

    SHIM_PATH.unlink()
    print(f"Removed: {SHIM_PATH}")

    # Try to remove directory if empty
    try:
        SHIM_DIR.rmdir()
        print(f"Removed: {SHIM_DIR}")
    except OSError:
        pass  # Directory not empty or doesn't exist

    # Remove from shell config
    remove_from_shell_config()

    print("Uninstall complete!")
    return True


def remove_from_shell_config() -> None:
    """Remove shim directory from shell config files."""
    shell_configs = [
        Path.home() / ".bashrc",
        Path.home() / ".bash_profile",
        Path.home() / ".zshrc",
    ]

    marker = "# Prompt Vault shim"

    for config_file in shell_configs:
        try:
            if not config_file.exists():
                continue

            content = config_file.read_text()
            if marker not in content:
                continue

            # Remove the marker and the export line
            lines = content.split("\n")
            new_lines = []
            skip_next = False

            for line in lines:
                if marker in line:
                    skip_next = True
                    continue
                if skip_next and line.startswith("export PATH=") and ".prompt-vault" in line:
                    skip_next = False
                    continue
                skip_next = False
                new_lines.append(line)

            config_file.write_text("\n".join(new_lines))
            print(f"Removed PATH entry from {config_file}")
        except Exception:
            continue

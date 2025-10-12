# ABOUTME: Shared constants for ccthink application
# ABOUTME: Defines timing intervals, file names, and configuration defaults

from pathlib import Path

# Timing
THINKING_WAIT_TIMEOUT_SECONDS = 30

# File names
CONFIG_FILE_NAME = "ccthink.conf"
GITIGNORE_FILE_NAME = ".gitignore"

# Git
GITIGNORE_ENTRIES = [CONFIG_FILE_NAME]

# Paths
DEFAULT_PROJECTS_DIR = "~/.claude/projects/"
FALLBACK_PROJECTS_DIR = "~/.config/claude/projects"

# Defaults
DEFAULT_MAIN_BRANCH = "master"

# ASCII Logo
ASCII_LOGO = """
   ____ ____ _____ _     _       _
  / ___/ ___|_   _| |__ (_)_ __ | | __
 | |  | |     | | | '_ \\| | '_ \\| |/ /
 | |__| |___  | | | | | | | | | |   <
  \\____\\____| |_| |_| |_|_|_| |_|_|\\_\\
"""


def get_config_path() -> Path:
    """Get the configuration file path.

    Returns:
        Path to configuration file in current directory.
    """
    return Path.cwd() / CONFIG_FILE_NAME

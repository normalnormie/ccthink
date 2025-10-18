# ABOUTME: Handler for retrieving Claude project directory
# ABOUTME: Expands paths and checks fallback locations

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.features.app.get_claude_directory.get_claude_directory_response import (
    GetClaudeDirectoryResponse,
)
from src.shared.constants import DEFAULT_PROJECTS_DIR, FALLBACK_PROJECTS_DIR

if TYPE_CHECKING:
    from src.features.app.get_claude_directory.get_claude_directory_command import (
        GetClaudeDirectoryCommand,
    )


class GetClaudeDirectoryHandler:
    """Handler for retrieving Claude project directory."""

    @staticmethod
    def handle(cmd: GetClaudeDirectoryCommand) -> GetClaudeDirectoryResponse:
        """Get Claude project directory with fallback logic.

        Args:
            cmd: Command with config

        Returns:
            Response with directory path
        """
        config = cmd.config
        home = Path.home()
        projects_dir = config.projects_dir

        if projects_dir.startswith("~/"):
            projects_dir = str(home / projects_dir[2:])

        project_name = str(Path.cwd()).replace("/", "-")
        claude_dir = Path(projects_dir) / project_name

        if config.projects_dir == DEFAULT_PROJECTS_DIR and not claude_dir.exists():
            fallback = home / FALLBACK_PROJECTS_DIR[2:] / project_name
            if fallback.exists():
                return GetClaudeDirectoryResponse(directory=fallback)

        return GetClaudeDirectoryResponse(directory=claude_dir)

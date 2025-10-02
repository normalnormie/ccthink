# ABOUTME: Find current JSONL handler implementation
# ABOUTME: Handles locating the active JSONL file by modification timestamp

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from src.features.monitoring.find_current_jsonl.find_current_jsonl_command import (
        FindCurrentJsonlCommand,
    )


@dataclass
class FindCurrentJsonlResponse:
    """Response from finding current JSONL file.

    Attributes:
        jsonl_path: Path to the current JSONL file, None if not found.
    """

    jsonl_path: Path | None


class FindCurrentJsonlHandler:
    """Handler for finding the current active JSONL file."""

    @staticmethod
    def handle(command: FindCurrentJsonlCommand) -> FindCurrentJsonlResponse:
        """Find the current JSONL file with highest modification time.

        Args:
            command: Find current JSONL command with directory path.

        Returns:
            Response containing path to current JSONL file or None.
        """
        if not command.claude_project_dir.exists():
            return FindCurrentJsonlResponse(jsonl_path=None)

        jsonl_files = list(command.claude_project_dir.rglob("*.jsonl"))

        if not jsonl_files:
            return FindCurrentJsonlResponse(jsonl_path=None)

        # Find file with highest modification time
        current_file = max(jsonl_files, key=lambda p: p.stat().st_mtime)

        return FindCurrentJsonlResponse(jsonl_path=current_file)

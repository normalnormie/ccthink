# ABOUTME: Ensure gitignore handler implementation
# ABOUTME: Handles adding entries to .gitignore file

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.features.gitignore.ensure_gitignore.ensure_gitignore_command import (
        EnsureGitignoreCommand,
    )


@dataclass
class EnsureGitignoreResponse:
    """Response from ensuring gitignore entries.

    Attributes:
        success: Whether the operation succeeded.
        written_entries: List of entries that were written.
        error: Error message if operation failed.
    """

    success: bool
    written_entries: list[str]
    error: str | None = None


class EnsureGitignoreHandler:
    """Handler for ensuring entries are in .gitignore."""

    @staticmethod
    def handle(command: EnsureGitignoreCommand) -> EnsureGitignoreResponse:
        """Ensure entries are in .gitignore file.

        Args:
            command: Ensure gitignore command.

        Returns:
            Response with operation status and written entries.
        """
        try:
            # Create .gitignore if it doesn't exist
            if not command.gitignore_path.exists():
                content = "\n".join(command.entries) + "\n"
                command.gitignore_path.write_text(content, encoding="utf-8")
                return EnsureGitignoreResponse(
                    success=True, written_entries=command.entries
                )

            # Read existing content
            content = command.gitignore_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            existing_entries = {line.strip() for line in lines}

            # Find missing entries
            missing_entries = [
                entry for entry in command.entries if entry not in existing_entries
            ]

            if not missing_entries:
                return EnsureGitignoreResponse(success=True, written_entries=[])

            # Add missing entries
            if not content.endswith("\n") and content:
                content += "\n"
            content += "\n".join(missing_entries) + "\n"

            command.gitignore_path.write_text(content, encoding="utf-8")

            return EnsureGitignoreResponse(
                success=True, written_entries=missing_entries
            )

        except (OSError, ValueError) as e:
            return EnsureGitignoreResponse(
                success=False, written_entries=[], error=str(e)
            )

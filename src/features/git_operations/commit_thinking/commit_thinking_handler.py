# ABOUTME: Commit thinking handler implementation
# ABOUTME: Handles creating git commits from thinking content

from __future__ import annotations

import subprocess  # noqa: S404
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.features.git_operations.commit_thinking.commit_thinking_command import (
        CommitThinkingCommand,
    )


@dataclass
class CommitThinkingResponse:
    """Response from committing thinking.

    Attributes:
        success: Whether the commit succeeded.
        nothing_to_commit: Whether there were no changes to commit.
        error: Error message if operation failed.
    """

    success: bool
    nothing_to_commit: bool = False
    error: str | None = None


class CommitThinkingHandler:
    """Handler for committing thinking content to git."""

    @staticmethod
    def handle(command: CommitThinkingCommand) -> CommitThinkingResponse:
        """Create git commit with thinking message.

        Args:
            command: Commit thinking command.

        Returns:
            Response with commit status.
        """
        if command.simulate:
            return CommitThinkingResponse(success=True)

        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )

            # Create commit
            result = subprocess.run(  # noqa: S603
                ["git", "commit", "-m", command.message],  # noqa: S607
                capture_output=True,
                text=True,
                check=False,  # Don't raise on non-zero exit
            )

            # Check if nothing to commit
            if result.returncode != 0:
                if "nothing to commit" in result.stdout.lower():
                    return CommitThinkingResponse(
                        success=True, nothing_to_commit=True
                    )
                return CommitThinkingResponse(
                    success=False,
                    error=f"Commit failed: {result.stderr or result.stdout}",
                )

            return CommitThinkingResponse(success=True)

        except subprocess.CalledProcessError as e:
            return CommitThinkingResponse(
                success=False, error=f"Git operation failed: {e.stderr}"
            )

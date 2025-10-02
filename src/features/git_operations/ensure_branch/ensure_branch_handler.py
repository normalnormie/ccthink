# ABOUTME: Ensure branch handler implementation
# ABOUTME: Handles creating or switching to a git branch

from __future__ import annotations

import subprocess  # noqa: S404
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.features.git_operations.ensure_branch.ensure_branch_command import EnsureBranchCommand


@dataclass
class EnsureBranchResponse:
    """Response from ensuring branch exists.

    Attributes:
        success: Whether the operation succeeded.
        was_created: Whether the branch was created (vs already existed).
        error: Error message if operation failed.
    """

    success: bool
    was_created: bool = False
    error: str | None = None


class EnsureBranchHandler:
    """Handler for ensuring git branch exists and is checked out."""

    @staticmethod
    def _branch_exists(branch_name: str) -> bool:
        """Check if a git branch exists.

        Args:
            branch_name: Name of branch to check.

        Returns:
            True if branch exists, False otherwise.
        """
        try:
            # Check if current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout.strip() == branch_name:
                return True

            # Check if branch exists in list
            result = subprocess.run(  # noqa: S603
                ["git", "branch", "--list", branch_name],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            return False
        else:
            return branch_name in result.stdout

    @staticmethod
    def handle(command: EnsureBranchCommand) -> EnsureBranchResponse:
        """Ensure git branch exists and switch to it.

        Args:
            command: Ensure branch command.

        Returns:
            Response with operation status.
        """
        try:
            if not EnsureBranchHandler._branch_exists(command.branch_name):
                # Create branch
                subprocess.run(  # noqa: S603
                    ["git", "checkout", "-b", command.branch_name],  # noqa: S607
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return EnsureBranchResponse(success=True, was_created=True)

            # Switch to existing branch
            subprocess.run(  # noqa: S603
                ["git", "checkout", command.branch_name],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
            return EnsureBranchResponse(success=True, was_created=False)

        except subprocess.CalledProcessError as e:
            return EnsureBranchResponse(
                success=False, error=f"Git operation failed: {e.stderr}"
            )

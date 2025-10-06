# ABOUTME: Merge branch handler implementation
# ABOUTME: Handles merging one git branch into another

from __future__ import annotations

import subprocess  # noqa: S404
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.features.git_operations.merge_branch.merge_branch_command import MergeBranchCommand


@dataclass
class MergeBranchResponse:
    """Response from merging branches.

    Attributes:
        success: Whether the merge succeeded.
        had_conflict: Whether a merge conflict occurred.
        error: Error message if operation failed.
    """

    success: bool
    had_conflict: bool = False
    error: str | None = None


class MergeBranchHandler:
    """Handler for merging git branches."""

    @staticmethod
    def _get_current_branch() -> str | None:
        """Get the current git branch name.

        Returns:
            Branch name or None if failed.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def branch_exists(branch_name: str) -> bool:
        """Check if a git branch exists.

        Args:
            branch_name: Name of the branch to check.

        Returns:
            True if branch exists, False otherwise.
        """
        try:
            subprocess.run(  # noqa: S603
                ["git", "rev-parse", "--verify", branch_name],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    @staticmethod
    def handle(command: MergeBranchCommand) -> MergeBranchResponse:
        """Merge source branch into target branch.

        Args:
            command: Merge branch command.

        Returns:
            Response with merge status.
        """
        try:
            # Check if already on target branch
            current = MergeBranchHandler._get_current_branch()
            if current == command.target_branch:
                # Already on target, just merge source
                pass
            else:
                # Switch to target branch
                subprocess.run(  # noqa: S603
                    ["git", "checkout", command.target_branch],  # noqa: S607
                    capture_output=True,
                    text=True,
                    check=True,
                )

            # Perform merge
            result = subprocess.run(  # noqa: S603
                ["git", "merge", command.source_branch],  # noqa: S607
                capture_output=True,
                text=True,
                check=False,  # Don't raise on conflict
            )

            # Check for conflict
            if result.returncode != 0:
                # Try to abort merge
                subprocess.run(
                    ["git", "merge", "--abort"],  # noqa: S607
                    capture_output=True,
                    text=True,
                    check=False,
                )

                return MergeBranchResponse(
                    success=False,
                    had_conflict=True,
                    error=f"Merge conflict: {result.stderr or result.stdout}",
                )

            return MergeBranchResponse(success=True)

        except subprocess.CalledProcessError as e:
            return MergeBranchResponse(
                success=False, error=f"Git operation failed: {e.stderr}"
            )

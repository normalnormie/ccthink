# ABOUTME: Handler for graceful application exit
# ABOUTME: Commits pending thinking and merges branches before exit

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from src.features.app.graceful_exit.graceful_exit_response import GracefulExitResponse
from src.features.config.save_config.save_config_command import SaveConfigCommand
from src.features.config.save_config.save_config_handler import SaveConfigHandler
from src.features.git_operations.commit_accumulated_thinking.commit_accumulated_thinking_command import (
    CommitAccumulatedThinkingCommand,
)
from src.features.git_operations.commit_accumulated_thinking.commit_accumulated_thinking_handler import (
    CommitAccumulatedThinkingHandler,
)
from src.features.git_operations.merge_branch.merge_branch_command import (
    MergeBranchCommand,
)
from src.features.git_operations.merge_branch.merge_branch_handler import (
    MergeBranchHandler,
)
from src.features.gitignore.ensure_gitignore.ensure_gitignore_command import (
    EnsureGitignoreCommand,
)
from src.features.gitignore.ensure_gitignore.ensure_gitignore_handler import (
    EnsureGitignoreHandler,
)
from src.shared.constants import GITIGNORE_ENTRIES, get_config_path

if TYPE_CHECKING:
    from src.features.app.graceful_exit.graceful_exit_command import GracefulExitCommand

logger = logging.getLogger(__name__)


class GracefulExitHandler:
    """Handler for graceful application exit."""

    @staticmethod
    async def handle(cmd: GracefulExitCommand) -> GracefulExitResponse:
        """Perform graceful exit with commits and merges.

        Args:
            cmd: Command with config and git status

        Returns:
            Response with exit status
        """
        logger.info("Shutting down...")

        if cmd.config and cmd.enable_git:
            if cmd.config.waiting_for_thinking:
                await CommitAccumulatedThinkingHandler.handle(
                    CommitAccumulatedThinkingCommand(
                        config=cmd.config,
                        enable_git=cmd.enable_git,
                    )
                )

            if cmd.config.monitored_file:
                branch = Path(cmd.config.monitored_file).stem
                if branch != cmd.config.main_branch:
                    GracefulExitHandler._ensure_gitignore_and_merge(
                        branch,
                        cmd.config.main_branch,
                        quit_on_conflict=cmd.config.quit_on_conflict,
                        verbose=cmd.config.verbose,
                    )

        if cmd.config:
            SaveConfigHandler.handle(
                SaveConfigCommand(config=cmd.config, config_path=get_config_path())
            )

        return GracefulExitResponse(success=True)

    @staticmethod
    def _ensure_gitignore_and_merge(
        source_branch: str,
        target_branch: str,
        *,
        quit_on_conflict: bool,
        verbose: bool,
    ) -> None:
        """Ensure .gitignore is configured and merge branch.

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into
            quit_on_conflict: Whether to quit on merge conflict
            verbose: Whether to log merge operations
        """
        EnsureGitignoreHandler.handle(
            EnsureGitignoreCommand(
                entries=GITIGNORE_ENTRIES, gitignore_path=Path.cwd() / ".gitignore"
            )
        )
        response = MergeBranchHandler.handle(
            MergeBranchCommand(
                source_branch=source_branch,
                target_branch=target_branch,
                quit_on_conflict=quit_on_conflict,
            )
        )
        if response.had_conflict and quit_on_conflict:
            logger.error("Merge conflict: %s", response.error)
            sys.exit(1)
        elif not response.success:
            logger.error("Merge failed: %s", response.error)
        elif verbose:
            logger.info("Merge %s -> %s", source_branch, target_branch)

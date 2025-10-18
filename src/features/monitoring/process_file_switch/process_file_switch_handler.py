# ABOUTME: Handler for processing JSONL file switch operations
# ABOUTME: Manages commits, merges, and config updates during file switches

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

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
from src.features.monitoring.process_file_switch.process_file_switch_response import (
    ProcessFileSwitchResponse,
)
from src.shared.constants import GITIGNORE_ENTRIES, get_config_path

if TYPE_CHECKING:
    from src.features.monitoring.process_file_switch.process_file_switch_command import (
        ProcessFileSwitchCommand,
    )

logger = logging.getLogger(__name__)


class ProcessFileSwitchHandler:
    """Handler for processing JSONL file switches."""

    @staticmethod
    async def handle(cmd: ProcessFileSwitchCommand) -> ProcessFileSwitchResponse:
        """Process file switch with commits and merges.

        Args:
            cmd: Command with file path and config

        Returns:
            Response with config state
        """
        config = cmd.config

        if config.verbose:
            logger.info("Monitoring: %s", cmd.current_file)

        if config.monitored_file and cmd.enable_git:
            if config.waiting_for_thinking:
                await CommitAccumulatedThinkingHandler.handle(
                    CommitAccumulatedThinkingCommand(
                        config=config,
                        enable_git=cmd.enable_git,
                    )
                )

            branch = Path(config.monitored_file).stem
            ProcessFileSwitchHandler._ensure_gitignore_and_merge(
                branch,
                config.main_branch,
                quit_on_conflict=config.quit_on_conflict,
                verbose=config.verbose,
                context="during file switch",
            )

        config.monitored_file = str(cmd.current_file)
        config.last_file_position = cmd.current_file.stat().st_size
        config.last_processed_uuid = ""
        config.waiting_for_thinking = False
        config.accumulated_thinking = []
        SaveConfigHandler.handle(
            SaveConfigCommand(config=config, config_path=get_config_path())
        )

        return ProcessFileSwitchResponse(config=config)

    @staticmethod
    def _ensure_gitignore_and_merge(
        source_branch: str,
        target_branch: str,
        *,
        quit_on_conflict: bool,
        verbose: bool,
        context: str = "",
    ) -> None:
        """Ensure .gitignore is configured and merge branch.

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into
            quit_on_conflict: Whether to quit on merge conflict
            verbose: Whether to log merge operations
            context: Additional context for error messages
        """
        ctx = f" {context}" if context else ""

        # Ensure ccthink.conf is in .gitignore before merging
        gitignore_response = EnsureGitignoreHandler.handle(
            EnsureGitignoreCommand(
                entries=GITIGNORE_ENTRIES, gitignore_path=Path.cwd() / ".gitignore"
            )
        )

        if not gitignore_response.success:
            logger.error(
                "Cannot merge%s: failed to add ccthink.conf to .gitignore: %s",
                ctx,
                gitignore_response.error,
            )
            if quit_on_conflict:
                sys.exit(1)
            return

        response = MergeBranchHandler.handle(
            MergeBranchCommand(
                source_branch=source_branch,
                target_branch=target_branch,
                quit_on_conflict=quit_on_conflict,
            )
        )
        if response.had_conflict and quit_on_conflict:
            logger.error("Merge conflict%s: %s", ctx, response.error)
            sys.exit(1)
        elif not response.success:
            logger.error("Merge failed%s: %s", ctx, response.error)
        elif verbose:
            logger.info("Merge %s -> %s", source_branch, target_branch)

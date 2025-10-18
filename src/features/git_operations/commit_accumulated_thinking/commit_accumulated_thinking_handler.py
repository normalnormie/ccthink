# ABOUTME: Handler for committing accumulated thinking to git
# ABOUTME: Orchestrates gitignore setup, commit creation, and config persistence

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.features.config.save_config.save_config_command import SaveConfigCommand
from src.features.config.save_config.save_config_handler import SaveConfigHandler
from src.features.git_operations.commit_accumulated_thinking.commit_accumulated_thinking_response import (
    CommitAccumulatedThinkingResponse,
)
from src.features.git_operations.commit_thinking.commit_thinking_command import (
    CommitThinkingCommand,
)
from src.features.git_operations.commit_thinking.commit_thinking_handler import (
    CommitThinkingHandler,
)
from src.features.gitignore.ensure_gitignore.ensure_gitignore_command import (
    EnsureGitignoreCommand,
)
from src.features.gitignore.ensure_gitignore.ensure_gitignore_handler import (
    EnsureGitignoreHandler,
)
from src.shared.constants import GITIGNORE_ENTRIES, get_config_path

if TYPE_CHECKING:
    from src.features.git_operations.commit_accumulated_thinking.commit_accumulated_thinking_command import (
        CommitAccumulatedThinkingCommand,
    )


class CommitAccumulatedThinkingHandler:
    """Handler for committing accumulated thinking to git."""

    @staticmethod
    async def handle(
        cmd: CommitAccumulatedThinkingCommand,
    ) -> CommitAccumulatedThinkingResponse:
        """Commit accumulated thinking and persist config state.

        Args:
            cmd: Command with config and git enablement status

        Returns:
            Response with operation status and config state
        """
        config = cmd.config

        if not config.waiting_for_thinking:
            return CommitAccumulatedThinkingResponse(
                config=config,
                gitignore_success=True,
                commit_success=True,
            )

        content = "\n\n---\n\n".join(config.accumulated_thinking)
        commit_cmd = CommitThinkingCommand(message=content, simulate=config.simulate)

        gitignore_success = True
        commit_success = True
        error = None

        if cmd.enable_git:
            # Ensure ccthink.conf is in .gitignore before committing
            gitignore_response = EnsureGitignoreHandler.handle(
                EnsureGitignoreCommand(
                    entries=GITIGNORE_ENTRIES,
                    gitignore_path=Path.cwd() / ".gitignore",
                )
            )
            gitignore_success = gitignore_response.success

            # Abort commit if gitignore update failed
            if not gitignore_success:
                error = f"Gitignore update failed: {gitignore_response.error}"
                return CommitAccumulatedThinkingResponse(
                    config=config,
                    gitignore_success=False,
                    commit_success=False,
                    error=error,
                )

            # Proceed with commit only if gitignore succeeded
            CommitThinkingHandler.handle(commit_cmd)

        # Clear accumulated thinking state
        config.last_processed_uuid = config.waiting_target_uuid
        config.waiting_for_thinking = False
        config.accumulated_thinking = []
        config.waiting_target_uuid = ""

        # Persist config
        SaveConfigHandler.handle(
            SaveConfigCommand(config=config, config_path=get_config_path())
        )

        return CommitAccumulatedThinkingResponse(
            config=config,
            gitignore_success=gitignore_success,
            commit_success=commit_success,
            error=error,
        )

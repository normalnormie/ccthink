# ABOUTME: Helper for managing git commits of thinking content
# ABOUTME: Handles commit timing, decision logic, and execution

from __future__ import annotations

from typing import TYPE_CHECKING

from src.features.config.save_config.save_config_command import SaveConfigCommand
from src.features.config.save_config.save_config_handler import SaveConfigHandler
from src.features.git_operations.commit_thinking.commit_thinking_command import (
    CommitThinkingCommand,
)
from src.features.git_operations.commit_thinking.commit_thinking_handler import (
    CommitThinkingHandler,
)
from src.features.monitoring.monitor_loop.commit_formatter import (
    format_entries_for_commit,
)
from src.shared.constants import get_config_path

if TYPE_CHECKING:
    import asyncio

    from src.shared.models import Config


def commit_accumulated_thinking(
    config: Config, *, enable_git: bool, timer_task: asyncio.Task[None] | None
) -> tuple[Config, asyncio.Task[None] | None]:
    """Commit accumulated thinking if ready.

    Args:
        config: Current configuration
        enable_git: Whether git operations are enabled
        timer_task: Current timer task if any

    Returns:
        Tuple of config and timer task after commit
    """
    if not config.waiting_for_thinking:
        return config, timer_task

    # Skip commit if both content types are disabled
    if not config.thinking_enabled and not config.chat_text_enabled:
        config.waiting_for_thinking = False
        config.accumulated_thinking = []
        config.waiting_target_uuid = ""
        SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))
        return config, timer_task

    # Content already compressed (if sonnet enabled), format for commit
    content = format_entries_for_commit(config.accumulated_thinking, config.line_max_length)

    commit_response = None
    if enable_git:
        commit_response = CommitThinkingHandler.handle(CommitThinkingCommand(message=content, simulate=config.simulate))

    # Only clear accumulated state if commit actually succeeded with content
    if commit_response and commit_response.nothing_to_commit:
        # Nothing to commit - preserve accumulated state for next commit attempt
        SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))
        return config, timer_task

    # Commit succeeded or git disabled - clear state
    config.last_processed_uuid = config.waiting_target_uuid
    config.waiting_for_thinking = False
    config.accumulated_thinking = []
    config.waiting_target_uuid = ""
    SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))

    return config, timer_task


def execute_immediate_commit(
    thinking_to_commit: list[str], config: Config, *, enable_git: bool
) -> None:
    """Execute immediate commit of thinking content.

    Args:
        thinking_to_commit: List of thinking entries to commit
        config: Current configuration
        enable_git: Whether git operations are enabled
    """
    formatted_entries = [
        "\n".join(
            format_entries_for_commit([line], config.line_max_length).split("\n\n---\n\n")[0].split("\n")
        )
        for line in thinking_to_commit
    ]
    content = "\n\n---\n\n".join(formatted_entries)

    if enable_git:
        CommitThinkingHandler.handle(CommitThinkingCommand(message=content, simulate=config.simulate))


def should_skip_commit(config: Config) -> bool:
    """Check if commit should be skipped for configuration.

    Args:
        config: Current configuration

    Returns:
        True if commit should be skipped
    """
    return not config.thinking_enabled and not config.chat_text_enabled

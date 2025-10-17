# ABOUTME: Helper for handling JSONL file switching operations
# ABOUTME: Manages branch merging and config updates during file switches

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from src.features.config.save_config.save_config_command import SaveConfigCommand
from src.features.config.save_config.save_config_handler import SaveConfigHandler
from src.features.git_operations.merge_branch.merge_branch_command import (
    MergeBranchCommand,
)
from src.features.git_operations.merge_branch.merge_branch_handler import (
    MergeBranchHandler,
)
from src.features.monitoring.monitor_loop.commit_helper import (
    commit_accumulated_thinking,
)
from src.shared.constants import get_config_path

if TYPE_CHECKING:
    import asyncio

    from src.shared.models import Config

logger = logging.getLogger(__name__)


def process_file_switch(
    config: Config,
    current_file: Path,
    *,
    enable_git: bool,
    timer_task: asyncio.Task[None] | None,
    verbose: bool,
) -> tuple[Config, asyncio.Task[None] | None]:
    """Handle switching to different JSONL file.

    Args:
        config: Current configuration
        current_file: Path to the file being switched to
        enable_git: Whether git operations are enabled
        timer_task: Current timer task if any
        verbose: Whether to log verbose output

    Returns:
        Tuple of config and timer task after file switch
    """
    if verbose:
        logger.info("Monitoring: %s", current_file)

    if config.monitored_file and enable_git:
        if config.waiting_for_thinking:
            config, timer_task = commit_accumulated_thinking(
                config, enable_git=enable_git, timer_task=timer_task
            )

        branch = Path(config.monitored_file).stem
        merge_cmd = MergeBranchCommand(
            source_branch=branch,
            target_branch=config.main_branch,
            quit_on_conflict=config.quit_on_conflict,
        )
        MergeBranchHandler.handle(merge_cmd)

    config.monitored_file = str(current_file)
    config.last_file_position = current_file.stat().st_size
    config.last_processed_uuid = ""
    config.waiting_for_thinking = False
    config.accumulated_thinking = []
    SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))

    return config, timer_task

# ABOUTME: Handler for monitor loop execution
# ABOUTME: Implements JSONL monitoring and thinking processing with Sonnet transformation

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from src.features.config.save_config.save_config_command import SaveConfigCommand
from src.features.config.save_config.save_config_handler import SaveConfigHandler
from src.features.git_operations.commit_thinking.commit_thinking_command import (
    CommitThinkingCommand,
)
from src.features.git_operations.commit_thinking.commit_thinking_handler import (
    CommitThinkingHandler,
)
from src.features.git_operations.ensure_branch.ensure_branch_command import (
    EnsureBranchCommand,
)
from src.features.git_operations.ensure_branch.ensure_branch_handler import (
    EnsureBranchHandler,
)
from src.features.monitoring.compress_entries.compress_entries_command import (
    CompressEntriesCommand,
)
from src.features.monitoring.compress_entries.compress_entries_handler import (
    CompressEntriesHandler,
)
from src.features.monitoring.find_current_jsonl.find_current_jsonl_command import (
    FindCurrentJsonlCommand,
)
from src.features.monitoring.find_current_jsonl.find_current_jsonl_handler import (
    FindCurrentJsonlHandler,
)
from src.features.monitoring.monitor_loop.commit_formatter import (
    format_entries_for_commit,
)
from src.features.monitoring.monitor_loop.commit_helper import (
    commit_accumulated_thinking,
)
from src.features.monitoring.monitor_loop.display_coordinator import DisplayCoordinator
from src.features.monitoring.monitor_loop.file_switch_helper import process_file_switch
from src.features.monitoring.monitor_loop.monitor_loop_command import (
    MonitorLoopCommand,
)
from src.features.monitoring.monitor_loop.monitor_loop_response import (
    MonitorLoopResponse,
)
from src.features.monitoring.parse_thinking.parse_thinking_command import (
    ParseThinkingCommand,
)
from src.features.monitoring.parse_thinking.parse_thinking_handler import (
    ParseThinkingHandler,
)
from src.features.processing.process_thinking.process_thinking_command import (
    ProcessThinkingCommand,
)
from src.features.processing.process_thinking.process_thinking_handler import (
    ProcessThinkingHandler,
)
from src.shared.constants import (
    DEFAULT_PROJECTS_DIR,
    FALLBACK_PROJECTS_DIR,
    THINKING_WAIT_TIMEOUT_SECONDS,
    get_config_path,
)

logger = logging.getLogger(__name__)


class MonitorLoopHandler:
    """Handler for monitor loop operations."""

    # Display coordinator manages separator logic
    _display_coordinator = DisplayCoordinator()

    @staticmethod
    def _get_claude_dir(command: MonitorLoopCommand) -> Path:
        """Get Claude project directory.

        Returns:
            Path to Claude project directory
        """
        home = Path.home()
        projects_dir = command.config.projects_dir
        if projects_dir.startswith("~/"):
            projects_dir = str(home / projects_dir[2:])

        project_name = str(Path.cwd()).replace("/", "-")
        claude_dir = Path(projects_dir) / project_name

        if command.config.projects_dir == DEFAULT_PROJECTS_DIR and not claude_dir.exists():
            fallback = home / FALLBACK_PROJECTS_DIR[2:] / project_name
            if fallback.exists():
                return fallback

        return claude_dir

    @staticmethod
    async def _commit_thinking(command: MonitorLoopCommand) -> MonitorLoopResponse:
        """Commit accumulated thinking.

        Returns:
            Response with config after commit
        """
        config, timer_task = commit_accumulated_thinking(
            command.config, enable_git=command.enable_git, timer_task=command.timer_task
        )
        return MonitorLoopResponse(config=config, timer_task=timer_task)

    @staticmethod
    async def _process_file_switch(
        command: MonitorLoopCommand, current_file: Path
    ) -> MonitorLoopResponse:
        """Handle switching to different JSONL file.

        Returns:
            Response with config after file switch
        """
        config, timer_task = process_file_switch(
            command.config,
            current_file,
            enable_git=command.enable_git,
            timer_task=command.timer_task,
            verbose=command.config.verbose,
        )
        return MonitorLoopResponse(config=config, timer_task=timer_task)

    @staticmethod
    async def handle(command: MonitorLoopCommand) -> MonitorLoopResponse:  # noqa: PLR0914
        """Execute one monitor loop iteration.

        Args:
            command: Command containing config and state

        Returns:
            Response with results
        """
        config = command.config
        timer_task = command.timer_task

        # Find current JSONL file
        claude_dir = MonitorLoopHandler._get_claude_dir(command)
        find_cmd = FindCurrentJsonlCommand(claude_project_dir=claude_dir)
        find_resp = FindCurrentJsonlHandler.handle(find_cmd)

        if not find_resp.jsonl_path:
            return MonitorLoopResponse(config=config, timer_task=timer_task, should_save_config=False)

        # Handle file switch
        if config.monitored_file != str(find_resp.jsonl_path):
            return await MonitorLoopHandler._process_file_switch(command, find_resp.jsonl_path)

        # Check for content changes
        current_size = find_resp.jsonl_path.stat().st_size
        if current_size <= config.last_file_position:
            return MonitorLoopResponse(config=config, timer_task=timer_task, should_save_config=False)

        # Parse thinking entries
        parse_cmd = ParseThinkingCommand(
            jsonl_path=find_resp.jsonl_path,
            from_position=config.last_file_position,
            config=config,
        )
        parse_resp = ParseThinkingHandler.handle(parse_cmd)
        config.last_file_position = parse_resp.end_position

        if not parse_resp.entries and not parse_resp.tool_uses:
            SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))
            return MonitorLoopResponse(config=config, timer_task=timer_task, should_save_config=False)

        # Compress all entries once if sonnet enabled (both thinking and text separately)
        compressed_thinking_map: dict[str, str] = {}
        compressed_text_map: dict[str, str] = {}
        if config.sonnet_enabled:
            compress_cmd = CompressEntriesCommand(entries=parse_resp.entries, config=config)
            compress_resp = await CompressEntriesHandler.handle(compress_cmd)
            compressed_thinking_map = compress_resp.compressed_thinking_map
            compressed_text_map = compress_resp.compressed_text_map

        # Display parsed items
        await MonitorLoopHandler._display_coordinator.display_items(
            parse_resp, config, compressed_thinking_map, compressed_text_map
        )

        if command.enable_git:
            EnsureBranchHandler.handle(EnsureBranchCommand(branch_name=find_resp.jsonl_path.stem))

        # Save accumulated state before ProcessThinkingHandler modifies it
        old_waiting = config.waiting_for_thinking
        old_accumulated = config.accumulated_thinking.copy()
        old_target_uuid = config.waiting_target_uuid

        proc_resp = ProcessThinkingHandler.handle(
            ProcessThinkingCommand(
                entries=parse_resp.entries,
                config=config,
                compressed_thinking_map=compressed_thinking_map,
                compressed_text_map=compressed_text_map,
            )
        )
        config = proc_resp.current_config

        if proc_resp.should_commit:
            # Skip commit if both content types are disabled
            if not config.thinking_enabled and not config.chat_text_enabled:
                config.last_processed_uuid = proc_resp.target_uuid
                if timer_task:
                    timer_task.cancel()
                    timer_task = None
            else:
                # Content is already compressed (if sonnet enabled), format for commit
                content = format_entries_for_commit(proc_resp.thinking_to_commit, config.line_max_length)
                commit_response = None
                if command.enable_git:
                    commit_response = CommitThinkingHandler.handle(
                        CommitThinkingCommand(message=content, simulate=config.simulate)
                    )

                # Only clear accumulated state if commit actually succeeded with content
                if commit_response and commit_response.nothing_to_commit:
                    # Nothing to commit - restore accumulated state for next commit attempt
                    config.waiting_for_thinking = old_waiting
                    config.accumulated_thinking = old_accumulated
                    config.waiting_target_uuid = old_target_uuid
                else:
                    # Commit succeeded or git disabled - clear state
                    config.last_processed_uuid = proc_resp.target_uuid
                    if timer_task:
                        timer_task.cancel()
                        timer_task = None

        # Handle timer start
        if proc_resp.should_start_timer:
            timer_task = asyncio.create_task(asyncio.sleep(THINKING_WAIT_TIMEOUT_SECONDS))
            commit_cmd = MonitorLoopCommand(
                config=config, enable_git=command.enable_git, timer_task=timer_task
            )
            commit_task = asyncio.create_task(MonitorLoopHandler._commit_thinking(commit_cmd))
            del commit_task  # Task runs independently

        SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))
        return MonitorLoopResponse(config=config, timer_task=timer_task)

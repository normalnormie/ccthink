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
from src.features.git_operations.merge_branch.merge_branch_command import (
    MergeBranchCommand,
)
from src.features.git_operations.merge_branch.merge_branch_handler import (
    MergeBranchHandler,
)
from src.features.monitoring.compress_entries.compress_entries_command import (
    CompressEntriesCommand,
)
from src.features.monitoring.compress_entries.compress_entries_handler import (
    CompressEntriesHandler,
)
from src.features.monitoring.display_item.display_item_command import DisplayItemCommand
from src.features.monitoring.display_item.display_item_handler import DisplayItemHandler
from src.features.monitoring.find_current_jsonl.find_current_jsonl_command import (
    FindCurrentJsonlCommand,
)
from src.features.monitoring.find_current_jsonl.find_current_jsonl_handler import (
    FindCurrentJsonlHandler,
)
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
from src.features.phrase_transformation.line_formatter.format_thinking_line import (
    format_thinking_line,
    strip_ansi_codes,
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

    # Track if we've shown any thinking in this session (for separator logic)
    _has_shown_thinking: bool = False

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
        config = command.config

        if not config.waiting_for_thinking:
            return MonitorLoopResponse(config=config, timer_task=command.timer_task)

        # Skip commit if both content types are disabled
        if not config.thinking_enabled and not config.text_enabled:
            config.waiting_for_thinking = False
            config.accumulated_thinking = []
            config.waiting_target_uuid = ""
            SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))
            return MonitorLoopResponse(config=config, timer_task=command.timer_task)

        # Content already compressed (if sonnet enabled), strip ANSI codes for commit
        formatted_entries = []
        for line in config.accumulated_thinking:
            clean_line = strip_ansi_codes(line)
            formatted_lines = format_thinking_line(clean_line, max_length=config.line_max_length)
            formatted_entries.append("\n".join(formatted_lines))
        content = "\n\n---\n\n".join(formatted_entries)

        if command.enable_git:
            CommitThinkingHandler.handle(CommitThinkingCommand(message=content, simulate=config.simulate))

        config.last_processed_uuid = config.waiting_target_uuid
        config.waiting_for_thinking = False
        config.accumulated_thinking = []
        config.waiting_target_uuid = ""
        SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))

        return MonitorLoopResponse(config=config, timer_task=command.timer_task)

    @staticmethod
    async def _process_file_switch(
        command: MonitorLoopCommand, current_file: Path
    ) -> MonitorLoopResponse:
        """Handle switching to different JSONL file.

        Returns:
            Response with config after file switch
        """
        config = command.config
        if config.verbose:
            logger.info("Monitoring: %s", current_file)

        if config.monitored_file and command.enable_git:
            if config.waiting_for_thinking:
                resp = await MonitorLoopHandler._commit_thinking(command)
                config = resp.config

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

        return MonitorLoopResponse(config=config, timer_task=command.timer_task)

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
        for item in parse_resp.ordered_items:
            has_thinking = item.thinking_entry is not None and item.thinking_entry.get_thinking_content() is not None
            show_separator = MonitorLoopHandler._has_shown_thinking and has_thinking

            # Get compressed content for this entry
            compressed_thinking = None
            compressed_text = None
            if item.thinking_entry:
                compressed_thinking = compressed_thinking_map.get(item.thinking_entry.parent_uuid)
                compressed_text = compressed_text_map.get(item.thinking_entry.parent_uuid)

            await DisplayItemHandler.handle(
                DisplayItemCommand(
                    item=item,
                    config=config,
                    show_separator=show_separator,
                    compressed_thinking=compressed_thinking,
                    compressed_text=compressed_text,
                )
            )
            if has_thinking:
                MonitorLoopHandler._has_shown_thinking = True

        if command.enable_git:
            EnsureBranchHandler.handle(EnsureBranchCommand(branch_name=find_resp.jsonl_path.stem))

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
            if not config.thinking_enabled and not config.text_enabled:
                config.last_processed_uuid = proc_resp.target_uuid
                if timer_task:
                    timer_task.cancel()
                    timer_task = None
            else:
                # Content is already compressed (if sonnet enabled), strip ANSI codes for commit
                formatted_entries = [
                    "\n".join(format_thinking_line(strip_ansi_codes(line), max_length=config.line_max_length))
                    for line in proc_resp.thinking_to_commit
                ]
                content = "\n\n---\n\n".join(formatted_entries)
                if command.enable_git:
                    CommitThinkingHandler.handle(
                        CommitThinkingCommand(message=content, simulate=config.simulate)
                    )
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

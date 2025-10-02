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
    format_colored_thinking_line,
    format_thinking_line,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
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

        thinking = config.accumulated_thinking
        # Apply sonnet transformation if enabled
        if config.sonnet_enabled:
            resp = await TransformThinkingHandler.handle(
                TransformThinkingCommand(thinking_lines=thinking, enable_streaming=False, enable_colors=False),
                config=config
            )
            thinking = list(resp.transformed_lines)
        # Format each entry and join entries with separator
        formatted_entries = []
        for line in thinking:
            formatted_lines = format_thinking_line(line, max_length=config.thinking_line_max_length)
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
    async def handle(command: MonitorLoopCommand) -> MonitorLoopResponse:  # noqa: C901, PLR0912, PLR0914
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
        )
        parse_resp = ParseThinkingHandler.handle(parse_cmd)
        config.last_file_position = parse_resp.end_position

        if not parse_resp.entries:
            SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))
            return MonitorLoopResponse(config=config, timer_task=timer_task)

        for entry in parse_resp.entries:
            thinking_content = entry.get_thinking_content()
            if thinking_content:
                if MonitorLoopHandler._has_shown_thinking:
                    if config.verbose:
                        for sep_line in config.thinking_separator.split("\n"):
                            logger.info("%s", sep_line)
                    else:
                        print(config.thinking_separator, end="" if config.thinking_separator.endswith("\n") else "\n")  # noqa: T201
                MonitorLoopHandler._has_shown_thinking = True

                if config.sonnet_enabled:
                    transform_resp = await TransformThinkingHandler.handle(
                        TransformThinkingCommand(
                            thinking_lines=[thinking_content],
                            enable_streaming=config.sonnet_streaming,
                            enable_colors=config.sonnet_colors
                        ),
                        config=command.config
                    )
                    for line in transform_resp.transformed_lines:
                        for formatted_line in format_colored_thinking_line(
                            line, max_length=config.thinking_line_max_length
                        ):
                            if config.verbose:
                                logger.info("%s", formatted_line)
                            else:
                                print(formatted_line)  # noqa: T201
                    for error in transform_resp.errors:
                        logger.warning("%s", error)
                else:
                    max_len = config.thinking_line_max_length
                    for formatted_line in format_thinking_line(thinking_content, max_length=max_len):
                        if config.verbose:
                            logger.info("%s", formatted_line)
                        else:
                            print(formatted_line)  # noqa: T201

        if command.enable_git:
            EnsureBranchHandler.handle(
                EnsureBranchCommand(branch_name=find_resp.jsonl_path.stem)
            )

        proc_resp = ProcessThinkingHandler.handle(ProcessThinkingCommand(entries=parse_resp.entries, config=config))
        config = proc_resp.current_config

        if proc_resp.should_commit:
            thinking_to_commit = proc_resp.thinking_to_commit

            if config.sonnet_enabled:
                transform_cmd = TransformThinkingCommand(
                    thinking_lines=thinking_to_commit,
                    enable_streaming=False,
                    enable_colors=False,
                )
                transform_resp = await TransformThinkingHandler.handle(transform_cmd, config=command.config)
                thinking_to_commit = list(transform_resp.transformed_lines)

            # Format each entry and join entries with separator
            formatted_entries = [
                "\n".join(format_thinking_line(line, max_length=config.thinking_line_max_length))
                for line in thinking_to_commit
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

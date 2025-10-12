# ABOUTME: Main application entry point for ccthink
# ABOUTME: Orchestrates monitoring, processing, and git operations

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from src.features.app.bootstrap.bootstrap_application_command import (
    BootstrapApplicationCommand,
)
from src.features.app.bootstrap.bootstrap_application_handler import (
    BootstrapApplicationHandler,
)
from src.features.cli.parse_arguments.parse_arguments_command import (
    ParseArgumentsCommand,
)
from src.features.cli.parse_arguments.parse_arguments_handler import (
    ParseArgumentsHandler,
)
from src.features.config.save_config.save_config_command import SaveConfigCommand
from src.features.config.save_config.save_config_handler import SaveConfigHandler
from src.features.git_operations.commit_thinking.commit_thinking_command import (
    CommitThinkingCommand,
)
from src.features.git_operations.commit_thinking.commit_thinking_handler import (
    CommitThinkingHandler,
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
from src.features.monitoring.monitor_loop.monitor_loop_command import (
    MonitorLoopCommand,
)
from src.features.monitoring.monitor_loop.monitor_loop_handler import (
    MonitorLoopHandler,
)
from src.shared.constants import (
    ASCII_LOGO,
    DEFAULT_PROJECTS_DIR,
    FALLBACK_PROJECTS_DIR,
    GITIGNORE_ENTRIES,
    get_config_path,
)

if TYPE_CHECKING:
    from src.shared.models import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

enable_git = False
config: Config | None = None
shutdown_event = asyncio.Event()
timer_task: asyncio.Task[None] | None = None


async def commit_thinking(cfg: Config) -> None:  # noqa: RUF029
    """Commit accumulated thinking."""
    global config
    config = cfg

    if not config.waiting_for_thinking:
        return

    content = "\n\n---\n\n".join(config.accumulated_thinking)
    cmd = CommitThinkingCommand(message=content, simulate=config.simulate)

    if enable_git:
        # Ensure ccthink.conf is in .gitignore before committing
        EnsureGitignoreHandler.handle(
            EnsureGitignoreCommand(
                entries=GITIGNORE_ENTRIES,
                gitignore_path=Path.cwd() / ".gitignore",
            )
        )
        CommitThinkingHandler.handle(cmd)

    config.last_processed_uuid = config.waiting_target_uuid
    config.waiting_for_thinking = False
    config.accumulated_thinking = []
    config.waiting_target_uuid = ""
    SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))


def get_claude_dir() -> Path:
    """Get Claude project directory."""
    if config is None:
        msg = "Config not initialized"
        raise RuntimeError(msg)

    home = Path.home()
    projects_dir = config.projects_dir
    if projects_dir.startswith("~/"):
        projects_dir = str(home / projects_dir[2:])

    project_name = str(Path.cwd()).replace("/", "-")
    claude_dir = Path(projects_dir) / project_name

    if config.projects_dir == DEFAULT_PROJECTS_DIR and not claude_dir.exists():
        fallback = home / FALLBACK_PROJECTS_DIR[2:] / project_name
        if fallback.exists():
            return fallback

    return claude_dir


def ensure_gitignore_and_merge(
    source_branch: str, target_branch: str, quit_on_conflict: bool, verbose: bool, context: str = ""
) -> None:
    """Ensure .gitignore is configured and merge branch."""
    EnsureGitignoreHandler.handle(
        EnsureGitignoreCommand(entries=GITIGNORE_ENTRIES, gitignore_path=Path.cwd() / ".gitignore")
    )
    response = MergeBranchHandler.handle(
        MergeBranchCommand(
            source_branch=source_branch,
            target_branch=target_branch,
            quit_on_conflict=quit_on_conflict,
        )
    )
    ctx = f" {context}" if context else ""
    if response.had_conflict and quit_on_conflict:
        logger.error("Merge conflict%s: %s", ctx, response.error)
        sys.exit(1)
    elif not response.success:
        logger.error("Merge failed%s: %s", ctx, response.error)
    elif verbose:
        logger.info("Merge %s -> %s", source_branch, target_branch)


async def process_file_switch(current_file: Path) -> None:
    """Handle switching to different JSONL file."""
    if config is None:
        return

    if config.verbose:
        logger.info("Monitoring: %s", current_file)

    if config.monitored_file and enable_git:
        if config.waiting_for_thinking:
            await commit_thinking(config)

        branch = Path(config.monitored_file).stem
        ensure_gitignore_and_merge(
            source_branch=branch,
            target_branch=config.main_branch,
            quit_on_conflict=config.quit_on_conflict,
            verbose=config.verbose,
            context="during file switch",
        )

    config.monitored_file = str(current_file)
    config.last_file_position = current_file.stat().st_size
    config.last_processed_uuid = ""
    config.waiting_for_thinking = False
    config.accumulated_thinking = []
    SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))


async def monitor() -> None:
    """Monitor JSONL and process thinking."""
    global config, timer_task

    if config is None:
        return

    cmd = MonitorLoopCommand(config=config, enable_git=enable_git, timer_task=timer_task)
    resp = await MonitorLoopHandler.handle(cmd)
    config = resp.config
    timer_task = resp.timer_task


async def main_loop() -> None:
    """Main monitoring loop."""
    if config is None:
        return

    while not shutdown_event.is_set():
        try:
            await monitor()
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=config.poll_interval_seconds)
            break
        except TimeoutError:
            continue


async def shutdown() -> None:
    """Graceful shutdown."""
    global config

    logger.info("Shutting down...")

    if config and enable_git:
        if config.waiting_for_thinking:
            await commit_thinking(config)

        if config.monitored_file:
            branch = Path(config.monitored_file).stem
            if branch != config.main_branch:
                ensure_gitignore_and_merge(
                    source_branch=branch,
                    target_branch=config.main_branch,
                    quit_on_conflict=config.quit_on_conflict,
                    verbose=config.verbose,
                )

    if config:
        SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=get_config_path()))


def main() -> None:
    """Entry point."""
    global enable_git, config

    # Parse CLI arguments
    parse_cmd = ParseArgumentsCommand()
    parse_resp = ParseArgumentsHandler.handle(parse_cmd)

    # Bootstrap application
    bootstrap_cmd = BootstrapApplicationCommand(
        config_path=get_config_path(),
        enable_commit=parse_resp.enable_commit, disable_commit=parse_resp.disable_commit,
        enable_sonnet=parse_resp.enable_sonnet, disable_sonnet=parse_resp.disable_sonnet,
        enable_streaming=parse_resp.enable_streaming, disable_streaming=parse_resp.disable_streaming,
        enable_colors=parse_resp.enable_colors, disable_colors=parse_resp.disable_colors,
        enable_chat_text=parse_resp.enable_chat_text, disable_chat_text=parse_resp.disable_chat_text,
        enable_verbose=parse_resp.enable_verbose, disable_verbose=parse_resp.disable_verbose,
        enable_simulate=parse_resp.enable_simulate, disable_simulate=parse_resp.disable_simulate,
    )
    bootstrap_resp = BootstrapApplicationHandler.handle(
        bootstrap_cmd, shutdown_event_setter=shutdown_event.set
    )
    config = bootstrap_resp.config

    # Use commit_enabled from config (persisted state)
    enable_git = config.commit_enabled

    # Validate main_branch exists if git operations are enabled
    if enable_git:
        branch_exists = MergeBranchHandler.branch_exists(config.main_branch)
        if not branch_exists:
            logger.warning("Configured main_branch '%s' does not exist in git repository", config.main_branch)
            # Check for common main/master confusion
            alternative = "main" if config.main_branch == "master" else "master"
            if MergeBranchHandler.branch_exists(alternative):
                logger.warning(
                    "Branch '%s' exists but you configured '%s' - consider updating main_branch",
                    alternative, config.main_branch
                )

    print(ASCII_LOGO)  # noqa: T201
    # Build feature lists grouped by state
    all_features = [
        ("commit", enable_git), ("sonnet", config.sonnet_enabled),
        ("colors", config.sonnet_colors), ("chat_text", config.chat_text_enabled),
        ("verbose", config.verbose), ("simulate", config.simulate),
        ("streaming", config.sonnet_streaming),
    ]
    active = [name for name, enabled in all_features if enabled]
    active.append(f"poll: {config.poll_interval_seconds}s")
    inactive = [name for name, enabled in all_features if not enabled]

    logger.info("ccthink started")
    logger.info("  Active: %s", ", ".join(active))
    logger.info("  Inactive: %s", ", ".join(inactive))

    try:
        asyncio.run(main_loop())
    finally:
        asyncio.run(shutdown())


if __name__ == "__main__":
    main()

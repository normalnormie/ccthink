# ABOUTME: Main application entry point for ccthink
# ABOUTME: Orchestrates monitoring, processing, and git operations

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from src.features.app.bootstrap.bootstrap_application_command import (
    BootstrapApplicationCommand,
)
from src.features.app.bootstrap.bootstrap_application_handler import (
    BootstrapApplicationHandler,
)
from src.features.app.graceful_exit.graceful_exit_command import GracefulExitCommand
from src.features.app.graceful_exit.graceful_exit_handler import GracefulExitHandler
from src.features.cli.parse_arguments.parse_arguments_command import (
    ParseArgumentsCommand,
)
from src.features.cli.parse_arguments.parse_arguments_handler import (
    ParseArgumentsHandler,
)
from src.features.git_operations.merge_branch.merge_branch_handler import (
    MergeBranchHandler,
)
from src.features.monitoring.monitor_loop.monitor_loop_command import (
    MonitorLoopCommand,
)
from src.features.monitoring.monitor_loop.monitor_loop_handler import (
    MonitorLoopHandler,
)
from src.shared.constants import ASCII_LOGO, get_config_path

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


async def monitor() -> None:
    """Monitor JSONL and process thinking."""
    global config, timer_task  # noqa: PLW0603

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
        except Exception:
            logger.exception("Error in monitoring loop")

        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=config.poll_interval_seconds)
            break
        except TimeoutError:
            continue


async def shutdown() -> None:
    """Graceful shutdown."""
    await GracefulExitHandler.handle(
        GracefulExitCommand(config=config, enable_git=enable_git)
    )


def main() -> None:
    """Entry point."""
    global enable_git, config  # noqa: PLW0603

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
        ("colors", config.colors), ("chat_text", config.chat_text_enabled),
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

# ABOUTME: Handler for bootstrapping application
# ABOUTME: Implements application initialization including config, gitignore, and signals

from __future__ import annotations

import logging
import signal
from collections.abc import Callable  # noqa: TC003
from pathlib import Path
from typing import TYPE_CHECKING

from src.features.app.bootstrap.bootstrap_application_command import (
    BootstrapApplicationCommand,  # noqa: TC001
)
from src.features.app.bootstrap.bootstrap_application_response import (
    BootstrapApplicationResponse,
)
from src.features.config.load_config.load_config_command import LoadConfigCommand
from src.features.config.load_config.load_config_handler import LoadConfigHandler
from src.features.config.save_config.save_config_command import SaveConfigCommand
from src.features.config.save_config.save_config_handler import SaveConfigHandler
from src.features.gitignore.ensure_gitignore.ensure_gitignore_command import (
    EnsureGitignoreCommand,
)
from src.features.gitignore.ensure_gitignore.ensure_gitignore_handler import (
    EnsureGitignoreHandler,
)
from src.shared.constants import GITIGNORE_ENTRIES

if TYPE_CHECKING:
    from src.shared.models import Config

logger = logging.getLogger(__name__)


class BootstrapApplicationHandler:
    """Handler for application bootstrap operations."""

    @staticmethod
    def _apply_cli_overrides(  # noqa: C901
        config: Config, command: BootstrapApplicationCommand
    ) -> bool:
        """Apply CLI argument overrides to config.

        Args:
            config: Configuration to update
            command: Command containing CLI overrides

        Returns:
            True if config has changes, False otherwise
        """
        config_has_changes = False

        if command.enable_commit:
            config.commit_enabled = True
            config_has_changes = True
        elif command.disable_commit:
            config.commit_enabled = False
            config_has_changes = True

        if command.enable_sonnet:
            config.sonnet_enabled = True
            config.claude_agent.model = "sonnet"
            config_has_changes = True
        elif command.disable_sonnet:
            config.sonnet_enabled = False
            config_has_changes = True

        if command.enable_haiku:
            config.sonnet_enabled = True
            config.claude_agent.model = "haiku"
            config_has_changes = True
        elif command.disable_haiku:
            config.sonnet_enabled = False
            config_has_changes = True

        if command.enable_streaming:
            config.sonnet_streaming = True
            config_has_changes = True
        elif command.disable_streaming:
            config.sonnet_streaming = False
            config_has_changes = True

        if command.enable_colors:
            config.colors = True
            config_has_changes = True
        elif command.disable_colors:
            config.colors = False
            config_has_changes = True

        if command.enable_chat_text:
            config.chat_text_enabled = True
            config_has_changes = True
        elif command.disable_chat_text:
            config.chat_text_enabled = False
            config_has_changes = True

        if command.enable_verbose:
            config.verbose = True
            config_has_changes = True
        elif command.disable_verbose:
            config.verbose = False
            config_has_changes = True

        if command.enable_simulate:
            config.simulate = True
            config_has_changes = True
        elif command.disable_simulate:
            config.simulate = False
            config_has_changes = True

        return config_has_changes

    @staticmethod
    def _setup_signal_handlers(shutdown_event_setter: Callable[[], None]) -> None:
        """Setup signal handlers for graceful shutdown.

        Args:
            shutdown_event_setter: Callback to set shutdown event
        """
        def signal_handler(signum: int, frame: object) -> None:
            """Handle shutdown signals."""
            shutdown_event_setter()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, "SIGHUP"):  # Unix only
            signal.signal(signal.SIGHUP, signal_handler)

    @staticmethod
    def handle(
        command: BootstrapApplicationCommand,
        shutdown_event_setter: Callable[[], None],
    ) -> BootstrapApplicationResponse:
        """Bootstrap the application.

        Args:
            command: Command containing bootstrap parameters
            shutdown_event_setter: Callback to set shutdown event

        Returns:
            Response containing initialized config
        """
        # Load configuration
        load_resp = LoadConfigHandler.handle(
            LoadConfigCommand(config_path=command.config_path)
        )
        config = load_resp.config

        # Apply CLI overrides to config and persist them
        config_has_changes = BootstrapApplicationHandler._apply_cli_overrides(
            config, command
        )

        if config_has_changes:
            SaveConfigHandler.handle(
                SaveConfigCommand(config=config, config_path=command.config_path)
            )

        # Ensure .gitignore entries
        gitignore_response = EnsureGitignoreHandler.handle(
            EnsureGitignoreCommand(
                entries=GITIGNORE_ENTRIES,
                gitignore_path=Path.cwd() / ".gitignore",
            )
        )

        if not gitignore_response.success:
            logger.warning(
                "Failed to add ccthink.conf to .gitignore: %s",
                gitignore_response.error,
            )

        # Setup signal handlers
        BootstrapApplicationHandler._setup_signal_handlers(shutdown_event_setter)

        return BootstrapApplicationResponse(config=config)

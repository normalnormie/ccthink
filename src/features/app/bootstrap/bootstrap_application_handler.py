# ABOUTME: Handler for bootstrapping application
# ABOUTME: Implements application initialization including config, gitignore, and signals

from __future__ import annotations

import signal
from collections.abc import Callable  # noqa: TC003
from pathlib import Path

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


class BootstrapApplicationHandler:
    """Handler for application bootstrap operations."""

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
        config_modified = False

        if command.enable_commit:
            config.commit_enabled = True
            config_modified = True
        elif command.disable_commit:
            config.commit_enabled = False
            config_modified = True

        if command.enable_sonnet:
            config.sonnet_enabled = True
            config_modified = True
        elif command.disable_sonnet:
            config.sonnet_enabled = False
            config_modified = True

        if command.enable_streaming:
            config.sonnet_streaming = True
            config_modified = True
        elif command.disable_streaming:
            config.sonnet_streaming = False
            config_modified = True

        if command.enable_colors:
            config.colors = True
            config_modified = True
        elif command.disable_colors:
            config.colors = False
            config_modified = True

        if command.enable_chat_text:
            config.chat_text_enabled = True
            config_modified = True
        elif command.disable_chat_text:
            config.chat_text_enabled = False
            config_modified = True

        if command.enable_verbose:
            config.verbose = True
            config_modified = True
        elif command.disable_verbose:
            config.verbose = False
            config_modified = True

        if command.enable_simulate:
            config.simulate = True
            config_modified = True
        elif command.disable_simulate:
            config.simulate = False
            config_modified = True

        # Persist config if CLI args override settings
        if config_modified:
            SaveConfigHandler.handle(SaveConfigCommand(config=config, config_path=command.config_path))

        # Ensure .gitignore entries
        EnsureGitignoreHandler.handle(
            EnsureGitignoreCommand(
                entries=GITIGNORE_ENTRIES,
                gitignore_path=Path.cwd() / ".gitignore",
            )
        )

        # Setup signal handlers
        def signal_handler(signum: int, frame: object) -> None:
            """Handle shutdown signals."""
            shutdown_event_setter()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, "SIGHUP"):  # Unix only
            signal.signal(signal.SIGHUP, signal_handler)

        return BootstrapApplicationResponse(config=config)

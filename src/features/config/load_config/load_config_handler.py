# ABOUTME: Load config handler implementation
# ABOUTME: Handles loading configuration from disk with error handling

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.shared.models import Config

if TYPE_CHECKING:
    from src.features.config.load_config.load_config_command import LoadConfigCommand


@dataclass
class LoadConfigResponse:
    """Response from loading configuration.

    Attributes:
        config: Loaded configuration instance.
        was_created: Whether config file was created during load.
    """

    config: Config
    was_created: bool


class LoadConfigHandler:
    """Handler for loading configuration from disk."""

    @staticmethod
    def handle(command: LoadConfigCommand) -> LoadConfigResponse:
        """Load configuration from file.

        Args:
            command: Load config command with file path.

        Returns:
            Load config response with config and creation status.
        """
        was_created = not command.config_path.exists()
        config = Config.load_from_file(command.config_path)

        # Save default config if it was just created
        if was_created:
            config.save_to_file(command.config_path)

        return LoadConfigResponse(config=config, was_created=was_created)

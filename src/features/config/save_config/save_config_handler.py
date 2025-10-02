# ABOUTME: Save config handler implementation
# ABOUTME: Handles saving configuration to disk with error handling

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.features.config.save_config.save_config_command import SaveConfigCommand


@dataclass
class SaveConfigResponse:
    """Response from saving configuration.

    Attributes:
        success: Whether the save operation succeeded.
    """

    success: bool


class SaveConfigHandler:
    """Handler for saving configuration to disk."""

    @staticmethod
    def handle(command: SaveConfigCommand) -> SaveConfigResponse:
        """Save configuration to file.

        Args:
            command: Save config command with config and file path.

        Returns:
            Save config response with success status.
        """
        try:
            command.config.save_to_file(command.config_path)
            return SaveConfigResponse(success=True)
        except (OSError, ValueError):
            return SaveConfigResponse(success=False)

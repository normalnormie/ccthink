# ABOUTME: Save config command definition
# ABOUTME: Defines the command to save configuration to disk

from dataclasses import dataclass
from pathlib import Path

from src.shared.models import Config


@dataclass
class SaveConfigCommand:
    """Command to save configuration to file.

    Attributes:
        config: Configuration to save.
        config_path: Path to the configuration file.
    """

    config: Config
    config_path: Path

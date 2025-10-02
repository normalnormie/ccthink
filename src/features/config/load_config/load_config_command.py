# ABOUTME: Load config command definition
# ABOUTME: Defines the command to load configuration from disk

from dataclasses import dataclass
from pathlib import Path


@dataclass
class LoadConfigCommand:
    """Command to load configuration from file.

    Attributes:
        config_path: Path to the configuration file.
    """

    config_path: Path

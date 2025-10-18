# ABOUTME: Command for processing JSONL file switch operations
# ABOUTME: Contains file path and config for file switching

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from src.shared.models import Config


@dataclass
class ProcessFileSwitchCommand:
    """Command to process file switch operation."""

    current_file: Path
    config: Config
    enable_git: bool

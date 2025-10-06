# ABOUTME: Command definition for compressing thinking entries
# ABOUTME: Contains entries list and configuration for compression operations

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.models import Config, ThinkingEntry


@dataclass
class CompressEntriesCommand:
    """Command to compress thinking and text entries.

    Attributes:
        entries: List of thinking entries to compress.
        config: Application configuration containing compression settings.
    """

    entries: list[ThinkingEntry]
    config: Config

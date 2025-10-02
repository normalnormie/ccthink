# ABOUTME: Command dataclass for thinking transformation requests
# ABOUTME: Contains thinking lines and configuration for compression and display

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class TransformThinkingCommand:
    """Command for transforming thinking entries."""

    thinking_lines: Sequence[str]
    """Thinking lines to transform."""

    enable_streaming: bool = True
    """Enable streaming display of compression."""

    enable_colors: bool = True
    """Enable colored output."""

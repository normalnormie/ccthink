# ABOUTME: Response dataclass for thinking transformation results
# ABOUTME: Contains compressed lines, colors, success status, and fallback data

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class TransformThinkingResponse:
    """Response from thinking transformation."""

    transformed_lines: Sequence[str]
    """Compressed thinking lines, or original lines on failure."""

    colors: Sequence[int]
    """ANSI 256 color codes for each line. Empty on failure."""

    success: bool
    """Whether transformation succeeded for all lines."""

    errors: Sequence[str]
    """Error messages encountered during transformation."""

    original_lines: Sequence[str]
    """Original thinking lines preserved for fallback."""

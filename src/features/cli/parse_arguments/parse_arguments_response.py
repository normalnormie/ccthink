# ABOUTME: Response from parsing CLI arguments
# ABOUTME: Contains parsed argument values in structured format

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParseArgumentsResponse:
    """Response containing parsed CLI arguments.

    Attributes:
        enable_commit: Enable git commit operations (None if not specified)
        disable_commit: Disable git commit operations (None if not specified)
        enable_sonnet: Enable Sonnet phrase transformation (None if not specified)
        disable_sonnet: Disable Sonnet phrase transformation (None if not specified)
        enable_streaming: Enable streaming output (None if not specified)
        disable_streaming: Disable streaming output (None if not specified)
        enable_colors: Enable colored output (None if not specified)
        disable_colors: Disable colored output (None if not specified)
        enable_verbose: Enable verbose logging (None if not specified)
        disable_verbose: Disable verbose logging (None if not specified)
        enable_simulate: Enable simulate/dry-run mode (None if not specified)
        disable_simulate: Disable simulate/dry-run mode (None if not specified)
    """

    enable_commit: bool | None
    disable_commit: bool | None
    enable_sonnet: bool | None
    disable_sonnet: bool | None
    enable_streaming: bool | None
    disable_streaming: bool | None
    enable_colors: bool | None
    disable_colors: bool | None
    enable_verbose: bool | None
    disable_verbose: bool | None
    enable_simulate: bool | None
    disable_simulate: bool | None

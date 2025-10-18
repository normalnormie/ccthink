# ABOUTME: Command for bootstrapping application
# ABOUTME: Defines input parameters for application initialization

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path  # noqa: TC003


@dataclass
class BootstrapApplicationCommand:
    """Command to bootstrap the application.

    Attributes:
        config_path: Path to configuration file
        enable_commit: Enable git commit operations (None if not specified)
        disable_commit: Disable git commit operations (None if not specified)
        enable_sonnet: Enable Sonnet transformation (None if not specified)
        disable_sonnet: Disable Sonnet transformation (None if not specified)
        enable_haiku: Enable Haiku transformation (None if not specified)
        disable_haiku: Disable Haiku transformation (None if not specified)
        enable_streaming: Enable streaming output (None if not specified)
        disable_streaming: Disable streaming output (None if not specified)
        enable_colors: Enable colored output (None if not specified)
        disable_colors: Disable colored output (None if not specified)
        enable_chat_text: Enable chat text extraction (None if not specified)
        disable_chat_text: Disable chat text extraction (None if not specified)
        enable_verbose: Enable verbose logging (None if not specified)
        disable_verbose: Disable verbose logging (None if not specified)
        enable_simulate: Enable simulate/dry-run mode (None if not specified)
        disable_simulate: Disable simulate/dry-run mode (None if not specified)
    """

    config_path: Path
    enable_commit: bool | None = None
    disable_commit: bool | None = None
    enable_sonnet: bool | None = None
    disable_sonnet: bool | None = None
    enable_haiku: bool | None = None
    disable_haiku: bool | None = None
    enable_streaming: bool | None = None
    disable_streaming: bool | None = None
    enable_colors: bool | None = None
    disable_colors: bool | None = None
    enable_chat_text: bool | None = None
    disable_chat_text: bool | None = None
    enable_verbose: bool | None = None
    disable_verbose: bool | None = None
    enable_simulate: bool | None = None
    disable_simulate: bool | None = None

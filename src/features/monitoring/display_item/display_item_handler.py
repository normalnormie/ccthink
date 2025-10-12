# ABOUTME: Display item handler implementation
# ABOUTME: Handles display of thinking entries and tool uses with formatting

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from src.features.phrase_transformation.colored_output.colored_formatter import ColoredFormatter
from src.features.phrase_transformation.line_formatter.format_thinking_line import (
    format_colored_thinking_line,
    format_thinking_line,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)
from src.shared.color_converter import ColorConverter

if TYPE_CHECKING:
    from src.features.monitoring.display_item.display_item_command import DisplayItemCommand
    from src.shared.models import Config

logger = logging.getLogger(__name__)


def _has_ansi_color_codes(text: str) -> bool:
    """Check if text contains ANSI color codes.

    Args:
        text: Text to check for ANSI color sequences.

    Returns:
        True if text contains ANSI 256 color codes, False otherwise.
    """
    ansi_pattern = r"\x1b\[38;5;\d+m"
    return bool(re.search(ansi_pattern, text))


def _get_configured_color(config: Config, content_type: str) -> int:
    """Get ANSI 256 color code for content type from config.

    Args:
        config: Application configuration.
        content_type: Type of content ('thinking' or 'text').

    Returns:
        ANSI 256 color code (0-255).
    """
    try:
        if content_type == "thinking":
            return ColorConverter.css_to_ansi256(config.thinking_color)
        else:  # "text"
            return ColorConverter.css_to_ansi256(config.chat_text_color)
    except ValueError:
        logger.warning("Invalid color config for %s, using default white", content_type)
        return 37  # Default white color


class DisplayItemHandler:
    """Handler for displaying parsed items."""

    @staticmethod
    async def handle(command: DisplayItemCommand) -> None:
        """Display a parsed item (thinking entry or tool use).

        Args:
            command: Display command with item and configuration.
        """
        config = command.config
        item = command.item

        # Display tool use if this is a tool use item
        if item.tool_use and config.tool_uses:
            tool_display = item.tool_use.format_tool_display()
            if config.verbose:
                logger.info("%s", tool_display)
            else:
                print(tool_display)  # noqa: T201
            return

        # Display thinking entry if this is a thinking item
        if not item.thinking_entry:
            return

        # Show separator if requested
        if command.show_separator:
            if config.verbose:
                for sep_line in config.separator.split("\n"):
                    logger.info("%s", sep_line)
            else:
                separator_end = "" if config.separator.endswith("\n") else "\n"
                print(config.separator, end=separator_end)  # noqa: T201

        # Display thinking content if enabled
        thinking_displayed = False
        if config.thinking_enabled:
            thinking_content = item.thinking_entry.get_thinking_content()
            if thinking_content:
                await DisplayItemHandler._display_content(
                    content=thinking_content,
                    compressed_content=command.compressed_thinking,
                    config=config,
                    content_type="thinking",
                )
                thinking_displayed = True

        # Display text content if enabled
        if config.chat_text_enabled:
            text_content = item.thinking_entry.get_text_content()
            if text_content:
                # Show separator if both thinking and text are displayed
                if thinking_displayed:
                    if config.verbose:
                        for sep_line in config.separator.split("\n"):
                            logger.info("%s", sep_line)
                    else:
                        separator_end = "" if config.separator.endswith("\n") else "\n"
                        print(config.separator, end=separator_end)  # noqa: T201

                await DisplayItemHandler._display_content(
                    content=text_content,
                    compressed_content=command.compressed_text,
                    config=config,
                    content_type="text",
                )

    @staticmethod
    async def _display_content(
        content: str,
        compressed_content: str | None,
        config: Config,
        content_type: str,
    ) -> None:
        """Display content with optional Sonnet transformation and color application.

        Args:
            content: Raw content to display.
            compressed_content: Pre-compressed content if available.
            config: Application configuration.
            content_type: Type of content ('thinking' or 'text').
        """
        # Display with Sonnet transformation if enabled
        if config.sonnet_enabled:
            # Use pre-compressed content if available, otherwise compress now
            if compressed_content:
                transformed_lines = [compressed_content]
                errors = []
            else:
                transform_resp = await TransformThinkingHandler.handle(
                    TransformThinkingCommand(
                        thinking_lines=[content],
                        enable_streaming=config.sonnet_streaming,
                        enable_colors=config.colors,
                    ),
                    config=config,
                )
                transformed_lines = transform_resp.transformed_lines
                errors = transform_resp.errors

            # Check if compressed content has color, apply configured color if not
            final_lines = []
            for line in transformed_lines:
                if config.colors and not _has_ansi_color_codes(line):
                    # Compression returned no color, apply configured color
                    color_code = _get_configured_color(config, content_type)
                    formatter = ColoredFormatter(enable_colors=config.colors)
                    colored_line = formatter.format(line, color_code)
                    final_lines.append(colored_line)
                else:
                    final_lines.append(line)

            for line in final_lines:
                for formatted_line in format_colored_thinking_line(
                    line, max_length=config.line_max_length
                ):
                    if config.verbose:
                        logger.info("%s", formatted_line)
                    else:
                        print(formatted_line)  # noqa: T201
            for error in errors:
                logger.warning("%s", error)
        else:
            # Sonnet disabled: apply configured colors to raw content if colors enabled
            if config.colors:
                color_code = _get_configured_color(config, content_type)
                formatter = ColoredFormatter(enable_colors=config.colors)
                display_content = formatter.format(content, color_code)
            else:
                display_content = content

            max_len = config.line_max_length
            for formatted_line in format_thinking_line(display_content, max_length=max_len):
                if config.verbose:
                    logger.info("%s", formatted_line)
                else:
                    print(formatted_line)  # noqa: T201

# ABOUTME: Display item handler implementation
# ABOUTME: Handles display of thinking entries and tool uses with formatting

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from src.features.monitoring.display_item.display_item_command import DisplayItemCommand
    from src.shared.models import Config

logger = logging.getLogger(__name__)


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
                )
                thinking_displayed = True

        # Display text content if enabled
        if config.text_enabled:
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
                )

    @staticmethod
    async def _display_content(
        content: str,
        compressed_content: str | None,
        config: Config,
    ) -> None:
        """Display content with optional Sonnet transformation.

        Args:
            content: Raw content to display.
            compressed_content: Pre-compressed content if available.
            config: Application configuration.
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
                        enable_colors=config.sonnet_colors,
                    ),
                    config=config,
                )
                transformed_lines = transform_resp.transformed_lines
                errors = transform_resp.errors

            for line in transformed_lines:
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
            # Display without transformation
            max_len = config.line_max_length
            for formatted_line in format_thinking_line(content, max_length=max_len):
                if config.verbose:
                    logger.info("%s", formatted_line)
                else:
                    print(formatted_line)  # noqa: T201

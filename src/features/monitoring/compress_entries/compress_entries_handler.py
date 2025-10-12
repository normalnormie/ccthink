# ABOUTME: Handler for compressing thinking entries
# ABOUTME: Compresses both thinking and text content separately when enabled

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.features.monitoring.compress_entries.compress_entries_response import (
    CompressEntriesResponse,
)
from src.features.phrase_transformation.colored_output.colored_formatter import ColoredFormatter
from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)
from src.shared.color_converter import ColorConverter

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.features.monitoring.compress_entries.compress_entries_command import (
        CompressEntriesCommand,
    )
    from src.shared.models import Config


def _get_configured_color_code(config: Config, content_type: str) -> int:
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


class CompressEntriesHandler:
    """Handler for compressing thinking and text entries separately."""

    @staticmethod
    async def handle(command: CompressEntriesCommand) -> CompressEntriesResponse:
        """Compress thinking and text content from entries.

        Loops through all entries and compresses:
        - Thinking content if config.thinking_enabled
        - Text content if config.chat_text_enabled

        Both can be compressed for the same entry if both are enabled.

        Args:
            command: Compress entries command with entries and config.

        Returns:
            Response with separate compressed maps for thinking and text.
        """
        config = command.config
        compressed_thinking_map: dict[str, str] = {}
        compressed_text_map: dict[str, str] = {}

        for entry in command.entries:
            # Compress thinking content if enabled
            if config.thinking_enabled:
                thinking_content = entry.get_thinking_content()
                if thinking_content:
                    compressed_thinking = await CompressEntriesHandler._compress_content(
                        content=thinking_content, config=config, content_type="thinking"
                    )
                    if compressed_thinking:
                        compressed_thinking_map[entry.parent_uuid] = compressed_thinking

            # Compress text content if enabled
            if config.chat_text_enabled:
                text_content = entry.get_text_content()
                if text_content:
                    compressed_text = await CompressEntriesHandler._compress_content(
                        content=text_content, config=config, content_type="text"
                    )
                    if compressed_text:
                        compressed_text_map[entry.parent_uuid] = compressed_text

        return CompressEntriesResponse(
            compressed_thinking_map=compressed_thinking_map,
            compressed_text_map=compressed_text_map,
        )

    @staticmethod
    async def _compress_content(content: str, config: Config, content_type: str) -> str | None:
        """Compress a single content string using Sonnet transformation.

        If compression fails, applies configured color as fallback if colors is enabled.

        Args:
            content: Content to compress.
            config: Application configuration.
            content_type: Type of content ('thinking' or 'text').

        Returns:
            Compressed content string or fallback colored content, None if both fail.
        """
        cmd = TransformThinkingCommand(
            thinking_lines=[content],
            enable_streaming=config.sonnet_streaming,
            enable_colors=config.colors,
        )
        resp = await TransformThinkingHandler.handle(cmd, config=config)

        if resp.transformed_lines and resp.transformed_lines[0]:
            return str(resp.transformed_lines[0])

        # Compression failed, apply configured color if colors enabled
        if config.colors:
            logger.warning("Compression failed for %s content, using configured color fallback", content_type)
            color_code = _get_configured_color_code(config, content_type)
            formatter = ColoredFormatter(enable_colors=config.colors)
            colored_content: str = formatter.format(content, color_code)
            return colored_content

        return None

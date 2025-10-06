# ABOUTME: Handler for compressing thinking entries
# ABOUTME: Compresses both thinking and text content separately when enabled

from __future__ import annotations

from typing import TYPE_CHECKING

from src.features.monitoring.compress_entries.compress_entries_response import (
    CompressEntriesResponse,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)

if TYPE_CHECKING:
    from src.features.monitoring.compress_entries.compress_entries_command import (
        CompressEntriesCommand,
    )
    from src.shared.models import Config


class CompressEntriesHandler:
    """Handler for compressing thinking and text entries separately."""

    @staticmethod
    async def handle(command: CompressEntriesCommand) -> CompressEntriesResponse:
        """Compress thinking and text content from entries.

        Loops through all entries and compresses:
        - Thinking content if config.thinking_enabled
        - Text content if config.text_enabled

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
                        content=thinking_content, config=config
                    )
                    if compressed_thinking:
                        compressed_thinking_map[entry.parent_uuid] = compressed_thinking

            # Compress text content if enabled
            if config.text_enabled:
                text_content = entry.get_text_content()
                if text_content:
                    compressed_text = await CompressEntriesHandler._compress_content(
                        content=text_content, config=config
                    )
                    if compressed_text:
                        compressed_text_map[entry.parent_uuid] = compressed_text

        return CompressEntriesResponse(
            compressed_thinking_map=compressed_thinking_map,
            compressed_text_map=compressed_text_map,
        )

    @staticmethod
    async def _compress_content(content: str, config: Config) -> str | None:
        """Compress a single content string using Sonnet transformation.

        Args:
            content: Content to compress.
            config: Application configuration.

        Returns:
            Compressed content string or None if compression failed.
        """
        cmd = TransformThinkingCommand(
            thinking_lines=[content],
            enable_streaming=config.sonnet_streaming,
            enable_colors=config.sonnet_colors,
        )
        resp = await TransformThinkingHandler.handle(cmd, config=config)

        if resp.transformed_lines:
            return resp.transformed_lines[0]

        return None

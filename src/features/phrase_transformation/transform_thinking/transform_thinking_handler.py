# ABOUTME: Handler for transforming thinking entries using compression service
# ABOUTME: Orchestrates batch compression, colored formatting, and error handling

import asyncio
import logging
import re

from src.features.phrase_transformation.colored_output.colored_formatter import ColoredFormatter
from src.features.phrase_transformation.compress_phrase.compress_phrase_service import (
    CompressPhraseService,
)
from src.features.phrase_transformation.compress_phrase.compression_options import CompressionOptions
from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_response import (
    TransformThinkingResponse,
)
from src.shared.models import Config

logger = logging.getLogger(__name__)


def safe_int_color(value: str | int, default: int = 37) -> int:
    """Safely convert color value to integer with fallback.

    Args:
        value: Color value (may be int, string, or contain ANSI codes).
        default: Default color code to use if conversion fails.

    Returns:
        Integer color code.
    """
    if isinstance(value, int):
        return value

    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning("Invalid color value %s, using default %d", value, default)
        return default


def extract_code_blocks(text: str) -> tuple[list[str], list[str]]:
    """Extract code blocks from text, returning compressible and preserved segments.

    Args:
        text: Raw thinking text potentially containing code blocks (``` markers).

    Returns:
        Tuple of (compressible_segments, all_segments_with_markers).
        - compressible_segments: Only the text outside code blocks.
        - all_segments_with_markers: All segments with marker strings to indicate code blocks.
    """
    # Split on code block markers: ``` optionally followed by language name and optional newline
    # Handles both multiline blocks (```python\n) and inline blocks (```python or ```)
    code_block_regex = r'(```[^\n]*\n?)'

    segments = re.split(code_block_regex, text)

    compressible: list[str] = []
    all_segments: list[str] = []
    in_code_block = False

    for segment in segments:
        if segment.startswith('```'):
            # Toggle code block state
            in_code_block = not in_code_block
            all_segments.append('__CODE_BLOCK_MARKER__')
        elif in_code_block:
            # Inside code block - preserve as-is
            all_segments.append(f'__CODE_BLOCK__{segment}__END_CODE_BLOCK__')
        elif segment.strip():
            # Outside code block - mark for compression
            compressible.append(segment)
            all_segments.append('__COMPRESSIBLE__')

    return compressible, all_segments


def reassemble_with_code_blocks(
    all_segments: list[str],
    compressed_texts: list[str],
    original_text: str,
) -> str:
    """Reassemble text with code blocks preserved and other parts compressed.

    Args:
        all_segments: Segment markers from extract_code_blocks.
        compressed_texts: Compressed versions of compressible segments.
        original_text: Original text for extracting preserved code blocks.

    Returns:
        Reassembled text with code blocks intact and other parts compressed.
    """
    # Re-split original to get code blocks (must match extract_code_blocks regex)
    code_block_regex = r'(```[^\n]*\n?)'
    original_segments = re.split(code_block_regex, original_text)

    result_parts: list[str] = []
    compressed_idx = 0
    original_idx = 0
    in_code_block = False

    for marker in all_segments:
        if marker == '__CODE_BLOCK_MARKER__':
            # Add the marker from original
            if original_idx < len(original_segments):
                result_parts.append(original_segments[original_idx])
                original_idx += 1
            in_code_block = not in_code_block
        elif marker.startswith('__CODE_BLOCK__'):
            # Extract and preserve code block content
            code_content = marker.replace('__CODE_BLOCK__', '').replace('__END_CODE_BLOCK__', '')
            result_parts.append(code_content)
            original_idx += 1
        elif marker == '__COMPRESSIBLE__':
            # Use compressed version
            if compressed_idx < len(compressed_texts):
                result_parts.append(compressed_texts[compressed_idx])
                compressed_idx += 1
            original_idx += 1

    return ''.join(result_parts)


class TransformThinkingHandler:
    """Handler for transforming thinking entries with compression and coloring."""

    @staticmethod
    async def handle(command: TransformThinkingCommand, config: Config | None = None) -> TransformThinkingResponse:
        """Handle thinking transformation request.

        Args:
            command: Transformation command with thinking lines and options.
            config: Application config with claude_agent settings. Optional.

        Returns:
            Transformation response with compressed lines and colors, or fallback on failure.
        """
        # Initialize services (pass config to compression service)
        compression_service = CompressPhraseService(CompressionOptions(), config=config)
        colored_formatter = ColoredFormatter(enable_colors=command.enable_colors)

        # Process each thinking line
        transformed_lines: list[str] = []
        colors: list[int] = []
        errors: list[str] = []
        overall_success = True

        # Process each thinking line
        for line in command.thinking_lines:
            # Check if line contains code blocks
            if '```' in line:
                # Extract code blocks - only compress non-code parts
                compressible_segments, all_segments = extract_code_blocks(line)

                if not compressible_segments:
                    # All code blocks, no compression needed
                    transformed_lines.append(line)
                    colors.append(37)
                    continue

                # Compress only the compressible segments
                tasks = [compression_service.compress(segment) for segment in compressible_segments]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Collect compressed texts
                compressed_texts: list[str] = []
                has_error = False
                for segment, result in zip(compressible_segments, results, strict=False):
                    if isinstance(result, BaseException) or "error" in result:
                        # Error - use original segment
                        compressed_texts.append(segment)
                        has_error = True
                    else:
                        compressed_texts.append(result.get("text", segment))

                # Reassemble with code blocks
                reassembled = reassemble_with_code_blocks(all_segments, compressed_texts, line)

                # Apply color to the whole line (use first result's color)
                if compressed_texts and not has_error and results and isinstance(results[0], dict):
                    color = safe_int_color(results[0].get("color", 37))
                else:
                    color = 37

                if command.enable_colors:
                    formatted_text = colored_formatter.format(reassembled, color)
                    transformed_lines.append(formatted_text)
                else:
                    transformed_lines.append(reassembled)

                colors.append(color)
            else:
                # No code blocks - compress normally
                try:
                    result = await compression_service.compress(line)

                    if isinstance(result, BaseException):
                        # Exception occurred
                        logger.error("Compression failed for line: %s", result)
                        transformed_lines.append(line)  # Use original
                        colors.append(37)  # Default white color
                        errors.append(f"⚠️  Compression error: {result}")
                        overall_success = False
                    elif "error" in result:
                        # Compression returned error dict
                        logger.warning("Compression error: %s", result.get("error"))
                        transformed_lines.append(line)  # Use original
                        colors.append(37)  # Default white color
                        errors.append(f"⚠️  {result.get('error')}")
                        overall_success = False
                    else:
                        # Success
                        compressed_text = result.get("text", line)
                        color = safe_int_color(result.get("color", 37))

                        # Apply color if enabled
                        if command.enable_colors:
                            formatted_text = colored_formatter.format(compressed_text, color)
                            transformed_lines.append(formatted_text)
                        else:
                            transformed_lines.append(compressed_text)

                        colors.append(color)
                except Exception as e:
                    # Catch any exceptions from compression (broad catch intentional for robustness)
                    logger.exception("Compression exception for line")
                    transformed_lines.append(line)  # Use original
                    colors.append(37)  # Default white color
                    errors.append(f"⚠️  Compression error: {e}")
                    overall_success = False

        return TransformThinkingResponse(
            transformed_lines=transformed_lines,
            colors=colors,
            success=overall_success,
            errors=errors,
            original_lines=list(command.thinking_lines),
        )

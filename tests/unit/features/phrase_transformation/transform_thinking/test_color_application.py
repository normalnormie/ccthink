# ABOUTME: Tests for ColoredFormatter integration and color application
# ABOUTME: Verifies format() calls, color enabling/disabling, and fallback colors

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)


class TestColorApplication:
    """Test color formatting and ColoredFormatter integration."""

    @pytest.mark.asyncio
    async def test_colored_formatter_called_when_colors_enabled(self) -> None:
        """ColoredFormatter.format() is called when colors enabled."""
        command = TransformThinkingCommand(
            thinking_lines=["Colored line"],
            enable_colors=True,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with (
            patch(
                "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
                mock_compress,
            ),
            patch.object(sys.stdout, "isatty", return_value=True),
            patch.dict(os.environ, {"TERM": "xterm"}, clear=True),
        ):
            response = await TransformThinkingHandler.handle(command)

        # With colors enabled and terminal support, should have ANSI codes
        assert "\x1b[" in response.transformed_lines[0]
        assert response.colors[0] == 34

    @pytest.mark.asyncio
    async def test_plain_text_returned_when_colors_disabled(self) -> None:
        """Plain text returned when colors disabled."""
        command = TransformThinkingCommand(
            thinking_lines=["Plain line"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed plain"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should not have ANSI escape codes
        assert "\x1b[" not in response.transformed_lines[0]
        assert response.transformed_lines[0] == "compressed plain"
        # Color code should still be recorded
        assert response.colors[0] == 34

    @pytest.mark.asyncio
    async def test_white_color_used_for_error_fallback(self) -> None:
        """White color (37) used when error occurs."""
        command = TransformThinkingCommand(
            thinking_lines=["Error line"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(side_effect=ValueError("Compression error"))

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Error should use white color (37)
        assert response.colors[0] == 37
        assert response.transformed_lines[0] == "Error line"

    @pytest.mark.asyncio
    async def test_color_from_compression_result_applied(self) -> None:
        """Color from compression result is properly applied."""
        command = TransformThinkingCommand(
            thinking_lines=["Blue line", "Green line", "Red line"],
            enable_colors=False,
        )

        call_count = 0
        colors = [34, 46, 196]  # Blue, green, red

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            color = colors[call_count]
            call_count += 1
            return {"color": str(color), "text": f"compressed {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Verify each color was applied
        assert response.colors[0] == 34
        assert response.colors[1] == 46
        assert response.colors[2] == 196

    @pytest.mark.asyncio
    async def test_default_color_when_color_field_missing(self) -> None:
        """Default to white (37) when color field missing from result."""
        command = TransformThinkingCommand(
            thinking_lines=["No color field"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"text": "compressed without color"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should default to 37 when color field missing
        assert response.colors[0] == 37
        assert response.transformed_lines[0] == "compressed without color"

    @pytest.mark.asyncio
    async def test_color_formatting_with_ansi_codes(self) -> None:
        """Verify ANSI color codes are properly formatted."""
        command = TransformThinkingCommand(
            thinking_lines=["ANSI test"],
            enable_colors=True,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "blue text"})

        with (
            patch(
                "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
                mock_compress,
            ),
            patch.object(sys.stdout, "isatty", return_value=True),
            patch.dict(os.environ, {"TERM": "xterm"}, clear=True),
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should contain ANSI color code for color 34
        assert "\x1b[38;5;34m" in response.transformed_lines[0]
        assert "\x1b[0m" in response.transformed_lines[0]  # Reset code

    @pytest.mark.asyncio
    async def test_mixed_colors_in_batch(self) -> None:
        """Handle mixed colors across multiple lines in batch."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2", "Line 3"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            color = 30 + call_count
            return {"color": str(color), "text": f"compressed {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Each line should have different color
        assert response.colors[0] == 31
        assert response.colors[1] == 32
        assert response.colors[2] == 33

    @pytest.mark.asyncio
    async def test_colors_disabled_but_codes_recorded(self) -> None:
        """Color codes recorded even when display disabled."""
        command = TransformThinkingCommand(
            thinking_lines=["Record color"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "196", "text": "red text"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Color should be recorded even though not applied
        assert response.colors[0] == 196
        # But text should be plain
        assert "\x1b[" not in response.transformed_lines[0]

    @pytest.mark.asyncio
    async def test_error_and_success_colors_in_same_response(self) -> None:
        """Mix of error (color 37) and success colors in response."""
        command = TransformThinkingCommand(
            thinking_lines=["Success", "Error", "Success"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Error on second line")
            return {"color": "34", "text": "compressed"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # First and third should have color 34
        assert response.colors[0] == 34
        assert response.colors[2] == 34
        # Second should have error color 37
        assert response.colors[1] == 37

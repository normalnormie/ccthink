# ABOUTME: Tests for safe_int_color utility function
# ABOUTME: Verifies handling of integers, strings, ANSI codes, and invalid values

from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
    safe_int_color,
)


class TestSafeColorConversion:
    """Verify safe_int_color handles all input types correctly."""

    def test_handles_valid_integers(self) -> None:
        """Direct integers pass through unchanged."""
        assert safe_int_color(42) == 42
        assert safe_int_color(0) == 0
        assert safe_int_color(255) == 255
        assert safe_int_color(37) == 37

    def test_converts_valid_string_integers(self) -> None:
        """String representations of integers convert correctly."""
        assert safe_int_color("42") == 42
        assert safe_int_color("0") == 0
        assert safe_int_color("255") == 255
        assert safe_int_color("37") == 37

    def test_returns_default_for_ansi_codes(self) -> None:
        """ANSI escape codes return default value instead of crashing."""
        # The exact case from the bug report
        result = safe_int_color("\x1b[38;5;209m", default=37)
        assert result == 37

        # Other ANSI variations
        assert safe_int_color("\x1b[0m", default=37) == 37
        assert safe_int_color("\x1b[1m", default=37) == 37
        assert safe_int_color("\x1b[38;5;34m", default=37) == 37

    def test_returns_default_for_empty_strings(self) -> None:
        """Empty strings return default value."""
        assert safe_int_color("", default=37) == 37
        assert safe_int_color("", default=42) == 42

    def test_returns_default_for_invalid_strings(self) -> None:
        """Invalid string values return default instead of crashing."""
        assert safe_int_color("not-a-number", default=37) == 37
        assert safe_int_color("42.5", default=37) == 37
        assert safe_int_color("abc123", default=37) == 37
        assert safe_int_color("None", default=37) == 37

    def test_uses_custom_default_values(self) -> None:
        """Custom default values are respected."""
        assert safe_int_color("invalid", default=100) == 100
        assert safe_int_color("\x1b[0m", default=200) == 200
        assert safe_int_color("", default=42) == 42

    def test_handles_none_type(self) -> None:
        """None values return default instead of crashing."""
        assert safe_int_color(None, default=37) == 37  # type: ignore[arg-type]


class TestColorConversionInHandler:
    """Verify handler uses safe_int_color for compression results."""

    @pytest.mark.asyncio
    async def test_handler_with_ansi_in_color_field(self) -> None:
        """Handler gracefully handles ANSI codes in compression color field."""
        command = TransformThinkingCommand(
            thinking_lines=["Line with ANSI color"],
            enable_colors=False,
        )

        # Simulate compression returning ANSI code in color field (the bug)
        mock_compress = AsyncMock(return_value={"color": "\x1b[38;5;209m", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should fall back to default color (37) instead of crashing
        assert response.colors[0] == 37
        assert response.transformed_lines[0] == "compressed"
        assert response.success is True

    @pytest.mark.asyncio
    async def test_handler_with_valid_int_color(self) -> None:
        """Handler correctly processes valid integer colors."""
        command = TransformThinkingCommand(
            thinking_lines=["Valid color"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "42", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Valid color should be preserved
        assert response.colors[0] == 42
        assert response.transformed_lines[0] == "compressed"

    @pytest.mark.asyncio
    async def test_handler_with_mixed_color_types(self) -> None:
        """Handler handles mix of valid colors and ANSI codes."""
        command = TransformThinkingCommand(
            thinking_lines=["Valid", "ANSI", "Valid"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                # Return ANSI code for second line
                return {"color": "\x1b[38;5;209m", "text": "compressed ansi"}
            return {"color": "34", "text": f"compressed {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # First and third should have valid color 34
        assert response.colors[0] == 34
        assert response.colors[2] == 34
        # Second should have fallen back to 37
        assert response.colors[1] == 37

# ABOUTME: Edge case tests for TransformThinkingHandler
# ABOUTME: Tests very long lines, Unicode content, special characters, and malformed data

from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_very_long_thinking_lines(self) -> None:
        """Handle very long thinking lines (>1000 chars)."""
        long_line = "x" * 2000
        command = TransformThinkingCommand(
            thinking_lines=[long_line],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed long"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is True
        assert response.transformed_lines[0] == "compressed long"

    @pytest.mark.asyncio
    async def test_empty_string_lines(self) -> None:
        """Handle empty string lines."""
        command = TransformThinkingCommand(
            thinking_lines=["", "content", ""],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"color": "34", "text": f"compressed {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Empty strings should still be processed
        assert len(response.transformed_lines) == 3
        assert response.success is True

    @pytest.mark.asyncio
    async def test_lines_with_special_characters(self) -> None:
        """Handle lines with special characters."""
        command = TransformThinkingCommand(
            thinking_lines=[
                "Line with !@#$%^&*()",
                "Line with \n newline",
                'Line with "quotes" and \'apostrophes\'',
            ],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"color": "34", "text": f"special {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert len(response.transformed_lines) == 3
        assert response.success is True

    @pytest.mark.asyncio
    async def test_unicode_content(self) -> None:
        """Handle Unicode content."""
        command = TransformThinkingCommand(
            thinking_lines=[
                "Unicode: 你好世界",
                "Emoji: 🎉🎊🎈",
                "Arabic: مرحبا",
            ],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"color": "34", "text": f"unicode {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert len(response.transformed_lines) == 3
        assert response.success is True

    @pytest.mark.asyncio
    async def test_concurrent_processing_result_ordering(self) -> None:
        """Verify concurrent processing doesn't corrupt result ordering."""
        # Create 9 lines (3 batches of 3)
        lines = [f"Line {i}" for i in range(1, 10)]
        command = TransformThinkingCommand(
            thinking_lines=lines,
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"color": "34", "text": f"result {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Verify results are in correct order
        for i in range(9):
            assert f"result {i + 1}" in response.transformed_lines[i]

    @pytest.mark.asyncio
    async def test_lines_with_only_whitespace(self) -> None:
        """Handle lines with only whitespace."""
        command = TransformThinkingCommand(
            thinking_lines=["   ", "\t\t", "  \n  "],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"color": "34", "text": f"ws {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert len(response.transformed_lines) == 3
        assert response.success is True

    @pytest.mark.asyncio
    async def test_malformed_json_response_handling(self) -> None:
        """Handle malformed JSON from compression service."""
        command = TransformThinkingCommand(
            thinking_lines=["Malformed"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "incomplete"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should process successfully with the returned dict
        assert response.transformed_lines[0] == "incomplete"
        assert response.success is True

    @pytest.mark.asyncio
    async def test_single_batch_with_mixed_results(self) -> None:
        """Single batch of 3 with mixed success/failure."""
        command = TransformThinkingCommand(
            thinking_lines=["S", "F", "S"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Middle fails")
            return {"color": "34", "text": "ok"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert len(response.transformed_lines) == 3
        assert response.transformed_lines[1] == "F"  # Fallback
        assert response.success is False

    @pytest.mark.asyncio
    async def test_ten_lines_across_four_batches(self) -> None:
        """Ten lines processed across 4 batches (3+3+3+1)."""
        command = TransformThinkingCommand(
            thinking_lines=[f"L{i}" for i in range(10)],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"color": "34", "text": f"c{call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert len(response.transformed_lines) == 10
        assert all(f"c{i + 1}" in response.transformed_lines[i] for i in range(10))
        assert response.success is True

    @pytest.mark.asyncio
    async def test_response_with_missing_text_field(self) -> None:
        """Handle response dict missing 'text' field."""
        command = TransformThinkingCommand(
            thinking_lines=["No text field"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should use original line as fallback when text is missing
        assert response.transformed_lines[0] == "No text field"
        assert response.colors[0] == 34
        assert response.success is True

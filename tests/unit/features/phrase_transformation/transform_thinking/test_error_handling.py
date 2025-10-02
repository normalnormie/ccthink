# ABOUTME: Tests for error handling with BaseException and error dicts
# ABOUTME: Verifies fallback behavior, error collection, and success flag management

from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)


class TestErrorHandling:
    """Test error handling from compression service."""

    @pytest.mark.asyncio
    async def test_handling_base_exception_from_asyncio_gather(self) -> None:
        """Handle BaseException from asyncio.gather with fallback."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call raises exception
                raise RuntimeError("Compression service error")
            # Second call succeeds
            return {"color": "34", "text": "compressed 2"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # First line should fallback to original
        assert response.transformed_lines[0] == "Line 1"
        assert response.colors[0] == 37  # White color for error
        # Second line should be compressed
        assert response.transformed_lines[1] == "compressed 2"
        assert response.colors[1] == 34
        # Success should be False due to first line error
        assert response.success is False
        assert len(response.errors) == 1
        assert "Compression error" in response.errors[0]

    @pytest.mark.asyncio
    async def test_handling_error_dict_from_compression(self) -> None:
        """Handle error dict from compression service."""
        command = TransformThinkingCommand(
            thinking_lines=["Line with error"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"error": "Compression failed", "raw": "Line with error"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should use original line
        assert response.transformed_lines[0] == "Line with error"
        assert response.colors[0] == 37  # White color for error
        assert response.success is False
        assert len(response.errors) == 1
        assert "Compression failed" in response.errors[0]

    @pytest.mark.asyncio
    async def test_handling_successful_compression_result(self) -> None:
        """Handle successful compression result dict."""
        command = TransformThinkingCommand(
            thinking_lines=["Success line"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed success"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.transformed_lines[0] == "compressed success"
        assert response.colors[0] == 34
        assert response.success is True
        assert len(response.errors) == 0

    @pytest.mark.asyncio
    async def test_fallback_to_original_line_on_exception(self) -> None:
        """Fallback to original line when compression raises exception."""
        command = TransformThinkingCommand(
            thinking_lines=["Original line"],
            enable_colors=False,
        )

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            raise ValueError("Invalid compression format")

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.transformed_lines[0] == "Original line"
        assert response.colors[0] == 37
        assert response.success is False

    @pytest.mark.asyncio
    async def test_fallback_to_white_color_on_error(self) -> None:
        """Fallback to white color (37) when error occurs."""
        command = TransformThinkingCommand(
            thinking_lines=["Error line"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"error": "Some error", "raw": "Error line"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Color should be white (37) for error
        assert response.colors[0] == 37

    @pytest.mark.asyncio
    async def test_error_message_collection(self) -> None:
        """Collect all error messages from failed compressions."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2", "Line 3"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Error 1")
            elif call_count == 2:
                return {"error": "Error 2", "raw": "Line 2"}
            else:
                return {"color": "34", "text": "compressed 3"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should have 2 errors
        assert len(response.errors) == 2
        assert any("Error 1" in err for err in response.errors)
        assert any("Error 2" in err for err in response.errors)
        assert response.success is False

    @pytest.mark.asyncio
    async def test_success_flag_false_when_any_line_fails(self) -> None:
        """Set success=False when any line fails."""
        command = TransformThinkingCommand(
            thinking_lines=["Success 1", "Fail", "Success 2"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("Middle failure")
            return {"color": "34", "text": f"compressed {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Overall success should be False
        assert response.success is False
        # But other lines should still be processed
        assert len(response.transformed_lines) == 3

    @pytest.mark.asyncio
    async def test_multiple_exception_types_handled(self) -> None:
        """Handle various exception types from compression."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2", "Line 3"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("ValueError occurred")
            elif call_count == 2:
                raise RuntimeError("RuntimeError occurred")
            else:
                return {"color": "34", "text": "compressed 3"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # All exceptions should be handled
        assert len(response.errors) == 2
        assert response.success is False
        # First two lines should use original
        assert response.transformed_lines[0] == "Line 1"
        assert response.transformed_lines[1] == "Line 2"
        # Third should be compressed
        assert response.transformed_lines[2] == "compressed 3"

    @pytest.mark.asyncio
    async def test_error_dict_without_raw_field(self) -> None:
        """Handle error dict even without 'raw' field."""
        command = TransformThinkingCommand(
            thinking_lines=["Line without raw"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"error": "Error without raw"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should still fallback to original line
        assert response.transformed_lines[0] == "Line without raw"
        assert response.colors[0] == 37
        assert response.success is False

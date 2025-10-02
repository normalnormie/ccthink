# ABOUTME: Integration tests for TransformThinkingHandler
# ABOUTME: Tests compression service integration and batch processing

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)


@pytest.fixture
def mock_compress_success() -> AsyncMock:
    """Create mock for successful compression.

    Returns:
        AsyncMock that returns successful compression result.
    """
    return AsyncMock(
        return_value={
            "text": "compressed",
            "color": "34",
        }
    )


@pytest.fixture
def mock_compress_failure() -> AsyncMock:
    """Create mock for failed compression.

    Returns:
        AsyncMock that returns error result.
    """
    return AsyncMock(
        return_value={
            "error": "Compression service unavailable",
        }
    )


class TestTransformThinkingHandler:
    """Test TransformThinkingHandler with mocked compression."""

    @pytest.mark.asyncio
    async def test_successful_transformation_with_colors(
        self, mock_compress_success: AsyncMock
    ) -> None:
        """Successful compression with colors enabled."""
        command = TransformThinkingCommand(
            thinking_lines=["Test thinking"],
            enable_streaming=True,
            enable_colors=True,
        )

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress_success,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is True
        assert len(response.transformed_lines) == 1
        assert len(response.colors) == 1
        assert response.colors[0] == 34
        assert len(response.errors) == 0
        mock_compress_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_transformation_no_colors(
        self, mock_compress_success: AsyncMock
    ) -> None:
        """Successful compression without colors."""
        command = TransformThinkingCommand(
            thinking_lines=["Test thinking"],
            enable_streaming=False,
            enable_colors=False,
        )

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress_success,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is True
        assert len(response.transformed_lines) == 1
        # Should be plain text, not colored
        assert response.transformed_lines[0] == "compressed"

    @pytest.mark.asyncio
    async def test_failed_transformation_fallback(self, mock_compress_failure: AsyncMock) -> None:
        """Compression failure uses fallback to original."""
        original_line = "Original thinking content"
        command = TransformThinkingCommand(
            thinking_lines=[original_line],
            enable_streaming=True,
            enable_colors=True,
        )

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress_failure,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is False
        # Should fallback to original
        assert response.transformed_lines[0] == original_line
        assert len(response.errors) == 1
        assert "Compression service unavailable" in response.errors[0]

    @pytest.mark.asyncio
    async def test_batch_processing_multiple_lines(self, mock_compress_success: AsyncMock) -> None:
        """Batch processing of multiple thinking lines."""
        command = TransformThinkingCommand(
            thinking_lines=["First line", "Second line", "Third line"],
            enable_streaming=True,
            enable_colors=False,
        )

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress_success,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is True
        assert len(response.transformed_lines) == 3
        # All should be compressed
        assert all(line == "compressed" for line in response.transformed_lines)
        assert mock_compress_success.call_count == 3

    @pytest.mark.asyncio
    async def test_empty_thinking_lines(self) -> None:
        """Empty thinking lines list handled gracefully."""
        command = TransformThinkingCommand(
            thinking_lines=[],
            enable_streaming=True,
            enable_colors=True,
        )

        response = await TransformThinkingHandler.handle(command)

        assert response.success is True
        assert len(response.transformed_lines) == 0
        assert len(response.errors) == 0

    @pytest.mark.asyncio
    async def test_mixed_success_failure(self) -> None:
        """Mixed success and failure in batch processing."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2", "Line 3"],
            enable_streaming=True,
            enable_colors=False,
        )

        # First succeeds, second fails, third succeeds
        mock_compress = AsyncMock(
            side_effect=[
                {"text": "compressed 1", "color": "32"},
                Exception("Network error"),
                {"text": "compressed 3", "color": "34"},
            ]
        )

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert len(response.transformed_lines) == 3
        assert response.transformed_lines[0] == "compressed 1"
        assert response.transformed_lines[1] == "Line 2"  # Fallback to original
        assert response.transformed_lines[2] == "compressed 3"
        assert response.success is False
        assert len(response.errors) == 1

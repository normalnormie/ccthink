# ABOUTME: Integration tests for error handling in compression flow
# ABOUTME: Tests fallback behavior and error logging

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)


class TestErrorHandling:
    """Test error handling in compression flow."""

    @pytest.mark.asyncio
    async def test_transformation_error_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Compression errors are logged."""
        command = TransformThinkingCommand(
            thinking_lines=["Test line"],
            enable_streaming=True,
            enable_colors=True,
        )

        mock_compress = AsyncMock(side_effect=Exception("Network error"))

        with (
            patch(
                "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
                mock_compress,
            ),
            caplog.at_level("ERROR"),
        ):
            response = await TransformThinkingHandler.handle(command)

            # Should fallback to original
            assert response.transformed_lines[0] == "Test line"
            assert response.success is False

            # Error should be logged
            assert any("Compression failed" in rec.message for rec in caplog.records)

    @pytest.mark.asyncio
    async def test_partial_failure_continues_processing(self) -> None:
        """Partial compression failure continues processing remaining lines."""
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

            # Should have all three lines
            assert len(response.transformed_lines) == 3
            assert response.transformed_lines[0] == "compressed 1"
            assert response.transformed_lines[1] == "Line 2"  # Fallback to original
            assert response.transformed_lines[2] == "compressed 3"
            assert response.success is False
            assert len(response.errors) == 1

    @pytest.mark.asyncio
    async def test_compression_service_error_response(self) -> None:
        """Compression service error response handled correctly."""
        command = TransformThinkingCommand(
            thinking_lines=["Test"],
            enable_streaming=True,
            enable_colors=True,
        )

        mock_compress = AsyncMock(
            return_value={
                "error": "API rate limit exceeded",
            }
        )

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

            assert response.success is False
            assert response.transformed_lines[0] == "Test"  # Fallback
            assert len(response.errors) == 1
            assert "rate limit" in response.errors[0]

    @pytest.mark.asyncio
    async def test_all_lines_fail_compression(self) -> None:
        """All lines failing compression returns all originals."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2", "Line 3"],
            enable_streaming=True,
            enable_colors=False,
        )

        mock_compress = AsyncMock(side_effect=Exception("Service down"))

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

            # All should fallback to original
            assert response.transformed_lines == ["Line 1", "Line 2", "Line 3"]
            assert response.success is False
            assert len(response.errors) == 3

    @pytest.mark.asyncio
    async def test_error_message_format(self, caplog: pytest.LogCaptureFixture) -> None:
        """Error messages have consistent format."""
        command = TransformThinkingCommand(
            thinking_lines=["Test"],
            enable_streaming=True,
            enable_colors=True,
        )

        mock_compress = AsyncMock(
            return_value={
                "error": "Timeout after 30s",
            }
        )

        with (
            patch(
                "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
                mock_compress,
            ),
            caplog.at_level("WARNING"),
        ):
            response = await TransformThinkingHandler.handle(command)

            # Error should have warning emoji
            assert "⚠️" in response.errors[0]
            assert "Timeout" in response.errors[0]

    @pytest.mark.asyncio
    async def test_unicode_in_error_messages(self) -> None:
        """Unicode content in errors handled correctly."""
        command = TransformThinkingCommand(
            thinking_lines=["你好世界 🌍"],
            enable_streaming=True,
            enable_colors=False,
        )

        mock_compress = AsyncMock(side_effect=Exception("Processing failed"))

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

            # Should fallback to original unicode content
            assert response.transformed_lines[0] == "你好世界 🌍"
            assert response.success is False

    @pytest.mark.asyncio
    async def test_exception_recovery_continues_batch(self) -> None:
        """Exception in one line doesn't stop batch processing."""
        command = TransformThinkingCommand(
            thinking_lines=["A", "B", "C", "D", "E"],
            enable_streaming=True,
            enable_colors=False,
        )

        # Fail on index 2
        mock_compress = AsyncMock(
            side_effect=[
                {"text": "a", "color": "32"},
                {"text": "b", "color": "33"},
                Exception("Error on C"),
                {"text": "d", "color": "34"},
                {"text": "e", "color": "35"},
            ]
        )

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

            assert len(response.transformed_lines) == 5
            assert response.transformed_lines[0] == "a"
            assert response.transformed_lines[1] == "b"
            assert response.transformed_lines[2] == "C"  # Original fallback
            assert response.transformed_lines[3] == "d"
            assert response.transformed_lines[4] == "e"
            assert response.success is False
            assert len(response.errors) == 1

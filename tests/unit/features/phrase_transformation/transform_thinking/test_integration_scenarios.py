# ABOUTME: Integration tests for TransformThinkingHandler
# ABOUTME: Tests streaming modes, color combinations, and mixed success/failure scenarios

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


class TestIntegrationScenarios:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    async def test_streaming_enabled_with_colors_enabled(self) -> None:
        """Integration with streaming and colors both enabled."""
        command = TransformThinkingCommand(
            thinking_lines=["Stream and color"],
            enable_streaming=True,
            enable_colors=True,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed stream"})

        with (
            patch(
                "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
                mock_compress,
            ),
            patch.object(sys.stdout, "isatty", return_value=True),
            patch.dict(os.environ, {"TERM": "xterm"}, clear=True),
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is True
        assert len(response.transformed_lines) == 1

    @pytest.mark.asyncio
    async def test_streaming_disabled_with_colors_disabled(self) -> None:
        """Integration with streaming and colors both disabled."""
        command = TransformThinkingCommand(
            thinking_lines=["No stream no color"],
            enable_streaming=False,
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "plain compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is True
        assert "\x1b[" not in response.transformed_lines[0]

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure_scenario(self) -> None:
        """Mixed success and failure across multiple lines."""
        command = TransformThinkingCommand(
            thinking_lines=["Success 1", "Fail 1", "Success 2", "Fail 2", "Success 3"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count in [2, 4]:  # Fail on calls 2 and 4
                raise ValueError(f"Failure {call_count}")
            return {"color": "34", "text": f"compressed {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Check mixed results
        assert "compressed 1" in response.transformed_lines[0]  # Success
        assert response.transformed_lines[1] == "Fail 1"  # Failure
        assert "compressed 3" in response.transformed_lines[2]  # Success
        assert response.transformed_lines[3] == "Fail 2"  # Failure
        assert "compressed 5" in response.transformed_lines[4]  # Success
        assert response.success is False  # Overall failure
        assert len(response.errors) == 2

    @pytest.mark.asyncio
    async def test_all_lines_fail_scenario(self) -> None:
        """All lines fail to compress."""
        command = TransformThinkingCommand(
            thinking_lines=["Fail 1", "Fail 2", "Fail 3"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(side_effect=ValueError("All compressions fail"))

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # All should fallback to original
        assert response.transformed_lines[0] == "Fail 1"
        assert response.transformed_lines[1] == "Fail 2"
        assert response.transformed_lines[2] == "Fail 3"
        # All should have white color
        assert all(color == 37 for color in response.colors)
        assert response.success is False
        assert len(response.errors) == 3

    @pytest.mark.asyncio
    async def test_all_lines_succeed_scenario(self) -> None:
        """All lines compress successfully."""
        command = TransformThinkingCommand(
            thinking_lines=["Success 1", "Success 2", "Success 3"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            return {"color": f"3{call_count}", "text": f"compressed {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # All should be compressed
        assert "compressed 1" in response.transformed_lines[0]
        assert "compressed 2" in response.transformed_lines[1]
        assert "compressed 3" in response.transformed_lines[2]
        assert response.success is True
        assert len(response.errors) == 0

    @pytest.mark.asyncio
    async def test_streaming_enabled_colors_disabled(self) -> None:
        """Streaming enabled but colors disabled."""
        command = TransformThinkingCommand(
            thinking_lines=["Stream without color"],
            enable_streaming=True,
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "stream plain"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is True
        assert "\x1b[" not in response.transformed_lines[0]
        assert response.transformed_lines[0] == "stream plain"

    @pytest.mark.asyncio
    async def test_streaming_disabled_colors_enabled(self) -> None:
        """Streaming disabled but colors enabled."""
        command = TransformThinkingCommand(
            thinking_lines=["Color without stream"],
            enable_streaming=False,
            enable_colors=True,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "color plain"})

        with (
            patch(
                "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
                mock_compress,
            ),
            patch.object(sys.stdout, "isatty", return_value=True),
            patch.dict(os.environ, {"TERM": "xterm"}, clear=True),
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is True
        assert "\x1b[" in response.transformed_lines[0]

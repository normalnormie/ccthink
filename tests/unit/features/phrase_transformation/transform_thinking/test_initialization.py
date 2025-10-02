# ABOUTME: Tests for TransformThinkingHandler service initialization
# ABOUTME: Verifies CompressPhraseService and ColoredFormatter initialization

from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)


class TestServiceInitialization:
    """Test service initialization within handler."""

    @pytest.mark.asyncio
    async def test_handler_initializes_with_colors_enabled(self) -> None:
        """Handler initializes ColoredFormatter with enable_colors=True."""
        command = TransformThinkingCommand(
            thinking_lines=["test line"],
            enable_colors=True,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            # The handler should initialize services without error
            response = await TransformThinkingHandler.handle(command)

        # Verify response structure is created (initialization succeeded)
        assert response is not None
        assert hasattr(response, "transformed_lines")
        assert hasattr(response, "colors")
        assert hasattr(response, "success")
        assert hasattr(response, "errors")
        assert hasattr(response, "original_lines")

    @pytest.mark.asyncio
    async def test_handler_initializes_with_colors_disabled(self) -> None:
        """Handler initializes ColoredFormatter with enable_colors=False."""
        command = TransformThinkingCommand(
            thinking_lines=["test line"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            # The handler should initialize services without error
            response = await TransformThinkingHandler.handle(command)

        # Verify response structure is created (initialization succeeded)
        assert response is not None
        assert hasattr(response, "transformed_lines")

    @pytest.mark.asyncio
    async def test_handler_initializes_with_streaming_enabled(self) -> None:
        """Handler initializes with streaming enabled."""
        command = TransformThinkingCommand(
            thinking_lines=["test line"],
            enable_streaming=True,
            enable_colors=True,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            # The handler should initialize services without error
            response = await TransformThinkingHandler.handle(command)

        # Verify response is created
        assert response is not None

    @pytest.mark.asyncio
    async def test_handler_initializes_with_streaming_disabled(self) -> None:
        """Handler initializes with streaming disabled."""
        command = TransformThinkingCommand(
            thinking_lines=["test line"],
            enable_streaming=False,
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            # The handler should initialize services without error
            response = await TransformThinkingHandler.handle(command)

        # Verify response is created
        assert response is not None

    @pytest.mark.asyncio
    async def test_handler_initializes_compression_service(self) -> None:
        """Handler initializes CompressPhraseService."""
        command = TransformThinkingCommand(
            thinking_lines=["test line"],
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            # The handler internally creates CompressPhraseService
            # We verify by checking that compression is attempted (response contains data)
            response = await TransformThinkingHandler.handle(command)

        # If compression service initialized, we should get a response
        assert response is not None
        assert len(response.transformed_lines) > 0

    @pytest.mark.asyncio
    async def test_handler_initializes_colored_formatter(self) -> None:
        """Handler initializes ColoredFormatter."""
        command = TransformThinkingCommand(
            thinking_lines=["test line"],
            enable_colors=True,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            # The handler internally creates ColoredFormatter
            # We verify by checking response structure
            response = await TransformThinkingHandler.handle(command)

        # If formatter initialized, colors should be present
        assert response is not None
        assert hasattr(response, "colors")
        assert len(response.colors) > 0

    @pytest.mark.asyncio
    async def test_handler_with_default_command_parameters(self) -> None:
        """Handler works with default command parameters."""
        command = TransformThinkingCommand(
            thinking_lines=["test line"],
            # Use defaults: enable_streaming=True, enable_colors=True
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response is not None
        assert response.transformed_lines is not None
        assert response.colors is not None

    @pytest.mark.asyncio
    async def test_handler_with_all_parameters_specified(self) -> None:
        """Handler works with all parameters explicitly specified."""
        command = TransformThinkingCommand(
            thinking_lines=["test line"],
            enable_streaming=False,
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response is not None
        assert response.transformed_lines is not None
        assert response.colors is not None

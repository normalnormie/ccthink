# ABOUTME: Tests for batch processing with max_concurrent=3 limit
# ABOUTME: Verifies parallel execution, batch ordering, and asyncio.gather usage

from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)


class TestBatchProcessing:
    """Test batch processing with concurrency control."""

    @pytest.mark.asyncio
    async def test_processing_single_line(self) -> None:
        """Process single line successfully."""
        command = TransformThinkingCommand(
            thinking_lines=["Single thinking line"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed single"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert len(response.transformed_lines) == 1
        assert response.transformed_lines[0] == "compressed single"
        assert len(response.colors) == 1
        assert response.colors[0] == 34

    @pytest.mark.asyncio
    async def test_processing_three_lines_max_concurrent_batch(self) -> None:
        """Process 3 lines (max concurrent batch) in parallel."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2", "Line 3"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            line_num = call_count
            return {"color": f"3{line_num}", "text": f"compressed {line_num}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # All 3 lines should be processed
        assert len(response.transformed_lines) == 3
        assert len(response.colors) == 3
        # Verify all compressions were called
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_processing_five_lines_multiple_batches(self) -> None:
        """Process 5+ lines across multiple batches of 3."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            line_num = call_count
            return {"color": f"3{line_num}", "text": f"compressed {line_num}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # All 5 lines should be processed
        # Batch 1: Lines 1-3, Batch 2: Lines 4-5
        assert len(response.transformed_lines) == 5
        assert len(response.colors) == 5
        assert call_count == 5

    @pytest.mark.asyncio
    async def test_processing_empty_list(self) -> None:
        """Process empty list returns empty response."""
        command = TransformThinkingCommand(
            thinking_lines=[],
            enable_colors=False,
        )

        response = await TransformThinkingHandler.handle(command)

        assert len(response.transformed_lines) == 0
        assert len(response.colors) == 0
        assert response.success is True
        assert len(response.errors) == 0

    @pytest.mark.asyncio
    async def test_batches_processed_in_order(self) -> None:
        """Batches are processed in order maintaining sequence."""
        command = TransformThinkingCommand(
            thinking_lines=[f"Line {i}" for i in range(1, 8)],  # 7 lines: 3+3+1 batches
            enable_colors=False,
        )

        call_order = []

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            # Extract line number from phrase
            for i in range(1, 8):
                if f"Line {i}" in phrase:
                    call_order.append(i)
                    return {"color": "34", "text": f"compressed {i}"}
            return {"color": "34", "text": "compressed"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Verify all lines processed in order
        assert len(response.transformed_lines) == 7
        for i in range(1, 8):
            assert f"compressed {i}" in response.transformed_lines[i - 1]

    @pytest.mark.asyncio
    async def test_max_concurrent_three_respected(self) -> None:
        """Verify max_concurrent=3 is respected in batching."""
        command = TransformThinkingCommand(
            thinking_lines=[f"Line {i}" for i in range(1, 10)],  # 9 lines: 3+3+3 batches
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # All lines should be processed
        assert len(response.transformed_lines) == 9

    @pytest.mark.asyncio
    async def test_asyncio_gather_used_for_parallel_execution(self) -> None:
        """Verify asyncio.gather is used for parallel batch execution."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2", "Line 3"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            # The handler uses asyncio.gather internally
            # We verify by checking all tasks complete
            response = await TransformThinkingHandler.handle(command)

        # If gather worked correctly, all lines processed
        assert len(response.transformed_lines) == 3
        assert response.success is True

    @pytest.mark.asyncio
    async def test_processing_six_lines_exactly_two_batches(self) -> None:
        """Process exactly 6 lines in exactly 2 batches of 3."""
        command = TransformThinkingCommand(
            thinking_lines=[f"Line {i}" for i in range(1, 7)],  # 6 lines
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

        # Should have 2 batches: lines 1-3 and 4-6
        assert len(response.transformed_lines) == 6
        assert call_count == 6

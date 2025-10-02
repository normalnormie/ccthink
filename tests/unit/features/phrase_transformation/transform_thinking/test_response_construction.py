# ABOUTME: Tests for TransformThinkingResponse construction and validation
# ABOUTME: Verifies response fields, success flags, and original line preservation

from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.transform_thinking.transform_thinking_command import (
    TransformThinkingCommand,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_handler import (
    TransformThinkingHandler,
)


class TestResponseConstruction:
    """Test response object construction and validation."""

    @pytest.mark.asyncio
    async def test_result_lines_contain_all_outputs(self) -> None:
        """Result lines contain all outputs (successful or fallback)."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2", "Line 3"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Error on line 2")
            return {"color": "34", "text": f"compressed {call_count}"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should have all 3 lines
        assert len(response.transformed_lines) == 3
        # Line 2 should be original (fallback)
        assert response.transformed_lines[1] == "Line 2"

    @pytest.mark.asyncio
    async def test_colors_list_matches_result_lines_length(self) -> None:
        """Colors list has same length as result lines."""
        command = TransformThinkingCommand(
            thinking_lines=["A", "B", "C", "D", "E"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Colors and lines should match
        assert len(response.colors) == len(response.transformed_lines)
        assert len(response.colors) == 5

    @pytest.mark.asyncio
    async def test_success_true_when_all_lines_succeed(self) -> None:
        """Success=True when all lines compress successfully."""
        command = TransformThinkingCommand(
            thinking_lines=["Line 1", "Line 2", "Line 3"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is True
        assert len(response.errors) == 0

    @pytest.mark.asyncio
    async def test_success_false_when_any_line_fails(self) -> None:
        """Success=False when any line fails to compress."""
        command = TransformThinkingCommand(
            thinking_lines=["Success", "Failure"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Compression failed")
            return {"color": "34", "text": "compressed"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert response.success is False

    @pytest.mark.asyncio
    async def test_errors_list_contains_all_error_messages(self) -> None:
        """Errors list contains all error messages encountered."""
        command = TransformThinkingCommand(
            thinking_lines=["L1", "L2", "L3", "L4"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count in [1, 3]:  # Fail on lines 1 and 3
                raise ValueError(f"Error {call_count}")
            return {"color": "34", "text": "compressed"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Should have 2 errors
        assert len(response.errors) == 2
        assert any("Error 1" in err for err in response.errors)
        assert any("Error 3" in err for err in response.errors)

    @pytest.mark.asyncio
    async def test_original_lines_preserved_in_response(self) -> None:
        """Original lines are preserved in response."""
        original_lines = ["Original 1", "Original 2", "Original 3"]
        command = TransformThinkingCommand(
            thinking_lines=original_lines,
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Original lines should be preserved exactly
        assert list(response.original_lines) == original_lines

    @pytest.mark.asyncio
    async def test_original_lines_preserved_on_all_failures(self) -> None:
        """Original lines preserved even when all compressions fail."""
        original_lines = ["Keep 1", "Keep 2"]
        command = TransformThinkingCommand(
            thinking_lines=original_lines,
            enable_colors=False,
        )

        mock_compress = AsyncMock(side_effect=ValueError("All fail"))

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Original lines preserved
        assert list(response.original_lines) == original_lines
        # Result lines should be originals (fallback)
        assert list(response.transformed_lines) == original_lines

    @pytest.mark.asyncio
    async def test_empty_errors_list_on_success(self) -> None:
        """Errors list is empty when all compressions succeed."""
        command = TransformThinkingCommand(
            thinking_lines=["Success line"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        assert len(response.errors) == 0
        assert response.success is True

    @pytest.mark.asyncio
    async def test_response_with_empty_thinking_lines(self) -> None:
        """Response constructed correctly with empty input."""
        command = TransformThinkingCommand(
            thinking_lines=[],
            enable_colors=False,
        )

        response = await TransformThinkingHandler.handle(command)

        assert len(response.transformed_lines) == 0
        assert len(response.colors) == 0
        assert len(response.errors) == 0
        assert len(response.original_lines) == 0
        assert response.success is True

    @pytest.mark.asyncio
    async def test_response_structure_fields_present(self) -> None:
        """Response has all required fields present."""
        command = TransformThinkingCommand(
            thinking_lines=["Test"],
            enable_colors=False,
        )

        mock_compress = AsyncMock(return_value={"color": "34", "text": "compressed"})

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            mock_compress,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Verify all fields present
        assert hasattr(response, "transformed_lines")
        assert hasattr(response, "colors")
        assert hasattr(response, "success")
        assert hasattr(response, "errors")
        assert hasattr(response, "original_lines")

    @pytest.mark.asyncio
    async def test_success_flag_with_partial_failures(self) -> None:
        """Success flag correctly reflects partial failures."""
        command = TransformThinkingCommand(
            thinking_lines=["S1", "F", "S2", "F", "S3"],
            enable_colors=False,
        )

        call_count = 0

        async def mock_compress_func(phrase: str) -> dict[str, str]:
            nonlocal call_count
            call_count += 1
            if call_count in [2, 4]:  # Failures
                raise ValueError("Fail")
            return {"color": "34", "text": "compressed"}

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
            side_effect=mock_compress_func,
        ):
            response = await TransformThinkingHandler.handle(command)

        # Partial success should still set success=False
        assert response.success is False
        # But successful lines should be compressed
        assert "compressed" in response.transformed_lines[0]
        # Failed lines should be original
        assert response.transformed_lines[1] == "F"

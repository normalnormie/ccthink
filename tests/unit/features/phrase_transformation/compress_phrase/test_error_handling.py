# ABOUTME: Tests for error handling in various failure scenarios
# ABOUTME: Verifies API errors, timeouts, network failures, and text preservation

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest
from claude_agent_sdk import AssistantMessage, TextBlock

from src.features.phrase_transformation.compress_phrase.compress_phrase_service import (
    CompressPhraseService,
)
from src.features.phrase_transformation.compress_phrase.compression_options import (
    CompressionOptions,
)


class TestErrorHandling:
    """Test error handling for various failure scenarios."""

    @pytest.mark.asyncio
    async def test_api_returns_non_json(self) -> None:
        """Verify error handling when API returns non-JSON response."""
        options = CompressionOptions(max_retries=1)
        service = CompressPhraseService(options)

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            mock_message = AssistantMessage(
                content=[TextBlock(text="This is not JSON")], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            test_phrase = "test phrase"
            result = await service.compress(test_phrase)

            assert "error" in result
            assert result["raw"] == test_phrase

    @pytest.mark.asyncio
    async def test_api_timeout_occurs(self) -> None:
        """Verify error handling when API timeout occurs."""
        options = CompressionOptions(max_retries=1)
        service = CompressPhraseService(options)

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                msg = "API timeout"
                raise TimeoutError(msg)
                yield  # Make it a generator type  # type: ignore[unreachable]

            mock_query.return_value = mock_query_gen()

            test_phrase = "test phrase"
            result = await service.compress(test_phrase)

            assert "error" in result
            assert result["raw"] == test_phrase

    @pytest.mark.asyncio
    async def test_network_failure(self) -> None:
        """Verify error handling when network fails."""
        options = CompressionOptions(max_retries=1)
        service = CompressPhraseService(options)

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                msg = "Network error"
                raise ValueError(msg)
                yield  # Make it a generator type  # type: ignore[unreachable]

            mock_query.return_value = mock_query_gen()

            test_phrase = "test phrase"
            result = await service.compress(test_phrase)

            assert "error" in result
            assert result["raw"] == test_phrase

    @pytest.mark.asyncio
    async def test_original_text_preserved_in_error_responses(self) -> None:
        """Verify original text is always preserved in error responses."""
        options = CompressionOptions(max_retries=1)
        service = CompressPhraseService(options)

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                msg = "Error"
                raise TimeoutError(msg)
                yield  # Make it a generator type  # type: ignore[unreachable]

            mock_query.return_value = mock_query_gen()

            test_phrase = "important original text"
            result = await service.compress(test_phrase)

            assert result["raw"] == test_phrase

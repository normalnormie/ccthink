# ABOUTME: Tests for different compression methods (compress, compress_streaming, compress_json)
# ABOUTME: Verifies streaming behavior, caching integration, and logging

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest
from claude_agent_sdk import AssistantMessage, TextBlock

from src.features.phrase_transformation.compress_phrase.compress_phrase_service import (
    CompressPhraseService,
)


class TestCompressionMethods:
    """Test different compression methods: compress, compress_streaming, compress_json."""

    @pytest.mark.asyncio
    async def test_compress_method_full_flow(self) -> None:
        """Verify compress() method executes full flow with cache and retry."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            mock_message = AssistantMessage(
                content=[TextBlock(text='{"color": "34", "text": "compressed"}')],
                model="claude-sonnet-4",
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            # First call
            result1 = await service.compress("test phrase")
            assert result1 == {"color": "34", "text": "compressed"}

            # Second call should use cache
            result2 = await service.compress("test phrase")
            assert result2 == {"color": "34", "text": "compressed"}
            assert mock_query.call_count == 1  # Only called once due to cache

    @pytest.mark.asyncio
    async def test_compress_streaming_yields_chunks(self) -> None:
        """Verify compress_streaming() yields text chunks as they arrive."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            # Mock multiple chunks
            messages = [
                AssistantMessage(content=[TextBlock(text='{"color":')], model="claude-sonnet-4"),
                AssistantMessage(content=[TextBlock(text=' "34",')], model="claude-sonnet-4"),
                AssistantMessage(
                    content=[TextBlock(text=' "text": "compressed"}')], model="claude-sonnet-4"
                ),
            ]

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                for msg in messages:
                    yield msg

            mock_query.return_value = mock_query_gen()

            chunks = [
                chunk async for chunk in service.compress_streaming("test phrase")
            ]

            assert len(chunks) == 3
            assert "".join(chunks) == '{"color": "34", "text": "compressed"}'

    @pytest.mark.asyncio
    async def test_compress_streaming_returns_cached_result(self) -> None:
        """Verify compress_streaming() returns cached result as single chunk."""
        service = CompressPhraseService()

        # Pre-populate cache using public API
        test_phrase = "test phrase"
        cached_result = {"color": "34", "text": "compressed"}
        service._cache.put(test_phrase, cached_result)

        chunks = [
            chunk async for chunk in service.compress_streaming(test_phrase)
        ]

        assert len(chunks) == 1
        assert chunks[0] == "compressed"

    @pytest.mark.asyncio
    async def test_compress_json_logs_streaming_output(self) -> None:
        """Verify compress_json() logs streaming output and returns parsed JSON."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query, patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.logger"
        ) as mock_logger:
            mock_message = AssistantMessage(
                content=[TextBlock(text='{"color": "34", "text": "compressed"}')],
                model="claude-sonnet-4",
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress_json("test phrase")

            assert result == {"color": "34", "text": "compressed"}
            assert mock_logger.info.called

    @pytest.mark.asyncio
    async def test_compress_json_handles_parse_errors(self) -> None:
        """Verify compress_json() returns error dict on JSON parse failure."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            mock_message = AssistantMessage(
                content=[TextBlock(text="invalid json")], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress_json("test phrase")

            assert "error" in result
            assert "Failed to parse JSON" in result["error"]
            assert result["raw"] == "invalid json"

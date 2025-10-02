# ABOUTME: Tests for JSON parsing from various response formats
# ABOUTME: Verifies handling of plain JSON, markdown-wrapped JSON, and malformed responses

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


class TestJsonParsing:
    """Test JSON parsing from various response formats."""

    @pytest.mark.asyncio
    async def test_parsing_plain_json_response(self) -> None:
        """Verify parsing of plain JSON response."""
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

            result = await service.compress("test phrase")

            assert result == {"color": "34", "text": "compressed"}

    @pytest.mark.asyncio
    async def test_parsing_markdown_wrapped_json(self) -> None:
        """Verify parsing of JSON wrapped in markdown code blocks."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            markdown_response = '```json\n{"color": "34", "text": "compressed"}\n```'
            mock_message = AssistantMessage(
                content=[TextBlock(text=markdown_response)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            assert result == {"color": "34", "text": "compressed"}

    @pytest.mark.asyncio
    async def test_handling_malformed_json(self) -> None:
        """Verify error handling for malformed JSON."""
        options = CompressionOptions(max_retries=1)
        service = CompressPhraseService(options)

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            mock_message = AssistantMessage(
                content=[TextBlock(text="{invalid json}")], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            test_phrase = "test phrase"
            result = await service.compress(test_phrase)

            assert "error" in result
            assert result["raw"] == test_phrase

    @pytest.mark.asyncio
    async def test_json_with_extra_whitespace(self) -> None:
        """Verify parsing handles extra whitespace in JSON."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            mock_message = AssistantMessage(
                content=[TextBlock(text='  \n{"color": "34", "text": "compressed"}\n  ')],
                model="claude-sonnet-4",
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            assert result == {"color": "34", "text": "compressed"}

    @pytest.mark.asyncio
    async def test_json_with_nested_objects(self) -> None:
        """Verify parsing handles JSON with nested structures."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            complex_json = '{"color": "34", "text": "compressed", "meta": {"nested": "value"}}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=complex_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            assert result["color"] == "34"
            assert result["text"] == "compressed"

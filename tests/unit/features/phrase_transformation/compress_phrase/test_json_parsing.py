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

    @pytest.mark.asyncio
    async def test_json_with_ansi_color_codes_in_values(self) -> None:
        """Verify ANSI codes are cleaned from JSON values before parsing."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            # Simulate Claude returning ANSI codes in JSON values
            ansi_json = '{"color": "\x1b[38;5;209m", "text": "compressed text"}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=ansi_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            # ANSI codes should be cleaned, leaving only clean values
            assert "color" in result
            assert "\x1b" not in result["color"]
            assert result["text"] == "compressed text"

    @pytest.mark.asyncio
    async def test_json_parsing_preserves_clean_int_values(self) -> None:
        """Verify clean integer color values are preserved correctly."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            mock_message = AssistantMessage(
                content=[TextBlock(text='{"color": "42", "text": "compressed"}')],
                model="claude-sonnet-4",
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            # Clean integer strings should parse correctly
            assert result["color"] == "42"
            assert result["text"] == "compressed"

    @pytest.mark.asyncio
    async def test_json_with_multiple_ansi_codes(self) -> None:
        """Verify multiple ANSI codes throughout response are cleaned."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            # Multiple ANSI codes in different fields
            complex_ansi = '{"color": "\x1b[38;5;209m", "text": "\x1b[1mcompressed\x1b[0m"}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=complex_ansi)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            # All ANSI codes should be cleaned
            assert "\x1b" not in result["color"]
            assert result["text"] == "compressed"
            assert "\x1b" not in result["text"]

# ABOUTME: Tests for json-repair fallback when parsing LLM-generated invalid JSON
# ABOUTME: Verifies automatic repair of unescaped quotes, missing commas, and malformed structures

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest
from claude_agent_sdk import AssistantMessage, TextBlock

from src.features.phrase_transformation.compress_phrase.compress_phrase_service import (
    CompressPhraseService,
)


class TestJsonRepairFunctionality:
    """Test json-repair fallback for LLM-generated invalid JSON."""

    @pytest.mark.asyncio
    async def test_repair_json_with_unescaped_quotes(self) -> None:
        """Verify json-repair handles unescaped quotes in JSON values."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            # Simulate the exact error from logs: unescaped quotes in text value
            invalid_json = '{"color": "231", "text": "When context["key"] contains value"}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=invalid_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            assert result["color"] == "231"
            assert "context" in result["text"]
            assert "key" in result["text"]

    @pytest.mark.asyncio
    async def test_repair_json_with_missing_commas(self) -> None:
        """Verify json-repair handles missing commas between key-value pairs."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            invalid_json = '{"color": "42" "text": "compressed"}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=invalid_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            assert result["color"] == "42"
            assert result["text"] == "compressed"

    @pytest.mark.asyncio
    async def test_repair_json_with_trailing_commas(self) -> None:
        """Verify json-repair handles trailing commas in JSON objects."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            invalid_json = '{"color": "34", "text": "compressed",}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=invalid_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            assert result["color"] == "34"
            assert result["text"] == "compressed"

    @pytest.mark.asyncio
    async def test_repair_json_with_missing_quotes_on_keys(self) -> None:
        """Verify json-repair handles missing quotes on object keys."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            invalid_json = '{color: "34", text: "compressed"}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=invalid_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            assert result["color"] == "34"
            assert result["text"] == "compressed"

    @pytest.mark.asyncio
    async def test_repair_complex_invalid_json(self) -> None:
        """Verify json-repair handles JSON with multiple issues."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            # Multiple issues: unescaped quotes, backticks, template strings
            invalid_json = '{"color": "220", "text": "When `{{ template }}` with context["var"] returns value"}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=invalid_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            assert result["color"] == "220"
            assert "template" in result["text"]
            assert "context" in result["text"]

    @pytest.mark.asyncio
    async def test_valid_json_uses_fast_path(self) -> None:
        """Verify valid JSON uses orjson fast path without repair."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query, patch(
            "src.features.phrase_transformation.compress_phrase.json_parser.repair_json"
        ) as mock_repair:
            valid_json = '{"color": "34", "text": "compressed"}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=valid_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            assert result == {"color": "34", "text": "compressed"}
            mock_repair.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_json_uses_repair_fallback(self) -> None:
        """Verify invalid JSON triggers json-repair fallback."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query, patch(
            "src.features.phrase_transformation.compress_phrase.json_parser.repair_json"
        ) as mock_repair:
            invalid_json = '{"color": "34" "text": "compressed"}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=invalid_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            # Mock repair_json to return valid result
            mock_repair.return_value = {"color": "34", "text": "compressed"}

            result = await service.compress("test phrase")

            assert result == {"color": "34", "text": "compressed"}
            mock_repair.assert_called_once()

    @pytest.mark.asyncio
    async def test_garbage_input_returns_empty_dict(self) -> None:
        """Verify json-repair returns empty dict for garbage input."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            # json-repair is very permissive and returns {} for garbage
            invalid_json = "This is not JSON at all! {[}]"
            mock_message = AssistantMessage(
                content=[TextBlock(text=invalid_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress("test phrase")

            # json-repair returns empty dict for unparseable input
            assert isinstance(result, dict)


class TestJsonRepairWithStreaming:
    """Test json-repair fallback in compress_json streaming method."""

    @pytest.mark.asyncio
    async def test_compress_json_repairs_invalid_json(self) -> None:
        """Verify compress_json uses repair fallback for invalid JSON."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            invalid_json = '{"color": "231", "text": "context["key"] value"}'
            mock_message = AssistantMessage(
                content=[TextBlock(text=invalid_json)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress_json("test phrase")

            assert result["color"] == "231"
            assert "context" in result["text"]
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_compress_json_with_garbage_input(self) -> None:
        """Verify compress_json handles garbage input gracefully."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            # json-repair is very permissive and returns empty string for non-JSON text
            invalid_response = "Not JSON at all"
            mock_message = AssistantMessage(
                content=[TextBlock(text=invalid_response)], model="claude-sonnet-4"
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.return_value = mock_query_gen()

            result = await service.compress_json("test phrase")

            # json-repair parses plain text as empty string
            assert isinstance(result, (dict, str))

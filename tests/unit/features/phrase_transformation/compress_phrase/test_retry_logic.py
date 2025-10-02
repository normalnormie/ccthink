# ABOUTME: Tests for retry logic with exponential backoff
# ABOUTME: Verifies retry behavior for various error types and delay calculation

import asyncio
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


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_successful_compression_on_first_attempt(self) -> None:
        """Verify successful compression without retries."""
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

            mock_query.side_effect = lambda *args, **kwargs: mock_query_gen()

            result = await service.compress("test phrase")

            assert result == {"color": "34", "text": "compressed"}
            assert mock_query.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_after_value_error(self) -> None:
        """Verify retry occurs after ValueError."""
        options = CompressionOptions(max_retries=2)
        service = CompressPhraseService(options)

        call_count = 0

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # First call - return invalid JSON
                    yield AssistantMessage(
                        content=[TextBlock(text="invalid json")], model="claude-sonnet-4"
                    )
                else:
                    # Second call - return valid JSON
                    yield AssistantMessage(
                        content=[TextBlock(text='{"color": "34", "text": "compressed"}')],
                        model="claude-sonnet-4",
                    )

            mock_query.side_effect = lambda *args, **kwargs: mock_query_gen()

            result = await service.compress("test phrase")

            assert result == {"color": "34", "text": "compressed"}
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_after_timeout_error(self) -> None:
        """Verify retry occurs after TimeoutError."""
        options = CompressionOptions(max_retries=2)
        service = CompressPhraseService(options)

        call_count = 0

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    msg = "API timeout"
                    raise TimeoutError(msg)
                else:
                    yield AssistantMessage(
                        content=[TextBlock(text='{"color": "34", "text": "compressed"}')],
                        model="claude-sonnet-4",
                    )

            mock_query.side_effect = lambda *args, **kwargs: mock_query_gen()

            result = await service.compress("test phrase")

            assert result == {"color": "34", "text": "compressed"}
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_after_json_decode_error(self) -> None:
        """Verify retry occurs after JSONDecodeError."""
        options = CompressionOptions(max_retries=2)
        service = CompressPhraseService(options)

        call_count = 0

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    yield AssistantMessage(
                        content=[TextBlock(text="{invalid}")], model="claude-sonnet-4"
                    )
                else:
                    yield AssistantMessage(
                        content=[TextBlock(text='{"color": "34", "text": "compressed"}')],
                        model="claude-sonnet-4",
                    )

            mock_query.side_effect = lambda *args, **kwargs: mock_query_gen()

            result = await service.compress("test phrase")

            assert result == {"color": "34", "text": "compressed"}
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_exhaustion_after_max_retries(self) -> None:
        """Verify error result after max retries exhausted."""
        options = CompressionOptions(max_retries=2)
        service = CompressPhraseService(options)

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                msg = "API timeout"
                raise TimeoutError(msg)
                yield  # Make it a generator type  # type: ignore[unreachable]

            mock_query.side_effect = lambda *args, **kwargs: mock_query_gen()

            test_phrase = "test phrase"
            result = await service.compress(test_phrase)

            assert "error" in result
            assert "Compression failed after 2 retries" in result["error"]
            assert result["raw"] == test_phrase
            assert mock_query.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_delay_exponential_backoff(self) -> None:
        """Verify retry delay uses exponential backoff: 1s -> 2s -> 4s."""
        options = CompressionOptions(
            max_retries=3,
            retry_initial_delay=1.0,
            retry_backoff_multiplier=2.0,
            retry_max_delay=10.0,
        )
        service = CompressPhraseService(options)

        delays: list[float] = []

        original_sleep = asyncio.sleep

        async def mock_sleep(delay: float) -> None:
            delays.append(delay)
            await original_sleep(0)  # Don't actually wait

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query, patch("asyncio.sleep", side_effect=mock_sleep):

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                msg = "API timeout"
                raise TimeoutError(msg)
                yield  # Make it a generator type  # type: ignore[unreachable]

            mock_query.side_effect = lambda *args, **kwargs: mock_query_gen()

            await service.compress("test phrase")

            # Verify exponential backoff: 1s, 2s (no third delay as retries exhausted)
            assert len(delays) == 2
            assert delays[0] == 1.0
            assert delays[1] == 2.0

    @pytest.mark.asyncio
    async def test_retry_delay_respects_max_delay(self) -> None:
        """Verify retry delay is capped at configured max_delay."""
        options = CompressionOptions(
            max_retries=3,
            retry_initial_delay=1.0,
            retry_backoff_multiplier=10.0,
            retry_max_delay=5.0,
        )
        service = CompressPhraseService(options)

        delays: list[float] = []

        original_sleep = asyncio.sleep

        async def mock_sleep(delay: float) -> None:
            delays.append(delay)
            await original_sleep(0)

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query, patch("asyncio.sleep", side_effect=mock_sleep):

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                msg = "API timeout"
                raise TimeoutError(msg)
                yield  # Make it a generator type  # type: ignore[unreachable]

            mock_query.side_effect = lambda *args, **kwargs: mock_query_gen()

            await service.compress("test phrase")

            # First delay: 1.0 * 10^0 = 1.0
            # Second delay: 1.0 * 10^1 = 10.0, capped at 5.0
            assert len(delays) == 2
            assert delays[0] == 1.0
            assert delays[1] == 5.0

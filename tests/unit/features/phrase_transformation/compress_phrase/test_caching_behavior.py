# ABOUTME: Tests for caching functionality including hits, misses, and eviction
# ABOUTME: Verifies FIFO eviction and cache disable functionality

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


class TestCachingBehavior:
    """Test caching functionality including hits, misses, and eviction."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_result(self) -> None:
        """Verify cache hit returns cached result without API call."""
        service = CompressPhraseService()

        # Pre-populate cache
        test_phrase = "test phrase"
        cached_result = {"color": "34", "text": "compressed"}
        cache_key = service._get_cache_key(test_phrase)  # noqa: SLF001
        service._cache[cache_key] = cached_result  # noqa: SLF001

        # Should return cached result without API call
        result = await service.compress(test_phrase)

        assert result == cached_result

    @pytest.mark.asyncio
    async def test_cache_miss_triggers_api_call(self) -> None:
        """Verify cache miss results in API call."""
        service = CompressPhraseService()

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            # Mock API response
            mock_message = AssistantMessage(
                content=[TextBlock(text='{"color": "34", "text": "compressed"}')],
                model="claude-sonnet-4",
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.side_effect = lambda *args, **kwargs: mock_query_gen()

            result = await service.compress("another phrase")

            assert result == {"color": "34", "text": "compressed"}
            assert mock_query.called

    @pytest.mark.asyncio
    async def test_successful_results_go_to_cache(self) -> None:
        """Verify successful compression results go to cache."""
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

            test_phrase = "test phrase"
            await service.compress(test_phrase)

            # Verify result was cached
            cache_key = service._get_cache_key(test_phrase)  # noqa: SLF001
            assert cache_key in service._cache  # noqa: SLF001
            assert service._cache[cache_key] == {"color": "34", "text": "compressed"}  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_error_results_bypass_cache(self) -> None:
        """Verify error results bypass cache storage."""
        options = CompressionOptions(max_retries=1)
        service = CompressPhraseService(options)

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            # Mock API to raise error
            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                msg = "API timeout"
                raise TimeoutError(msg)
                yield  # Make it a generator type  # type: ignore[unreachable]

            mock_query.return_value = mock_query_gen()

            test_phrase = "test phrase"
            result = await service.compress(test_phrase)

            # Verify error was returned
            assert "error" in result
            assert result["raw"] == test_phrase

            # Verify result was NOT cached
            cache_key = service._get_cache_key(test_phrase)  # noqa: SLF001
            assert cache_key not in service._cache  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_fifo_eviction_at_cache_limit(self) -> None:
        """Verify FIFO eviction when cache reaches configured entry limit."""
        options = CompressionOptions(cache_max_size=3)
        service = CompressPhraseService(options)

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

            # Fill cache to limit
            await service.compress("phrase 1")
            await service.compress("phrase 2")
            await service.compress("phrase 3")

            # Verify cache is full
            assert len(service._cache) == 3  # noqa: SLF001

            # Compress another phrase - should evict first entry
            await service.compress("phrase 4")

            # Verify cache size is still at limit
            assert len(service._cache) == 3  # noqa: SLF001

            # Verify first entry was evicted
            key1 = service._get_cache_key("phrase 1")  # noqa: SLF001
            assert key1 not in service._cache  # noqa: SLF001

            # Verify last entry is present
            key4 = service._get_cache_key("phrase 4")  # noqa: SLF001
            assert key4 in service._cache  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_caching_disabled_when_option_is_false(self) -> None:
        """Verify caching is disabled when enable_cache is False."""
        options = CompressionOptions(enable_cache=False)
        service = CompressPhraseService(options)

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:
            mock_message = AssistantMessage(
                content=[TextBlock(text='{"color": "34", "text": "result"}')],
                model="claude-sonnet-4",
            )

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                yield mock_message

            mock_query.side_effect = lambda *args, **kwargs: mock_query_gen()

            test_phrase = "test phrase"
            await service.compress(test_phrase)

            # Verify cache is empty
            assert len(service._cache) == 0  # noqa: SLF001

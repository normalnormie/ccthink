# ABOUTME: Tests for CompressionOptions integration with CompressPhraseService
# ABOUTME: Verifies custom configuration settings are respected

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


class TestCompressionOptionsIntegration:
    """Test integration with CompressionOptions configuration."""

    @pytest.mark.asyncio
    async def test_custom_max_retries_respected(self) -> None:
        """Verify custom max_retries setting is respected."""
        options = CompressionOptions(max_retries=5)
        service = CompressPhraseService(options)

        with patch(
            "src.features.phrase_transformation.compress_phrase.compress_phrase_service.query"
        ) as mock_query:

            async def mock_query_gen(*args: Any, **kwargs: Any) -> AsyncIterator[AssistantMessage]:
                msg = "Error"
                raise TimeoutError(msg)
                yield  # Make it a generator type  # type: ignore[unreachable]

            mock_query.return_value = mock_query_gen()

            await service.compress("test phrase")

            assert mock_query.call_count == 5

    @pytest.mark.asyncio
    async def test_custom_cache_size_respected(self) -> None:
        """Verify custom cache_max_size setting is respected."""
        options = CompressionOptions(cache_max_size=2)
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

            await service.compress("phrase 1")
            await service.compress("phrase 2")
            await service.compress("phrase 3")

            # Cache should be limited to 2
            assert len(service._cache) == 2  # noqa: SLF001

    def test_default_options_when_none_provided(self) -> None:
        """Verify default options are used when none provided."""
        service = CompressPhraseService()

        assert service._options.max_retries == 3  # noqa: SLF001
        assert service._options.cache_max_size == 100  # noqa: SLF001
        assert service._options.enable_cache is True  # noqa: SLF001
        assert service._options.retry_initial_delay == 1.0  # noqa: SLF001
        assert service._options.retry_backoff_multiplier == 2.0  # noqa: SLF001
        assert service._options.retry_max_delay == 10.0  # noqa: SLF001

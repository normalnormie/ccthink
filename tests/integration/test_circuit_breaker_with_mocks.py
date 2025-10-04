# ABOUTME: Integration tests using mocks to simulate SDK failures
# ABOUTME: Tests circuit breaker behavior with deterministic failure simulation

from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.compress_phrase.compress_phrase_service import (
    CompressPhraseService,
)
from src.features.phrase_transformation.compress_phrase.compression_options import CompressionOptions


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_sdk_subprocess_failures() -> None:
    """Circuit breaker should open after consecutive SDK subprocess failures."""
    options = CompressionOptions()
    options.max_retries = 1  # Single retry for faster test
    service = CompressPhraseService(options=options)

    # Mock _compress_single to simulate SDK subprocess failure (exit code -2)
    mock_compress = AsyncMock(side_effect=Exception("Command failed with exit code -2"))

    with patch.object(service, "_compress_single", mock_compress):
        # First failure
        result1 = await service.compress("test phrase 1")
        assert "error" in result1
        assert mock_compress.call_count == 1

        # Second failure
        result2 = await service.compress("test phrase 2")
        assert "error" in result2
        assert mock_compress.call_count == 2

        # Third failure - opens circuit
        result3 = await service.compress("test phrase 3")
        assert "error" in result3
        assert mock_compress.call_count == 3

        # Circuit should be open
        assert service._circuit_breaker.is_open

        # Fourth attempt - blocked by circuit breaker, no SDK call
        result4 = await service.compress("test phrase 4")
        assert "error" in result4
        assert "temporarily disabled" in result4["error"]
        # SDK method not called because circuit is open
        assert mock_compress.call_count == 3  # Still 3, not 4


@pytest.mark.asyncio
async def test_circuit_breaker_resets_after_successful_call() -> None:
    """Circuit breaker should reset failure counter after successful compression."""
    service = CompressPhraseService()

    # Manually record 2 failures
    service._circuit_breaker.record_failure()
    service._circuit_breaker.record_failure()

    # Circuit still closed (threshold is 3)
    assert not service._circuit_breaker.is_open

    # Manually record success - resets counter
    service._circuit_breaker.record_success()
    assert not service._circuit_breaker.is_open

    # Would need 3 more failures to open (counter was reset)
    service._circuit_breaker.record_failure()
    service._circuit_breaker.record_failure()
    assert not service._circuit_breaker.is_open

    # Third failure opens circuit
    service._circuit_breaker.record_failure()
    assert service._circuit_breaker.is_open


@pytest.mark.asyncio
async def test_circuit_breaker_with_parsing_errors() -> None:
    """Circuit breaker should handle JSON parsing errors."""
    options = CompressionOptions()
    options.max_retries = 1
    service = CompressPhraseService(options=options)

    # Mock _compress_single to simulate JSON parsing failure
    mock_compress = AsyncMock(side_effect=ValueError("Failed to parse JSON"))

    with patch.object(service, "_compress_single", mock_compress):
        # Three consecutive parsing failures
        for i in range(3):
            result = await service.compress(f"phrase {i}")
            assert "error" in result

        # Circuit should be open
        assert service._circuit_breaker.is_open

        # Next call blocked
        result = await service.compress("phrase blocked")
        assert "temporarily disabled" in result["error"]

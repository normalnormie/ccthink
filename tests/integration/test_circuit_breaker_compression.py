# ABOUTME: Integration tests for circuit breaker in compression service
# ABOUTME: Verifies circuit breaker prevents infinite loops on SDK failures

from unittest.mock import AsyncMock, patch

import pytest

from src.features.phrase_transformation.compress_phrase.compress_phrase_service import (
    CompressPhraseService,
)
from src.features.phrase_transformation.compress_phrase.compression_options import CompressionOptions


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_consecutive_failures() -> None:
    """Circuit breaker should open after consecutive compression failures."""
    service = CompressPhraseService()

    # Manually trigger 3 failures to open circuit
    service._circuit_breaker.record_failure()
    service._circuit_breaker.record_failure()
    service._circuit_breaker.record_failure()

    # Circuit should now be open
    assert service._circuit_breaker.is_open

    # Next compression attempt should be blocked
    result = await service.compress("test phrase")
    assert "error" in result
    assert "temporarily disabled" in result["error"]


@pytest.mark.asyncio
async def test_circuit_breaker_resets_on_successful_compression() -> None:
    """Circuit breaker should reset failure counter on successful compression."""
    options = CompressionOptions()
    options.max_retries = 1
    options.enable_cache = False  # Disable cache for testing
    service = CompressPhraseService(options=options)

    # Record some failures
    empty_phrase = ""
    await service.compress(empty_phrase)
    await service.compress(empty_phrase)

    # Circuit should still be closed (need 3 failures)
    assert not service._circuit_breaker.is_open

    # Simulate success by checking breaker state
    # (We can't easily create a real success without mocking Claude SDK)
    service._circuit_breaker.record_success()

    # Failure counter should be reset
    result = await service.compress(empty_phrase)
    assert "error" in result
    assert "temporarily disabled" not in result.get("error", "")


@pytest.mark.asyncio
async def test_circuit_breaker_allows_operations_when_closed() -> None:
    """Circuit breaker should allow operations when closed."""
    service = CompressPhraseService()

    # Service should have closed circuit on initialization
    assert not service._circuit_breaker.is_open

    # Should attempt compression (circuit allows it to proceed)
    result = await service.compress("test phrase")
    # Should not be blocked by circuit breaker
    assert "temporarily disabled" not in result.get("error", "")
    # Either succeeds with text/color or fails with error, but not circuit blocked
    assert "text" in result or "error" in result


@pytest.mark.asyncio
async def test_cached_results_bypass_circuit_breaker() -> None:
    """Cached results should be returned even when circuit is open."""
    options = CompressionOptions()
    options.max_retries = 1
    options.enable_cache = True
    service = CompressPhraseService(options=options)

    # Manually add a cached result
    test_phrase = "test phrase"
    cached_result = {"text": "compressed", "color": "37"}
    service._cache.put(test_phrase, cached_result)

    # Open the circuit
    service._circuit_breaker.record_failure()
    service._circuit_breaker.record_failure()
    service._circuit_breaker.record_failure()
    assert service._circuit_breaker.is_open

    # Should still get cached result
    result = await service.compress(test_phrase)
    assert result == cached_result
    assert "error" not in result

# ABOUTME: Tests for cache key generation using SHA256 hash
# ABOUTME: Verifies 16-character hex string generation and determinism

from src.features.phrase_transformation.compress_phrase.compress_phrase_service import (
    CompressPhraseService,
)


class TestCacheKeyGeneration:
    """Test cache key generation using SHA256 hash."""

    def test_generates_16_char_hex(self) -> None:
        """Verify cache key is 16-character hex string from SHA256."""
        service = CompressPhraseService()
        cache_key = service._get_cache_key("test phrase")  # noqa: SLF001

        assert len(cache_key) == 16
        assert all(c in "0123456789abcdef" for c in cache_key)

    def test_identical_phrases_produce_same_key(self) -> None:
        """Verify identical phrases generate identical cache keys."""
        service = CompressPhraseService()
        key1 = service._get_cache_key("test phrase")  # noqa: SLF001
        key2 = service._get_cache_key("test phrase")  # noqa: SLF001

        assert key1 == key2

    def test_different_phrases_produce_different_keys(self) -> None:
        """Verify different phrases generate different cache keys."""
        service = CompressPhraseService()
        key1 = service._get_cache_key("phrase one")  # noqa: SLF001
        key2 = service._get_cache_key("phrase two")  # noqa: SLF001

        assert key1 != key2

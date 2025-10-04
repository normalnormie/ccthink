# ABOUTME: In-memory caching for compression results
# ABOUTME: Provides LRU-style cache with configurable size limits

import hashlib
import logging

logger = logging.getLogger(__name__)


class CompressionCache:
    """In-memory cache for compression results with FIFO eviction."""

    def __init__(self, max_size: int = 1000, *, enabled: bool = True) -> None:
        """Initialize compression cache.

        Args:
            max_size: Maximum number of cached items.
            enabled: Whether caching is enabled.
        """
        self._cache: dict[str, dict[str, str]] = {}
        self._max_size = max_size
        self._enabled = enabled

    @staticmethod
    def _get_cache_key(phrase: str) -> str:
        """Generate cache key from phrase.

        Args:
            phrase: The phrase to generate key for.

        Returns:
            16-character hash string.
        """
        return hashlib.sha256(phrase.encode()).hexdigest()[:16]

    def get(self, phrase: str) -> dict[str, str] | None:
        """Get cached compression result.

        Args:
            phrase: The phrase to look up.

        Returns:
            Cached result dict or None if not found.
        """
        if not self._enabled:
            return None

        cache_key = self._get_cache_key(phrase)
        result = self._cache.get(cache_key)

        if result:
            logger.debug("Cache hit for phrase hash: %s", cache_key)

        return result

    def put(self, phrase: str, result: dict[str, str]) -> None:
        """Add compression result to cache.

        Args:
            phrase: The original phrase.
            result: The compression result.
        """
        if not self._enabled:
            return

        cache_key = self._get_cache_key(phrase)

        # Maintain cache size limit (FIFO eviction)
        if len(self._cache) >= self._max_size:
            self._cache.pop(next(iter(self._cache)))

        self._cache[cache_key] = result

    def __len__(self) -> int:
        """Get number of items in cache.

        Returns:
            Number of cached items.
        """
        return len(self._cache)

    def __contains__(self, phrase: str) -> bool:
        """Check if phrase is in cache.

        Args:
            phrase: The phrase to check.

        Returns:
            True if phrase is cached, False otherwise.
        """
        if not self._enabled:
            return False
        cache_key = self._get_cache_key(phrase)
        return cache_key in self._cache

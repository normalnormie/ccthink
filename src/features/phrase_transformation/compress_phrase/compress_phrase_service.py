# ABOUTME: Service class for compressing phrases using Claude Agent SDK
# ABOUTME: Handles API calls, caching, retry logic, and error handling for compression

import asyncio
import hashlib
import logging
from collections.abc import AsyncIterator
from typing import Any, cast

import orjson
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

from src.shared.models import Config

from .compression_options import CompressionOptions

logger = logging.getLogger(__name__)


class CompressPhraseService:
    """Service for compressing phrases using Claude Sonnet.

    Authentication is handled automatically by claude_agent_sdk through
    Claude Code's internal configuration (~/.claude.json).
    """

    def __init__(
        self, options: CompressionOptions | None = None, config: Config | None = None
    ) -> None:
        """Initialize compression service.

        Args:
            options: Configuration options. Uses defaults if not provided.
            config: Application config with claude_agent settings. Optional.
        """
        self._options = options or CompressionOptions()
        self._config = config
        self._cache: dict[str, dict[str, str]] = {}

        # Override compression prompt from config if available
        if config and config.compression_prompt:
            self._options.compression_prompt_template = config.compression_prompt

    def _build_agent_options(self) -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions from compression options and config.

        Merges settings from both sources, with compression-specific options
        taking precedence over config defaults.

        Returns:
            Configured ClaudeAgentOptions instance.
        """
        # Start with compression-specific settings
        params: dict[str, Any] = {
            "system_prompt": self._options.system_prompt,
            "allowed_tools": [],  # No tools for compression
            "max_turns": 1,  # Single-shot response
        }

        # Merge config settings if available
        if self._config and self._config.claude_agent:
            config_params = self._config.claude_agent.to_agent_options_params()
            # Config provides defaults, but compression settings override
            for key, value in config_params.items():
                if key not in params:
                    params[key] = value

        return ClaudeAgentOptions(**params)  # pyright: ignore[reportArgumentType]

    @staticmethod
    def _get_cache_key(phrase: str) -> str:
        """Generate cache key from phrase.

        Args:
            phrase: The phrase to generate key for.

        Returns:
            16-character hash string.
        """
        return hashlib.sha256(phrase.encode()).hexdigest()[:16]

    def _get_from_cache(self, phrase: str) -> dict[str, str] | None:
        """Get cached compression result.

        Args:
            phrase: The phrase to look up.

        Returns:
            Cached result dict or None if not found.
        """
        if not self._options.enable_cache:
            return None

        cache_key = self._get_cache_key(phrase)
        result = self._cache.get(cache_key)

        if result:
            logger.debug("Cache hit for phrase hash: %s", cache_key)

        return result

    def _add_to_cache(self, phrase: str, result: dict[str, str]) -> None:
        """Add compression result to cache.

        Args:
            phrase: The original phrase.
            result: The compression result.
        """
        if not self._options.enable_cache:
            return

        cache_key = self._get_cache_key(phrase)

        # Maintain cache size limit (FIFO eviction)
        if len(self._cache) >= self._options.cache_max_size:
            self._cache.pop(next(iter(self._cache)))

        self._cache[cache_key] = result

    async def _compress_with_retry(self, phrase: str) -> dict[str, str]:
        """Compress phrase with retry logic.

        Args:
            phrase: The phrase to compress.

        Returns:
            Dict with "color" and "text" keys, or "error" and "raw" on failure.
        """
        last_exception: BaseException | None = None

        for attempt in range(self._options.max_retries):
            try:
                return await self._compress_single(phrase)
            except (TimeoutError, ValueError, orjson.JSONDecodeError) as e:
                last_exception = e
                logger.warning(
                    "Compression attempt %d/%d failed: %s",
                    attempt + 1,
                    self._options.max_retries,
                    e,
                )

                if attempt < self._options.max_retries - 1:
                    delay = self._options.get_retry_delay(attempt)
                    logger.debug("Retrying in %.1fs...", delay)
                    await asyncio.sleep(delay)

        # All retries exhausted
        error_msg = f"Compression failed after {self._options.max_retries} retries"
        logger.error("%s: %s", error_msg, last_exception)

        return {
            "error": error_msg,
            "raw": phrase,
        }

    async def _compress_single(self, phrase: str) -> dict[str, str]:
        """Compress single phrase without retry.

        Args:
            phrase: The phrase to compress.

        Returns:
            Dict with "color" and "text" keys.

        Raises:
            ValueError: On JSON parsing failures.
        """
        # Configure agent options (uses config if available)
        agent_options = self._build_agent_options()

        # Format prompt
        compression_prompt = self._options.format_compression_prompt(phrase)

        # Collect response
        result_text = ""
        async for message in query(prompt=compression_prompt, options=agent_options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        result_text += block.text

        # Parse JSON from result
        if "```json" in result_text:
            json_start = result_text.find("{")
            json_end = result_text.rfind("}") + 1
            json_str = result_text[json_start:json_end]
        else:
            json_str = result_text.strip()

        try:
            return cast("dict[str, str]", orjson.loads(json_str))
        except orjson.JSONDecodeError as e:
            msg = f"Failed to parse JSON: {e}"
            raise ValueError(msg) from e

    async def compress(self, phrase: str) -> dict[str, str]:
        """Compress phrase with caching and retry logic.

        Args:
            phrase: The phrase to compress.

        Returns:
            Dict with "color" and "text" keys on success.
            Dict with "error" and "raw" keys on failure.
        """
        # Check cache first
        cached = self._get_from_cache(phrase)
        if cached:
            return cached

        # Compress with retry
        result = await self._compress_with_retry(phrase)

        # Cache successful results only
        if "error" not in result:
            self._add_to_cache(phrase, result)

        return result

    async def compress_streaming(self, phrase: str) -> AsyncIterator[str]:
        """Compress phrase with streaming output.

        Args:
            phrase: The phrase to compress.

        Yields:
            Chunks of compressed text as they arrive.
        """
        # Check cache first
        cached = self._get_from_cache(phrase)
        if cached:
            # Return cached result as single chunk
            if "text" in cached:
                yield cached["text"]
            return

        # Configure agent options (uses config if available)
        agent_options = self._build_agent_options()

        compression_prompt = self._options.format_compression_prompt(phrase)

        # Stream response chunks
        async for message in query(prompt=compression_prompt, options=agent_options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield block.text

    async def compress_json(self, phrase: str) -> dict[str, str]:
        """Compress phrase and return parsed JSON result with streaming to logger.

        This method logs streaming output and returns parsed result.

        Args:
            phrase: The phrase to compress.

        Returns:
            Dictionary with 'color' and 'text' keys, or 'error' and 'raw' on failure.
        """
        result_text = ""

        async for chunk in self.compress_streaming(phrase):
            result_text += chunk
            logger.info("%s", chunk)

        logger.info("")  # Line break after streaming

        # Parse JSON from result
        try:
            if "```json" in result_text:
                json_start = result_text.find("{")
                json_end = result_text.rfind("}") + 1
                json_str = result_text[json_start:json_end]
            else:
                json_str = result_text.strip()

            return cast("dict[str, str]", orjson.loads(json_str))
        except orjson.JSONDecodeError as e:
            return {"error": f"Failed to parse JSON: {e}", "raw": result_text}

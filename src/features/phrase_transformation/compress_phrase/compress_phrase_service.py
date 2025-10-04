# ABOUTME: Service class for compressing phrases using Claude Agent SDK
# ABOUTME: Orchestrates compression, caching, retry logic, and circuit breaker

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, TextBlock, query

from src.shared.models import Config

from .circuit_breaker import CircuitBreaker
from .compression_cache import CompressionCache
from .compression_options import CompressionOptions
from .json_parser import CompressionJsonParser

logger = logging.getLogger(__name__)


class CompressPhraseService:
    """Service for compressing phrases using Claude Sonnet.

    Authentication is handled automatically by claude_agent_sdk through
    Claude Code's internal configuration (~/.claude.json).

    Uses circuit breaker to prevent infinite retry loops when the Claude Agent
    SDK subprocess fails repeatedly.
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
        self._cache = CompressionCache(max_size=self._options.cache_max_size, enabled=self._options.enable_cache)
        self._circuit_breaker = CircuitBreaker(failure_threshold=3)

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

    async def _compress_with_retry(self, phrase: str) -> dict[str, str]:
        """Compress phrase with retry logic and circuit breaker.

        Args:
            phrase: The phrase to compress.

        Returns:
            Dict with "color" and "text" keys, or "error" and "raw" on failure.
        """
        # Check circuit breaker
        if self._circuit_breaker.is_open:
            logger.debug("Circuit breaker open - skipping compression")
            return {"error": "Compression temporarily disabled", "raw": phrase}

        last_exception: BaseException | None = None

        for attempt in range(self._options.max_retries):
            try:
                result = await self._compress_single(phrase)
                self._circuit_breaker.record_success()
                return result
            except Exception as e:  # noqa: BLE001 - Must catch all SDK subprocess errors to prevent infinite loops
                last_exception = e
                logger.warning("Compression attempt %d/%d failed: %s", attempt + 1, self._options.max_retries, e)

                if attempt < self._options.max_retries - 1:
                    delay = self._options.get_retry_delay(attempt)
                    logger.debug("Retrying in %.1fs...", delay)
                    await asyncio.sleep(delay)

        # All retries exhausted
        self._circuit_breaker.record_failure()
        error_msg = f"Compression failed after {self._options.max_retries} retries"
        logger.error("%s: %s", error_msg, last_exception)

        return {"error": error_msg, "raw": phrase}

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

        try:
            return CompressionJsonParser.parse(result_text, strip_ansi=True)
        except Exception as e:
            logger.exception("JSON parsing failed. Raw: %s", result_text[:200])
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
        cached = self._cache.get(phrase)
        if cached:
            return cached

        # Compress with retry
        result = await self._compress_with_retry(phrase)

        # Cache successful results only
        if "error" not in result:
            self._cache.put(phrase, result)

        return result

    async def compress_streaming(self, phrase: str) -> AsyncIterator[str]:
        """Compress phrase with streaming output.
        Args:
            phrase: The phrase to compress.
        Yields:
            Chunks of compressed text as they arrive.
        """
        # Check cache first
        cached = self._cache.get(phrase)
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

        try:
            return CompressionJsonParser.parse(result_text, strip_ansi=False)
        except Exception as e:  # noqa: BLE001 - Graceful degradation for all parsing errors
            return {"error": f"Failed to parse JSON: {e}", "raw": result_text}

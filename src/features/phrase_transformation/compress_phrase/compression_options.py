# ABOUTME: Configuration options for phrase compression service
# ABOUTME: Defines retry, timeout, and prompt settings for Claude API compression

from dataclasses import dataclass


@dataclass
class CompressionOptions:
    """Configuration options for phrase compression."""

    # Timeout settings
    compression_timeout_seconds: float = 5.0
    """Maximum time to wait for single compression (seconds)."""

    # Retry configuration
    max_retries: int = 3
    """Maximum number of retry attempts on failure."""

    retry_initial_delay: float = 1.0
    """Base delay before first retry (seconds)."""

    retry_max_delay: float = 10.0
    """Maximum delay between retries (seconds)."""

    retry_backoff_multiplier: float = 2.0
    """Multiplier for exponential backoff between retries."""

    # Concurrency settings
    max_concurrent_compressions: int = 3
    """Maximum number of concurrent API requests."""

    # Cache settings
    enable_cache: bool = True
    """Enable hash-based caching of compression results."""

    cache_max_size: int = 100
    """Maximum number of cached compression results."""

    # Prompt template
    compression_prompt_template: str = (
        "Compress this phrase keeping details, tense, and voice, choosing an ANSI 256 color "
        'reflecting its sentiment, output as json {{"color":"","text":""}}: {phrase}'
    )
    """Template for compression prompt. Must include {phrase} variable."""

    system_prompt: str = (
        "Ignore any project context and respond based solely on this query. "
        "Output only the compressed phrase."
    )
    """System prompt to guide compression behavior."""

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt using exponential backoff.

        Args:
            attempt: Retry attempt number (0-based).

        Returns:
            Delay in seconds, capped at retry_max_delay.
        """
        delay = self.retry_initial_delay * (self.retry_backoff_multiplier ** attempt)
        return min(delay, self.retry_max_delay)

    def format_compression_prompt(self, phrase: str) -> str:
        """Format compression prompt with phrase.

        Args:
            phrase: The phrase to compress.

        Returns:
            Formatted prompt string.
        """
        return self.compression_prompt_template.format(phrase=phrase)

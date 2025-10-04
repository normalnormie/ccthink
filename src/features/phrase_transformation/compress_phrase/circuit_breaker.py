# ABOUTME: Circuit breaker implementation to prevent infinite retry loops
# ABOUTME: Tracks consecutive failures and temporarily disables operations

import logging

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Prevents infinite retry loops by tracking consecutive failures.

    After a threshold of consecutive failures, the circuit "opens" and
    operations are temporarily disabled to prevent system overload.
    """

    def __init__(self, failure_threshold: int = 3) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening circuit.
        """
        self._consecutive_failures = 0
        self._is_open = False
        self._failure_threshold = failure_threshold

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (operations disabled).

        Returns:
            True if circuit is open, False otherwise.
        """
        return self._is_open

    def record_success(self) -> None:
        """Record successful operation and reset failure counter."""
        self._consecutive_failures = 0
        if self._is_open:
            logger.info("Circuit breaker closed - operations resumed")
            self._is_open = False

    def record_failure(self) -> None:
        """Record failed operation and potentially open circuit."""
        self._consecutive_failures += 1

        if self._consecutive_failures >= self._failure_threshold and not self._is_open:
            self._is_open = True
            logger.error(
                "Circuit breaker opened after %d consecutive failures - operations disabled",
                self._consecutive_failures,
            )

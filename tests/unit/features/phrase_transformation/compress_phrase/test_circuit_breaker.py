# ABOUTME: Unit tests for CircuitBreaker class
# ABOUTME: Verifies failure tracking, threshold behavior, and reset logic

from src.features.phrase_transformation.compress_phrase.circuit_breaker import CircuitBreaker


def test_circuit_breaker_starts_closed() -> None:
    """Circuit breaker should start in closed state."""
    breaker = CircuitBreaker(failure_threshold=3)
    assert not breaker.is_open


def test_circuit_breaker_opens_after_threshold_failures() -> None:
    """Circuit breaker should open after reaching failure threshold."""
    breaker = CircuitBreaker(failure_threshold=3)

    # Record failures up to threshold
    breaker.record_failure()
    assert not breaker.is_open

    breaker.record_failure()
    assert not breaker.is_open

    breaker.record_failure()
    assert breaker.is_open


def test_circuit_breaker_resets_on_success() -> None:
    """Circuit breaker should reset failure counter on success."""
    breaker = CircuitBreaker(failure_threshold=3)

    # Record some failures
    breaker.record_failure()
    breaker.record_failure()
    assert not breaker.is_open

    # Success resets counter
    breaker.record_success()
    assert not breaker.is_open

    # Should need 3 more failures to open
    breaker.record_failure()
    breaker.record_failure()
    assert not breaker.is_open

    breaker.record_failure()
    assert breaker.is_open


def test_circuit_breaker_closes_on_success_after_open() -> None:
    """Circuit breaker should close when recording success after being open."""
    breaker = CircuitBreaker(failure_threshold=3)

    # Open the circuit
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.is_open

    # Success closes circuit
    breaker.record_success()
    assert not breaker.is_open


def test_circuit_breaker_custom_threshold() -> None:
    """Circuit breaker should respect custom failure threshold."""
    breaker = CircuitBreaker(failure_threshold=5)

    # Record 4 failures - should stay closed
    for _ in range(4):
        breaker.record_failure()
    assert not breaker.is_open

    # 5th failure opens circuit
    breaker.record_failure()
    assert breaker.is_open


def test_circuit_breaker_multiple_failures_when_open() -> None:
    """Recording failures when circuit is open should not cause issues."""
    breaker = CircuitBreaker(failure_threshold=2)

    # Open the circuit
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.is_open

    # Additional failures when open should be safe
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.is_open


def test_circuit_breaker_threshold_one() -> None:
    """Circuit breaker with threshold=1 should open on first failure."""
    breaker = CircuitBreaker(failure_threshold=1)

    assert not breaker.is_open
    breaker.record_failure()
    assert breaker.is_open

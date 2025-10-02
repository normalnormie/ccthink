# CompressPhraseService Test Suite

Comprehensive unit tests for the CompressPhraseService class with 98% code coverage.

## Test Organization

Tests are organized into separate files by functionality:

### test_cache_key_generation.py

- Tests SHA256 hash-based cache key generation
- Verifies 16-character hex string output
- Tests deterministic key generation for identical phrases
- Tests unique keys for different phrases

### test_caching_behavior.py

- Cache hit/miss scenarios
- Successful result caching
- Error result bypass (errors not cached)
- FIFO eviction at cache limit
- Cache disable functionality

### test_retry_logic.py

- Successful compression on first attempt
- Retry after ValueError, TimeoutError, JSONDecodeError
- Exhaustion after max retries
- Exponential backoff delay calculation (1s -> 2s -> 4s)
- Max delay cap enforcement

### test_json_parsing.py

- Plain JSON response parsing
- Markdown-wrapped JSON parsing (`json ... `)
- Malformed JSON error handling
- Extra whitespace handling
- Nested object support

### test_compression_methods.py

- compress() method full flow (cache + retry)
- compress_streaming() chunk yielding
- compress_streaming() cached result handling
- compress_json() logging and parsing
- compress_json() error handling

### test_error_handling.py

- Non-JSON API responses
- API timeout errors
- Network failures
- Original text preservation in error responses

### test_compression_options.py

- Custom max_retries configuration
- Custom cache_max_size configuration
- Default options validation

## Test Coverage

**Overall Coverage: 98%**

- compress_phrase_service.py: 97% (101/104 statements)
- compression_options.py: 100% (28/28 statements)

Only 3 uncovered lines in compress_phrase_service.py (lines 244-246) in the compress_json error handling path.

## Running Tests

```bash
# Run all compress phrase tests
uv run pytest tests/unit/features/phrase_transformation/compress_phrase/ -v

# Run with coverage
uv run pytest tests/unit/features/phrase_transformation/compress_phrase/ \
    --cov=src/features/phrase_transformation/compress_phrase --cov-report=term-missing

# Run specific file
uv run pytest tests/unit/features/phrase_transformation/compress_phrase/test_caching_behavior.py -v

# Run specific case
uv run pytest tests/unit/features/phrase_transformation/compress_phrase/test_retry_logic.py::TestRetryLogic::test_retry_after_value_error -v
```

## Linting

All tests pass ruff and mypy linting:

```bash
# Run ruff
uv run ruff check tests/unit/features/phrase_transformation/compress_phrase/

# Run mypy
uv run mypy tests/unit/features/phrase_transformation/compress_phrase/ --config-file mypy.ini
```

## Design Principles

1. **Isolated Tests**: Each case is independent with proper setup/teardown
2. **Mocked Dependencies**: claude_agent_sdk query function is mocked for all cases
3. **Clear Assertions**: Specific assertions with helpful error messages
4. **Comprehensive Coverage**: Tests cover success paths, error paths, and edge cases
5. **Type Safety**: Full type annotations with mypy validation
6. **Performance**: All tests complete in ~25 seconds total

## Key Techniques

- **Mock Side Effects**: Using `side_effect` for independent generators on each call
- **Async Iterator Mocking**: Proper async generator mocking for streaming responses
- **Private Member Testing**: Testing internal methods with `# noqa: SLF001` annotations
- **Error Message Variables**: Exception messages assigned to variables for linting compliance
- **Type Ignores**: Strategic use of `# type: ignore[unreachable]` for generator type hints

## Total Count

**33 comprehensive unit tests** covering all major functionality of CompressPhraseService.

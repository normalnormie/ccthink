# ABOUTME: Unit tests for ColoredFormatter fallback behavior
# ABOUTME: Tests format_with_fallback() method for graceful degradation

import logging
import os
import sys
from unittest.mock import patch

import pytest

from src.features.phrase_transformation.colored_output.colored_formatter import (
    ColoredFormatter,
)


class TestFallbackBehavior:
    """Tests for format_with_fallback method."""

    def test_fallback_returns_colored_text_when_enabled_and_valid(self) -> None:
        """format_with_fallback returns colored text when colors enabled and valid color."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            result = formatter.format_with_fallback("test", 34)
            assert result == "\x1b[38;5;34mtest\x1b[0m"

    def test_fallback_returns_plain_text_when_colors_disabled(self) -> None:
        """format_with_fallback returns plain text when colors disabled."""
        formatter = ColoredFormatter(enable_colors=False)
        result = formatter.format_with_fallback("test", 34)
        assert result == "test"

    def test_fallback_returns_fallback_text_when_colors_disabled(self) -> None:
        """format_with_fallback returns fallback text when provided and colors disabled."""
        formatter = ColoredFormatter(enable_colors=False)
        result = formatter.format_with_fallback("test", 34, fallback_text="FALLBACK")
        assert result == "FALLBACK"

    def test_fallback_returns_plain_text_for_invalid_color(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """format_with_fallback returns plain text for invalid color."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            with caplog.at_level(logging.WARNING):
                result = formatter.format_with_fallback("test", 300)
            assert result == "test"
            assert "Invalid color code 300" in caplog.text

    def test_fallback_returns_fallback_text_for_invalid_color(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """format_with_fallback returns fallback text for invalid color when provided."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            with caplog.at_level(logging.WARNING):
                result = formatter.format_with_fallback("test", -1, fallback_text="FALLBACK")
            assert result == "FALLBACK"
            assert "Invalid color code -1" in caplog.text

    def test_fallback_handles_terminal_not_supporting_colors(self) -> None:
        """format_with_fallback returns plain text when terminal does not support colors."""
        with patch.object(sys.stdout, "isatty", return_value=False):
            formatter = ColoredFormatter(enable_colors=True)
            result = formatter.format_with_fallback("test", 34)
            assert result == "test"

    def test_fallback_with_enable_colors_true(self) -> None:
        """format_with_fallback works correctly with enable_colors=True."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            result = formatter.format_with_fallback("test", 34)
            assert "\x1b[38;5;34m" in result

    def test_fallback_with_enable_colors_false(self) -> None:
        """format_with_fallback works correctly with enable_colors=False."""
        formatter = ColoredFormatter(enable_colors=False)
        result = formatter.format_with_fallback("test", 34)
        assert "\x1b[" not in result
        assert result == "test"

    def test_fallback_with_none_fallback_text(self) -> None:
        """format_with_fallback uses original text when fallback_text is None."""
        formatter = ColoredFormatter(enable_colors=False)
        result = formatter.format_with_fallback("original", 34, fallback_text=None)
        assert result == "original"

# ABOUTME: Unit tests for ColoredFormatter edge cases
# ABOUTME: Tests special scenarios like empty strings, unicode, and initialization

import os
import sys
from unittest.mock import patch

from src.features.phrase_transformation.colored_output.colored_formatter import (
    ColoredFormatter,
)


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_text_string(self) -> None:
        """Format handles empty text string."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            result = formatter.format("", 34)
            assert result == "\x1b[38;5;34m\x1b[0m"

    def test_text_with_multiple_newlines(self) -> None:
        """Format handles text with multiple newlines."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            text = "line1\nline2\nline3"
            result = formatter.format(text, 34)
            assert result == f"\x1b[38;5;34m{text}\x1b[0m"

    def test_text_with_tabs_and_special_whitespace(self) -> None:
        """Format handles text with tabs and special whitespace."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            text = "tab\there\tand\rcarriage\fform"
            result = formatter.format(text, 34)
            assert result == f"\x1b[38;5;34m{text}\x1b[0m"

    def test_unicode_emoji_text(self) -> None:
        """Format handles Unicode emoji text."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            text = "Hello 👋 World 🌍"
            result = formatter.format(text, 34)
            assert result == f"\x1b[38;5;34m{text}\x1b[0m"

    def test_text_with_mixed_unicode(self) -> None:
        """Format handles text with mixed Unicode scripts."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            text = "English 中文 Русский العربية"
            result = formatter.format(text, 34)
            assert result == f"\x1b[38;5;34m{text}\x1b[0m"

    def test_very_long_text_performance(self) -> None:
        """Format handles very long text without performance issues."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            text = "x" * 100000
            result = formatter.format(text, 34)
            assert result.startswith("\x1b[38;5;34m")
            assert result.endswith("\x1b[0m")
            assert text in result

    def test_initialization_with_terminal_detection(self) -> None:
        """Initialization properly detects terminal capabilities."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            assert formatter._enable_colors is True  # noqa: SLF001

    def test_initialization_with_dumb_terminal(self) -> None:
        """Initialization disables colors for dumb terminal even when requested."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "dumb"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            assert formatter._enable_colors is False  # noqa: SLF001

    def test_initialization_explicit_disable(self) -> None:
        """Initialization respects explicit disable regardless of terminal."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=False)
            assert formatter._enable_colors is False  # noqa: SLF001

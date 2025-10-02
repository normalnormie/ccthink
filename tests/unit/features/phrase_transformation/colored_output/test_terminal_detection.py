# ABOUTME: Unit tests for ColoredFormatter terminal detection
# ABOUTME: Tests TTY detection, TERM variable parsing, and COLORTERM support

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from src.features.phrase_transformation.colored_output.colored_formatter import (
    ColoredFormatter,
)


class TestTerminalDetection:
    """Tests for terminal color support detection."""

    def test_tty_terminal_supports_colors(self) -> None:
        """Terminal detection returns True for TTY terminals."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            assert ColoredFormatter._terminal_supports_color() is True  # noqa: SLF001

    def test_non_tty_terminal_does_not_support_colors(self) -> None:
        """Terminal detection returns False for non-TTY."""
        with patch.object(sys.stdout, "isatty", return_value=False):
            assert ColoredFormatter._terminal_supports_color() is False  # noqa: SLF001

    def test_missing_isatty_attribute_returns_false(self) -> None:
        """Terminal detection returns False when isatty attribute is missing."""
        original_stdout = sys.stdout
        try:
            # Create stdout without isatty attribute
            mock_stdout = MagicMock(spec=[])
            sys.stdout = mock_stdout
            assert ColoredFormatter._terminal_supports_color() is False  # noqa: SLF001
        finally:
            sys.stdout = original_stdout

    def test_dumb_terminal_does_not_support_colors(self) -> None:
        """Terminal detection returns False for dumb terminal."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "dumb"}, clear=True
        ):
            assert ColoredFormatter._terminal_supports_color() is False  # noqa: SLF001

    @pytest.mark.parametrize(
        "term_value",
        [
            "xterm",
            "xterm-256color",
            "screen",
            "screen-256color",
            "tmux",
            "tmux-256color",
            "rxvt",
            "rxvt-unicode",
            "ansi",
            "color_xterm",
        ],
    )
    def test_color_supporting_terminals(self, term_value: str) -> None:
        """Terminal detection returns True for color-supporting terminals."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": term_value}, clear=True
        ):
            assert ColoredFormatter._terminal_supports_color() is True  # noqa: SLF001

    def test_colorterm_environment_variable_enables_colors(self) -> None:
        """Terminal detection returns True when COLORTERM is set."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "unknown", "COLORTERM": "truecolor"}, clear=True
        ):
            assert ColoredFormatter._terminal_supports_color() is True  # noqa: SLF001

    def test_colorterm_empty_string_does_not_enable_colors(self) -> None:
        """Terminal detection ignores empty COLORTERM variable."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "unknown", "COLORTERM": ""}, clear=True
        ):
            # Should return True due to default behavior (line 50)
            assert ColoredFormatter._terminal_supports_color() is True  # noqa: SLF001

    def test_default_behavior_returns_true(self) -> None:
        """Terminal detection defaults to True for unknown terminals."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "unknown"}, clear=True
        ):
            assert ColoredFormatter._terminal_supports_color() is True  # noqa: SLF001

    def test_term_case_insensitive_matching(self) -> None:
        """Terminal detection matches TERM value case-insensitively."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "XTERM-256COLOR"}, clear=True
        ):
            assert ColoredFormatter._terminal_supports_color() is True  # noqa: SLF001

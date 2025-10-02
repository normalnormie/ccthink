# ABOUTME: Unit tests for ColoredFormatter ANSI escape sequence generation
# ABOUTME: Tests format() method with various colors, text types, and edge cases

import logging
import os
import sys
from unittest.mock import patch

import pytest

from src.features.phrase_transformation.colored_output.colored_formatter import (
    ColoredFormatter,
)


class TestAnsiFormatting:
    """Tests for ANSI escape sequence generation."""

    def test_format_generates_correct_ansi_sequence(self) -> None:
        """Format generates correct ANSI sequence for colored text."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            result = formatter.format("test", 34)
            assert result == "\x1b[38;5;34mtest\x1b[0m"

    @pytest.mark.parametrize(
        ("color", "expected_prefix"),
        [
            (0, "\x1b[38;5;0m"),
            (34, "\x1b[38;5;34m"),
            (128, "\x1b[38;5;128m"),
            (255, "\x1b[38;5;255m"),
        ],
    )
    def test_format_with_various_colors(self, color: int, expected_prefix: str) -> None:
        """Format generates correct sequences for various colors."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            result = formatter.format("text", color)
            assert result == f"{expected_prefix}text\x1b[0m"

    @pytest.mark.parametrize(
        "text",
        [
            "simple",
            "text with spaces",
            "special!@#$%^&*()chars",
            "multiple\nlines",
            "unicode 你好 مرحبا",
            "",
        ],
    )
    def test_format_with_various_text_strings(self, text: str) -> None:
        """Format handles various text strings correctly."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            result = formatter.format(text, 34)
            assert result == f"\x1b[38;5;34m{text}\x1b[0m"

    def test_reset_sequence_always_appended(self) -> None:
        """Format always appends reset sequence."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            result = formatter.format("test", 100)
            assert result.endswith("\x1b[0m")

    def test_format_with_colors_disabled_returns_plain_text(self) -> None:
        """Format returns plain text when colors are disabled."""
        formatter = ColoredFormatter(enable_colors=False)
        result = formatter.format("test", 34)
        assert result == "test"
        assert "\x1b[" not in result

    def test_format_with_invalid_color_returns_plain_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Format returns plain text with warning for invalid color."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            with caplog.at_level(logging.WARNING):
                result = formatter.format("test", 256)
            assert result == "test"
            assert "Invalid color code 256" in caplog.text

    def test_format_preserves_existing_ansi_codes(self) -> None:
        """Format preserves existing ANSI codes in text."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            text_with_ansi = "\x1b[1mbold\x1b[0m text"
            result = formatter.format(text_with_ansi, 34)
            assert result == f"\x1b[38;5;34m{text_with_ansi}\x1b[0m"

    def test_format_with_very_long_text(self) -> None:
        """Format handles very long text strings."""
        with patch.object(sys.stdout, "isatty", return_value=True), patch.dict(
            os.environ, {"TERM": "xterm"}, clear=True
        ):
            formatter = ColoredFormatter(enable_colors=True)
            long_text = "x" * 10000
            result = formatter.format(long_text, 34)
            assert result == f"\x1b[38;5;34m{long_text}\x1b[0m"
            assert len(result) == len(long_text) + len("\x1b[38;5;34m") + len("\x1b[0m")

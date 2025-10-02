# ABOUTME: Formatter for colored terminal output using ANSI 256 color codes
# ABOUTME: Handles color validation, terminal capability detection, and ANSI escaping

import logging
import os
import sys

logger = logging.getLogger(__name__)


class ColoredFormatter:
    """Formatter that adds ANSI 256 colors to text output."""

    def __init__(self, enable_colors: bool = True) -> None:  # noqa: FBT001, FBT002
        """Initialize colored formatter.

        Args:
            enable_colors: Whether to enable colored output. Defaults to True.
        """
        self._enable_colors = enable_colors and self._terminal_supports_color()

    @staticmethod
    def _terminal_supports_color() -> bool:
        """Detect if terminal supports ANSI colors.

        Returns:
            True if terminal supports colors, False otherwise.
        """
        # Check if running in a TTY
        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            return False

        # Check TERM environment variable
        term = os.getenv("TERM", "")
        if term == "dumb":
            return False

        # Check for common color-supporting terminals
        if any(
            color_term in term.lower()
            for color_term in ["color", "ansi", "xterm", "screen", "tmux", "rxvt"]
        ):
            return True

        # Check COLORTERM environment variable
        if os.getenv("COLORTERM"):
            return True

        # Default to True for most terminals
        return True

    @staticmethod
    def _validate_color(color: int) -> bool:
        """Validate ANSI 256 color code.

        Args:
            color: Color code to validate.

        Returns:
            True if color is valid (0-255), False otherwise.
        """
        return 0 <= color <= 255

    def format(self, text: str, color: int) -> str:
        """Format text with ANSI 256 color.

        Args:
            text: The text to format.
            color: ANSI 256 color code (0-255).

        Returns:
            Formatted text with color codes if enabled, plain text otherwise.
        """
        # If colors disabled, return plain text
        if not self._enable_colors:
            return text

        # Validate color code
        if not self._validate_color(color):
            logger.warning("Invalid color code %d, using plain text", color)
            return text

        # Apply ANSI 256 color
        return f"\x1b[38;5;{color}m{text}\x1b[0m"

    def format_with_fallback(self, text: str, color: int, fallback_text: str | None = None) -> str:
        """Format text with color, falling back to alternative text on failure.

        Args:
            text: The text to format.
            color: ANSI 256 color code (0-255).
            fallback_text: Text to use if formatting fails. Defaults to plain text.

        Returns:
            Formatted text with color, or fallback text if formatting fails.
        """
        if not self._enable_colors:
            return fallback_text or text

        if not self._validate_color(color):
            logger.warning("Invalid color code %d, using fallback", color)
            return fallback_text or text

        return self.format(text, color)

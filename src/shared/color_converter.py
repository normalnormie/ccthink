# ABOUTME: Color conversion utility for CSS colors to ANSI 256 codes
# ABOUTME: Converts CSS color names and hex values to terminal-compatible ANSI 256 color codes

import logging
import re

import webcolors

logger = logging.getLogger(__name__)


class ColorConverter:
    """Convert CSS color names and hex values to ANSI 256 color codes."""

    # ANSI 256 color cube increments (6x6x6 color cube)
    COLOR_CUBE_INCREMENTS = (0x00, 0x5F, 0x87, 0xAF, 0xD7, 0xFF)

    @staticmethod
    def _strip_hash(hex_color: str) -> str:
        """Strip leading hash from hex color if present.

        Args:
            hex_color: Hex color string, possibly with leading #.

        Returns:
            Hex color string without leading #.
        """
        return hex_color.lstrip("#")

    @staticmethod
    def _rgb_to_ansi256(r: int, g: int, b: int) -> int:
        """Convert RGB values to closest ANSI 256 color code.

        Uses the xterm 256-color palette:
        - 0-15: Standard colors
        - 16-231: 6x6x6 color cube
        - 232-255: Grayscale

        Args:
            r: Red component (0-255).
            g: Green component (0-255).
            b: Blue component (0-255).

        Returns:
            ANSI 256 color code (0-255).
        """
        # Check if color is grayscale
        if r == g == b:
            # Use grayscale ramp (232-255)
            if r < 8:
                return 16  # Black
            if r > 248:
                return 231  # White
            return round(((r - 8) / 247) * 23) + 232

        # Use 6x6x6 color cube (16-231)
        # Map RGB values to cube indices
        increments = ColorConverter.COLOR_CUBE_INCREMENTS

        def _get_closest_index(value: int) -> int:
            """Get closest color cube index for a color component.

            Returns:
                Index into COLOR_CUBE_INCREMENTS (0-5).
            """
            for i in range(len(increments) - 1):
                lower, upper = increments[i], increments[i + 1]
                if lower <= value <= upper:
                    # Return index of closest increment
                    return i if abs(value - lower) < abs(value - upper) else i + 1
            return len(increments) - 1

        r_idx = _get_closest_index(r)
        g_idx = _get_closest_index(g)
        b_idx = _get_closest_index(b)

        # Calculate ANSI 256 code: 16 + 36*r + 6*g + b
        return 16 + (36 * r_idx) + (6 * g_idx) + b_idx

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple.

        Args:
            hex_color: Hex color string (with or without #).

        Returns:
            RGB tuple (r, g, b) with values 0-255.

        Raises:
            ValueError: If hex color format is invalid.
        """
        hex_color = ColorConverter._strip_hash(hex_color)

        # Validate hex format
        if not re.match(r"^[0-9A-Fa-f]{6}$", hex_color):
            msg = f"Invalid hex color format: #{hex_color}"
            raise ValueError(msg)

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        return r, g, b

    @classmethod
    def css_to_ansi256(cls, color_value: str) -> int:
        """Convert CSS color name or hex value to ANSI 256 color code.

        Supports:
        - CSS color names: 'lightblue', 'red', 'magenta'
        - Hex values: '#A5D8FF', '#FFFACD'

        Args:
            color_value: CSS color name or hex color string.

        Returns:
            ANSI 256 color code (0-255).

        Raises:
            ValueError: If color format is invalid or unsupported.
        """
        color_value = color_value.strip()

        # Try hex format first
        if color_value.startswith("#"):
            try:
                r, g, b = cls._hex_to_rgb(color_value)
                return cls._rgb_to_ansi256(r, g, b)
            except ValueError as e:
                logger.warning("Invalid hex color %s: %s", color_value, e)
                raise

        # Try CSS color name
        try:
            rgb_tuple = webcolors.name_to_rgb(color_value)
            return cls._rgb_to_ansi256(rgb_tuple.red, rgb_tuple.green, rgb_tuple.blue)
        except ValueError:
            # Not a valid CSS color name, try as hex without #
            try:
                r, g, b = cls._hex_to_rgb(color_value)
                return cls._rgb_to_ansi256(r, g, b)
            except ValueError:
                logger.exception("Invalid color value: %s", color_value)
                msg = (
                    f"Invalid color value '{color_value}'. "
                    "Use CSS color names (e.g., 'lightblue') or hex values (e.g., '#A5D8FF')"
                )
                raise ValueError(msg) from None

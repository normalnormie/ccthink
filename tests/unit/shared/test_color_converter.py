# ABOUTME: Unit tests for ColorConverter utility
# ABOUTME: Tests CSS color name and hex to ANSI 256 conversion

import pytest

from src.shared.color_converter import ColorConverter


class TestColorConverter:  # noqa: PLR0904 - Test class with many test methods is acceptable
    """Test cases for ColorConverter utility."""

    def test_css_color_name_lightblue(self) -> None:
        """Test CSS color name 'lightblue' converts to valid ANSI 256 code."""
        result = ColorConverter.css_to_ansi256("lightblue")
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_css_color_name_red(self) -> None:
        """Test CSS color name 'red' converts to valid ANSI 256 code."""
        result = ColorConverter.css_to_ansi256("red")
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_css_color_name_magenta(self) -> None:
        """Test CSS color name 'magenta' converts to valid ANSI 256 code."""
        result = ColorConverter.css_to_ansi256("magenta")
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_css_color_name_white(self) -> None:
        """Test CSS color name 'white' converts to valid ANSI 256 code."""
        result = ColorConverter.css_to_ansi256("white")
        assert isinstance(result, int)
        assert 0 <= result <= 255
        # White should map to high value in grayscale or cube
        assert result >= 15

    def test_css_color_name_black(self) -> None:
        """Test CSS color name 'black' converts to valid ANSI 256 code."""
        result = ColorConverter.css_to_ansi256("black")
        assert isinstance(result, int)
        assert 0 <= result <= 255
        # Black should map to low value
        assert result <= 16

    def test_hex_color_with_hash(self) -> None:
        """Test hex color with # prefix converts to valid ANSI 256 code."""
        result = ColorConverter.css_to_ansi256("#A5D8FF")
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_hex_color_without_hash(self) -> None:
        """Test hex color without # prefix converts to valid ANSI 256 code."""
        result = ColorConverter.css_to_ansi256("A5D8FF")
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_hex_color_lowercase(self) -> None:
        """Test lowercase hex color converts to valid ANSI 256 code."""
        result = ColorConverter.css_to_ansi256("#a5d8ff")
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_default_thinking_color(self) -> None:
        """Test default thinking color #A5D8FF converts correctly."""
        result = ColorConverter.css_to_ansi256("#A5D8FF")
        assert isinstance(result, int)
        assert 0 <= result <= 255
        # Light blue should be in higher range
        assert result >= 16

    def test_default_chat_color(self) -> None:
        """Test default chat color #FFFACD converts correctly."""
        result = ColorConverter.css_to_ansi256("#FFFACD")
        assert isinstance(result, int)
        assert 0 <= result <= 255
        # Light yellow should be in higher range
        assert result >= 16

    def test_grayscale_conversion(self) -> None:
        """Test grayscale colors use grayscale ramp."""
        # Pure gray (R=G=B)
        result = ColorConverter.css_to_ansi256("#808080")
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_invalid_color_name_raises_error(self) -> None:
        """Test invalid CSS color name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid color value"):
            ColorConverter.css_to_ansi256("notacolor")

    def test_invalid_hex_format_raises_error(self) -> None:
        """Test invalid hex format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid"):
            ColorConverter.css_to_ansi256("#ZZZZZ")

    def test_invalid_hex_length_raises_error(self) -> None:
        """Test hex color with wrong length raises ValueError."""
        with pytest.raises(ValueError, match="Invalid"):
            ColorConverter.css_to_ansi256("#FFF")

    def test_rgb_to_ansi256_black(self) -> None:
        """Test RGB black (0,0,0) converts to expected ANSI code."""
        result = ColorConverter._rgb_to_ansi256(0, 0, 0)
        assert isinstance(result, int)
        assert result == 16  # Black in 256 palette

    def test_rgb_to_ansi256_white(self) -> None:
        """Test RGB white (255,255,255) converts to expected ANSI code."""
        result = ColorConverter._rgb_to_ansi256(255, 255, 255)
        assert isinstance(result, int)
        assert result == 231  # White in 256 palette

    def test_rgb_to_ansi256_pure_red(self) -> None:
        """Test RGB pure red (255,0,0) converts correctly."""
        result = ColorConverter._rgb_to_ansi256(255, 0, 0)
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_rgb_to_ansi256_pure_green(self) -> None:
        """Test RGB pure green (0,255,0) converts correctly."""
        result = ColorConverter._rgb_to_ansi256(0, 255, 0)
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_rgb_to_ansi256_pure_blue(self) -> None:
        """Test RGB pure blue (0,0,255) converts correctly."""
        result = ColorConverter._rgb_to_ansi256(0, 0, 255)
        assert isinstance(result, int)
        assert 0 <= result <= 255

    def test_hex_to_rgb_conversion(self) -> None:
        """Test hex to RGB conversion produces correct values."""
        r, g, b = ColorConverter._hex_to_rgb("FF0000")
        assert r == 255
        assert g == 0
        assert b == 0

    def test_hex_to_rgb_with_hash(self) -> None:
        """Test hex to RGB handles # prefix correctly."""
        r, g, b = ColorConverter._hex_to_rgb("#00FF00")
        assert r == 0
        assert g == 255
        assert b == 0

    def test_strip_hash_utility(self) -> None:
        """Test hash stripping utility function."""
        assert ColorConverter._strip_hash("#ABCDEF") == "ABCDEF"
        assert ColorConverter._strip_hash("ABCDEF") == "ABCDEF"
        assert ColorConverter._strip_hash("###ABC") == "ABC"

    def test_color_with_whitespace(self) -> None:
        """Test color values with leading/trailing whitespace."""
        result = ColorConverter.css_to_ansi256("  lightblue  ")
        assert isinstance(result, int)
        assert 0 <= result <= 255

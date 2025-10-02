# ABOUTME: Unit tests for ColoredFormatter color validation
# ABOUTME: Tests ANSI 256 color code validation (0-255 range)

import pytest

from src.features.phrase_transformation.colored_output.colored_formatter import (
    ColoredFormatter,
)


class TestColorValidation:
    """Tests for ANSI 256 color code validation."""

    @pytest.mark.parametrize("color", [0, 1, 34, 128, 200, 255])
    def test_valid_color_range(self, color: int) -> None:
        """Color validation accepts valid colors (0-255)."""
        assert ColoredFormatter._validate_color(color) is True  # noqa: SLF001

    @pytest.mark.parametrize("color", [-1, -10, -100])
    def test_invalid_negative_colors(self, color: int) -> None:
        """Color validation rejects negative colors."""
        assert ColoredFormatter._validate_color(color) is False  # noqa: SLF001

    @pytest.mark.parametrize("color", [256, 300, 1000, 99999])
    def test_invalid_high_colors(self, color: int) -> None:
        """Color validation rejects colors above 255."""
        assert ColoredFormatter._validate_color(color) is False  # noqa: SLF001

    def test_boundary_value_zero(self) -> None:
        """Color validation accepts boundary value 0."""
        assert ColoredFormatter._validate_color(0) is True  # noqa: SLF001

    def test_boundary_value_255(self) -> None:
        """Color validation accepts boundary value 255."""
        assert ColoredFormatter._validate_color(255) is True  # noqa: SLF001

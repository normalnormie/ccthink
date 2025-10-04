# ABOUTME: JSON parsing utilities for compression results
# ABOUTME: Handles two-phase parsing with orjson and json-repair fallback

import logging
import re
from typing import cast

import orjson
from json_repair import repair_json

logger = logging.getLogger(__name__)


class CompressionJsonParser:
    """Parses JSON compression results with fallback mechanisms."""

    @staticmethod
    def parse(result_text: str, *, strip_ansi: bool = False) -> dict[str, str]:
        """Parse compression result with two-phase JSON parsing and validation.

        Args:
            result_text: Raw result text from Claude.
            strip_ansi: Whether to strip ANSI color codes first.

        Returns:
            Dict with "color" and "text" keys.

        Raises:
            ValueError: If parsing or validation fails.
        """
        # Strip ANSI codes if requested
        text = re.sub(r'\x1b\[[0-9;]*m', '', result_text) if strip_ansi else result_text

        # Extract JSON from markdown if present
        json_str = text[text.find("{"):text.rfind("}") + 1] if "```json" in text else text.strip()

        # Two-phase parsing: try orjson first, fall back to json-repair
        try:
            parsed = orjson.loads(json_str)
        except orjson.JSONDecodeError:
            parsed = repair_json(json_str, return_objects=True)

        # Validate result structure
        if not isinstance(parsed, dict) or "color" not in parsed or "text" not in parsed:
            msg = f"Invalid result structure: {parsed}"
            raise ValueError(msg)

        return cast("dict[str, str]", parsed)

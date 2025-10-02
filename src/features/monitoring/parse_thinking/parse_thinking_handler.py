# ABOUTME: Parse thinking handler implementation
# ABOUTME: Handles extraction of thinking entries from JSONL file content

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import orjson

from src.shared.models import ThinkingEntry

if TYPE_CHECKING:
    from src.features.monitoring.parse_thinking.parse_thinking_command import ParseThinkingCommand


@dataclass
class ParseThinkingResponse:
    """Response from parsing thinking entries.

    Attributes:
        entries: List of parsed thinking entries.
        end_position: File position after reading (bytes).
    """

    entries: list[ThinkingEntry]
    end_position: int


class ParseThinkingHandler:
    """Handler for parsing thinking entries from JSONL."""

    MAX_BUFFER_SIZE = 100 * 1024 * 1024  # 100MB buffer

    @staticmethod
    def handle(command: ParseThinkingCommand) -> ParseThinkingResponse:
        """Parse thinking entries from JSONL file.

        Args:
            command: Parse thinking command with file path and position.

        Returns:
            Response with parsed entries and end position.
        """
        if not command.jsonl_path.exists():
            return ParseThinkingResponse(entries=[], end_position=command.from_position)

        entries: list[ThinkingEntry] = []

        with command.jsonl_path.open("r", encoding="utf-8") as f:
            # Seek to start position
            f.seek(command.from_position)

            for line in f:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                try:
                    data = orjson.loads(stripped_line)
                    entry = ThinkingEntry.model_validate(data)

                    # Only include assistant entries with thinking content
                    if entry.type == "assistant" and entry.get_thinking_content():
                        entries.append(entry)
                except (orjson.JSONDecodeError, ValueError):
                    # Skip malformed lines
                    continue

            end_position = f.tell()

        return ParseThinkingResponse(entries=entries, end_position=end_position)

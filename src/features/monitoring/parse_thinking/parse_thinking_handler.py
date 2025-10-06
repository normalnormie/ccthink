# ABOUTME: Parse thinking handler implementation
# ABOUTME: Handles extraction of thinking entries and tool uses from JSONL file content

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import orjson

from src.shared.models import ThinkingEntry

if TYPE_CHECKING:
    from src.features.monitoring.parse_thinking.parse_thinking_command import ParseThinkingCommand
    from src.shared.tool_use_models import ToolUseEntry


@dataclass
class ParsedItem:
    """A parsed item that can be either a thinking entry or tool use.

    Attributes:
        thinking_entry: ThinkingEntry if this is a thinking item, None otherwise.
        tool_use: ToolUseEntry if this is a tool use item, None otherwise.
    """

    thinking_entry: ThinkingEntry | None = None
    tool_use: ToolUseEntry | None = None


@dataclass
class ParseThinkingResponse:
    """Response from parsing thinking entries and tool uses.

    Attributes:
        entries: List of parsed thinking entries.
        tool_uses: List of parsed tool use entries.
        ordered_items: List of parsed items in chronological order.
        end_position: File position after reading (bytes).
    """

    entries: list[ThinkingEntry]
    tool_uses: list[ToolUseEntry]
    ordered_items: list[ParsedItem]
    end_position: int


class ParseThinkingHandler:
    """Handler for parsing thinking entries from JSONL."""

    MAX_BUFFER_SIZE = 100 * 1024 * 1024  # 100MB buffer

    @staticmethod
    def _process_assistant_message(
        entry: ThinkingEntry,
        entries: list[ThinkingEntry],
        tool_uses: list[ToolUseEntry],
        ordered_items: list[ParsedItem],
        *,
        thinking_enabled: bool,
        text_enabled: bool,
    ) -> None:
        """Process assistant message content to extract thinking, text, and tool uses.

        Args:
            entry: ThinkingEntry to process.
            entries: List to append thinking/text entries to.
            tool_uses: List to append tool use entries to.
            ordered_items: List to append ordered items to.
            thinking_enabled: Whether to extract thinking content.
            text_enabled: Whether to extract text content.
        """
        from src.shared.tool_use_models import ToolUseEntry  # noqa: PLC0415

        if not isinstance(entry.message.content, list):
            return

        thinking_processed = False
        text_processed = False
        for content_item in entry.message.content:
            if content_item.type == "thinking" and content_item.thinking and thinking_enabled:
                # Include thinking entry once
                if not thinking_processed:
                    entries.append(entry)
                    ordered_items.append(ParsedItem(thinking_entry=entry))
                    thinking_processed = True
            elif content_item.type == "text" and content_item.text and text_enabled:
                # Include text entry once
                if not text_processed:
                    entries.append(entry)
                    ordered_items.append(ParsedItem(thinking_entry=entry))
                    text_processed = True
            elif content_item.type == "tool_use":
                # Extract tool use from message content
                tool_data = {
                    "type": content_item.type,
                    "id": getattr(content_item, "id", ""),
                    "name": getattr(content_item, "name", ""),
                    "input": getattr(content_item, "input", {}),
                }
                tool_use = ToolUseEntry.model_validate(tool_data)
                tool_uses.append(tool_use)
                ordered_items.append(ParsedItem(tool_use=tool_use))

    @staticmethod
    def handle(command: ParseThinkingCommand) -> ParseThinkingResponse:
        """Parse thinking entries and tool uses from JSONL file.

        Args:
            command: Parse thinking command with file path and position.

        Returns:
            Response with parsed entries, tool uses, ordered items, and end position.
        """
        # Import here to avoid circular dependency at runtime
        from src.shared.tool_use_models import ToolUseEntry  # noqa: PLC0415

        if not command.jsonl_path.exists():
            return ParseThinkingResponse(
                entries=[], tool_uses=[], ordered_items=[], end_position=command.from_position
            )

        entries: list[ThinkingEntry] = []
        tool_uses: list[ToolUseEntry] = []
        ordered_items: list[ParsedItem] = []

        with command.jsonl_path.open("r", encoding="utf-8") as f:
            # Seek to start position
            f.seek(command.from_position)

            for line in f:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                try:
                    data = orjson.loads(stripped_line)

                    # Check if this is a standalone tool use entry
                    if data.get("type") == "tool_use":
                        tool_use = ToolUseEntry.model_validate(data)
                        tool_uses.append(tool_use)
                        ordered_items.append(ParsedItem(tool_use=tool_use))
                    else:
                        # Try to parse as thinking entry (assistant message)
                        entry = ThinkingEntry.model_validate(data)
                        if entry.type == "assistant":
                            # Extract tool uses, thinking, and text from message content
                            thinking_enabled = command.config.thinking_enabled if command.config else True
                            text_enabled = command.config.text_enabled if command.config else False
                            ParseThinkingHandler._process_assistant_message(
                                entry,
                                entries,
                                tool_uses,
                                ordered_items,
                                thinking_enabled=thinking_enabled,
                                text_enabled=text_enabled,
                            )
                except (orjson.JSONDecodeError, ValueError):
                    # Skip malformed lines
                    continue

            end_position = f.tell()

        return ParseThinkingResponse(
            entries=entries, tool_uses=tool_uses, ordered_items=ordered_items, end_position=end_position
        )

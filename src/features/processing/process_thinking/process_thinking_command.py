# ABOUTME: Process thinking command definition
# ABOUTME: Defines command to process and accumulate thinking entries

from dataclasses import dataclass

from src.shared.models import Config, ThinkingEntry


@dataclass
class ProcessThinkingCommand:
    """Command to process thinking entries with accumulation logic.

    Attributes:
        entries: Thinking entries to process.
        config: Current application configuration.
        compressed_thinking_map: Map of entry parent_uuid to pre-compressed thinking content.
        compressed_text_map: Map of entry parent_uuid to pre-compressed text content.
    """

    entries: list[ThinkingEntry]
    config: Config
    compressed_thinking_map: dict[str, str] | None = None
    compressed_text_map: dict[str, str] | None = None

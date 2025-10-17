# ABOUTME: Helper for coordinating display of parsed items
# ABOUTME: Manages item display loop and separator logic

from src.features.monitoring.display_item.display_item_command import DisplayItemCommand
from src.features.monitoring.display_item.display_item_handler import DisplayItemHandler
from src.features.monitoring.parse_thinking.parse_thinking_handler import (
    ParseThinkingResponse,
)
from src.shared.models import Config


class DisplayCoordinator:
    """Coordinates display of parsed items with separator logic."""

    def __init__(self) -> None:
        """Initialize display coordinator."""
        self._has_shown_thinking = False

    async def display_items(
        self,
        parse_resp: ParseThinkingResponse,
        config: Config,
        compressed_thinking_map: dict[str, str],
        compressed_text_map: dict[str, str],
    ) -> None:
        """Display all parsed items with appropriate separators.

        Args:
            parse_resp: Parsed thinking response
            config: Current configuration
            compressed_thinking_map: Map of compressed thinking content
            compressed_text_map: Map of compressed text content
        """
        for item in parse_resp.ordered_items:
            has_thinking = item.thinking_entry is not None and item.thinking_entry.get_thinking_content() is not None
            show_separator = self._has_shown_thinking and has_thinking

            # Get compressed content for this entry
            compressed_thinking = None
            compressed_text = None
            if item.thinking_entry:
                compressed_thinking = compressed_thinking_map.get(item.thinking_entry.parent_uuid)
                compressed_text = compressed_text_map.get(item.thinking_entry.parent_uuid)

            await DisplayItemHandler.handle(
                DisplayItemCommand(
                    item=item,
                    config=config,
                    show_separator=show_separator,
                    compressed_thinking=compressed_thinking,
                    compressed_text=compressed_text,
                )
            )
            if has_thinking:
                self._has_shown_thinking = True

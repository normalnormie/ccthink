# ABOUTME: Display item command definition
# ABOUTME: Command for displaying a single parsed item (thinking or tool use)

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.features.monitoring.parse_thinking.parse_thinking_handler import ParsedItem
    from src.shared.models import Config


@dataclass
class DisplayItemCommand:
    """Command to display a parsed item.

    Attributes:
        item: The parsed item to display (thinking entry or tool use).
        config: Application configuration.
        show_separator: Whether to show separator before this item.
    """

    item: ParsedItem
    config: Config
    show_separator: bool

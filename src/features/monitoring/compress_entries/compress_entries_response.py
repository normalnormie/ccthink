# ABOUTME: Response definition for compress entries operation
# ABOUTME: Contains separate compressed maps for thinking and text content

from dataclasses import dataclass


@dataclass
class CompressEntriesResponse:
    """Response from compress entries operation.

    Attributes:
        compressed_thinking_map: Map of parent_uuid to compressed thinking content.
        compressed_text_map: Map of parent_uuid to compressed text content.
    """

    compressed_thinking_map: dict[str, str]
    compressed_text_map: dict[str, str]

# ABOUTME: Parse thinking command definition
# ABOUTME: Defines command to extract thinking entries from JSONL file

from dataclasses import dataclass
from pathlib import Path

from src.shared.models import Config


@dataclass
class ParseThinkingCommand:
    """Command to parse thinking entries from JSONL file.

    Attributes:
        jsonl_path: Path to JSONL file to parse.
        from_position: File position to start reading from (bytes).
        config: Application configuration for content extraction toggles.
    """

    jsonl_path: Path
    from_position: int = 0
    config: Config | None = None

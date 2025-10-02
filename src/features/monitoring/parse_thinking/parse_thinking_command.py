# ABOUTME: Parse thinking command definition
# ABOUTME: Defines command to extract thinking entries from JSONL file

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParseThinkingCommand:
    """Command to parse thinking entries from JSONL file.

    Attributes:
        jsonl_path: Path to JSONL file to parse.
        from_position: File position to start reading from (bytes).
    """

    jsonl_path: Path
    from_position: int = 0

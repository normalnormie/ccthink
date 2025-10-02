# ABOUTME: Find current JSONL command definition
# ABOUTME: Defines command to locate the active JSONL file by timestamp

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FindCurrentJsonlCommand:
    """Command to find the current active JSONL file in a directory.

    Locates the JSONL file with the highest modification timestamp.

    Attributes:
        claude_project_dir: Path to Claude project directory.
    """

    claude_project_dir: Path

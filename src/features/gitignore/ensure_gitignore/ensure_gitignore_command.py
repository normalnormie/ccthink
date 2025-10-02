# ABOUTME: Ensure gitignore command definition
# ABOUTME: Defines command to add entries to .gitignore file

from dataclasses import dataclass
from pathlib import Path


@dataclass
class EnsureGitignoreCommand:
    """Command to ensure entries are in .gitignore.

    Attributes:
        entries: List of patterns to add to .gitignore.
        gitignore_path: Path to .gitignore file.
    """

    entries: list[str]
    gitignore_path: Path

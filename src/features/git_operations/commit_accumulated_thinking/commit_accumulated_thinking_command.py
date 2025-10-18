# ABOUTME: Command for committing accumulated thinking to git
# ABOUTME: Orchestrates gitignore setup, commit, and config updates

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.models import Config


@dataclass
class CommitAccumulatedThinkingCommand:
    """Command to commit accumulated thinking."""

    config: Config
    enable_git: bool

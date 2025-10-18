# ABOUTME: Response for commit accumulated thinking operation
# ABOUTME: Contains config state and operation status

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.models import Config


@dataclass
class CommitAccumulatedThinkingResponse:
    """Response from commit accumulated thinking operation."""

    config: Config
    gitignore_success: bool
    commit_success: bool
    error: str | None = None

# ABOUTME: Response containing Claude project directory path
# ABOUTME: Contains directory path

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class GetClaudeDirectoryResponse:
    """Response with Claude project directory path."""

    directory: Path

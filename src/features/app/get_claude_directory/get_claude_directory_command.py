# ABOUTME: Command for retrieving Claude project directory
# ABOUTME: Contains config with projects directory path

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.models import Config


@dataclass
class GetClaudeDirectoryCommand:
    """Command to get Claude project directory."""

    config: Config

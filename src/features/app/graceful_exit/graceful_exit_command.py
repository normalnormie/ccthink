# ABOUTME: Command for graceful application exit
# ABOUTME: Contains config and git enablement status

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.models import Config


@dataclass
class GracefulExitCommand:
    """Command for graceful application exit."""

    config: Config | None
    enable_git: bool

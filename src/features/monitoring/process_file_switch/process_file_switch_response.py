# ABOUTME: Response for file switch operation
# ABOUTME: Contains config state after file switch

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.models import Config


@dataclass
class ProcessFileSwitchResponse:
    """Response from file switch operation."""

    config: Config

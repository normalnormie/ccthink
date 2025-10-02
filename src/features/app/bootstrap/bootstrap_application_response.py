# ABOUTME: Response from application bootstrap operation
# ABOUTME: Contains initialized configuration and application state

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.models import Config


@dataclass
class BootstrapApplicationResponse:
    """Response containing bootstrapped application state.

    Attributes:
        config: Loaded and configured application config
    """

    config: Config

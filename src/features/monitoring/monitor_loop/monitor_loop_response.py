# ABOUTME: Response from monitor loop iteration
# ABOUTME: Contains current state after monitoring cycle

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import asyncio

    from src.shared.models import Config


@dataclass
class MonitorLoopResponse:
    """Response containing monitor loop execution results.

    Attributes:
        config: Current configuration after monitoring
        timer_task: Current timer task reference (optional)
        should_save_config: Whether config should be persisted
    """

    config: Config
    timer_task: asyncio.Task[None] | None = None
    should_save_config: bool = True

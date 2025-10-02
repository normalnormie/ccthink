# ABOUTME: Command for executing monitor loop iteration
# ABOUTME: Defines input parameters for monitoring cycle

from __future__ import annotations

import asyncio  # noqa: TC003
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.shared.models import Config


@dataclass
class MonitorLoopCommand:
    """Command to execute one monitor loop iteration.

    Attributes:
        config: Current configuration
        enable_git: Whether git operations are enabled
        timer_task: Current timer task reference (optional)
    """

    config: Config
    enable_git: bool
    timer_task: asyncio.Task[None] | None = None

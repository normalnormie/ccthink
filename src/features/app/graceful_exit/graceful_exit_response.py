# ABOUTME: Response for graceful exit operation
# ABOUTME: Contains exit status

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GracefulExitResponse:
    """Response from graceful exit operation."""

    success: bool

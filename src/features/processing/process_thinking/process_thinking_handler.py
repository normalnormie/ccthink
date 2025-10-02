# ABOUTME: Process thinking handler implementation
# ABOUTME: Handles accumulation and timing logic for thinking entries

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.features.processing.process_thinking.process_thinking_command import (
        ProcessThinkingCommand,
    )
    from src.shared.models import Config


@dataclass
class ProcessThinkingResponse:
    """Response from processing thinking entries.

    Attributes:
        should_commit: Whether accumulated thinking should be committed.
        thinking_to_commit: List of thinking content to commit.
        target_uuid: UUID to mark as processed after commit.
        should_start_timer: Whether to start accumulation timer.
        current_config: Current configuration state.
    """

    should_commit: bool
    thinking_to_commit: list[str]
    target_uuid: str
    should_start_timer: bool
    current_config: Config


class ProcessThinkingHandler:
    """Handler for processing thinking entries with accumulation logic."""

    @staticmethod
    def handle(command: ProcessThinkingCommand) -> ProcessThinkingResponse:
        """Process thinking entries and determine commit actions.

        Logic:
        - If not waiting and have entries: start waiting
        - If waiting and have additional entries: commit accumulated + first additional
        - Otherwise: continue waiting

        Args:
            command: Process thinking command.

        Returns:
            Response with commit decision and current state.
        """
        config = command.config

        # Extract thinking content from entries
        thinking_content = [
            entry.get_thinking_content() or ""
            for entry in command.entries
            if entry.get_thinking_content()
        ]

        if not config.waiting_for_thinking:
            # Not waiting - start waiting if we have thinking
            if thinking_content:
                config.waiting_for_thinking = True
                config.accumulated_thinking = thinking_content
                config.waiting_target_uuid = command.entries[-1].parent_uuid

                return ProcessThinkingResponse(
                    should_commit=False,
                    thinking_to_commit=[],
                    target_uuid="",
                    should_start_timer=True,
                    current_config=config,
                )

            # No thinking to process
            return ProcessThinkingResponse(
                should_commit=False,
                thinking_to_commit=[],
                target_uuid="",
                should_start_timer=False,
                current_config=config,
            )

        # Currently waiting - check for additional thinking
        total_thinking = len(config.accumulated_thinking) + len(thinking_content)

        if total_thinking > len(config.accumulated_thinking):
            # Have additional thinking - commit accumulated + first additional
            to_commit = [*config.accumulated_thinking, thinking_content[0]]
            target_uuid = command.entries[0].parent_uuid

            # Reset waiting state
            config.waiting_for_thinking = False
            config.accumulated_thinking = []
            config.waiting_target_uuid = ""

            return ProcessThinkingResponse(
                should_commit=True,
                thinking_to_commit=to_commit,
                target_uuid=target_uuid,
                should_start_timer=False,
                current_config=config,
            )

        # No additional thinking yet
        return ProcessThinkingResponse(
            should_commit=False,
            thinking_to_commit=[],
            target_uuid="",
            should_start_timer=False,
            current_config=config,
        )

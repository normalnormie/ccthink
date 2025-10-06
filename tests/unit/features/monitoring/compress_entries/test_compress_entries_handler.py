# ABOUTME: Tests for compress entries handler
# ABOUTME: Verifies separate compression of thinking and text content

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.features.monitoring.compress_entries.compress_entries_command import (
    CompressEntriesCommand,
)
from src.features.monitoring.compress_entries.compress_entries_handler import (
    CompressEntriesHandler,
)
from src.features.phrase_transformation.transform_thinking.transform_thinking_response import (
    TransformThinkingResponse,
)
from src.shared.models import Config, Message, MessageContent, ThinkingEntry


class TestCompressEntriesHandler:
    """Test compress entries handler with dual compression logic."""

    @pytest.mark.asyncio
    async def test_compress_both_thinking_and_text(self) -> None:
        """Verify both thinking and text are compressed when both enabled."""
        # Create config with both enabled
        config = Config(
            sonnet_enabled=True,
            thinking_enabled=True,
            text_enabled=True,
        )

        # Create entry with both thinking and text content
        entry = ThinkingEntry(
            parentUuid="uuid-1",
            type="assistant",
            message=Message(
                role="assistant",
                content=[
                    MessageContent(type="thinking", thinking="Original thinking content"),
                    MessageContent(type="text", text="Original text content"),
                ],
            ),
            timestamp="2025-10-06T12:00:00Z",
        )

        # Mock the transform handler
        with patch(
            "src.features.monitoring.compress_entries.compress_entries_handler.TransformThinkingHandler.handle"
        ) as mock_transform:
            # Setup mock to return different compressed values
            mock_responses = [
                TransformThinkingResponse(
                    transformed_lines=["Compressed thinking"],
                    colors=[34],
                    success=True,
                    errors=[],
                    original_lines=["Original thinking content"],
                ),
                TransformThinkingResponse(
                    transformed_lines=["Compressed text"],
                    colors=[34],
                    success=True,
                    errors=[],
                    original_lines=["Original text content"],
                ),
            ]
            mock_transform.side_effect = mock_responses

            # Execute handler
            command = CompressEntriesCommand(entries=[entry], config=config)
            response = await CompressEntriesHandler.handle(command)

            # Verify both maps have compressed content
            assert "uuid-1" in response.compressed_thinking_map
            assert response.compressed_thinking_map["uuid-1"] == "Compressed thinking"
            assert "uuid-1" in response.compressed_text_map
            assert response.compressed_text_map["uuid-1"] == "Compressed text"

            # Verify transform was called twice (once for thinking, once for text)
            assert mock_transform.call_count == 2

    @pytest.mark.asyncio
    async def test_compress_only_thinking(self) -> None:
        """Verify only thinking is compressed when text_enabled=False."""
        # Create config with only thinking enabled
        config = Config(
            sonnet_enabled=True,
            thinking_enabled=True,
            text_enabled=False,
        )

        # Create entry with both thinking and text content
        entry = ThinkingEntry(
            parentUuid="uuid-2",
            type="assistant",
            message=Message(
                role="assistant",
                content=[
                    MessageContent(type="thinking", thinking="Original thinking content"),
                    MessageContent(type="text", text="Original text content"),
                ],
            ),
            timestamp="2025-10-06T12:00:00Z",
        )

        # Mock the transform handler
        with patch(
            "src.features.monitoring.compress_entries.compress_entries_handler.TransformThinkingHandler.handle"
        ) as mock_transform:
            mock_transform.return_value = TransformThinkingResponse(
                transformed_lines=["Compressed thinking"],
                colors=[34],
                success=True,
                errors=[],
                original_lines=["Original thinking content"],
            )

            # Execute handler
            command = CompressEntriesCommand(entries=[entry], config=config)
            response = await CompressEntriesHandler.handle(command)

            # Verify only thinking map has content
            assert "uuid-2" in response.compressed_thinking_map
            assert response.compressed_thinking_map["uuid-2"] == "Compressed thinking"
            assert "uuid-2" not in response.compressed_text_map

            # Verify transform was called only once
            assert mock_transform.call_count == 1

    @pytest.mark.asyncio
    async def test_compress_only_text(self) -> None:
        """Verify only text is compressed when thinking_enabled=False."""
        # Create config with only text enabled
        config = Config(
            sonnet_enabled=True,
            thinking_enabled=False,
            text_enabled=True,
        )

        # Create entry with both thinking and text content
        entry = ThinkingEntry(
            parentUuid="uuid-3",
            type="assistant",
            message=Message(
                role="assistant",
                content=[
                    MessageContent(type="thinking", thinking="Original thinking content"),
                    MessageContent(type="text", text="Original text content"),
                ],
            ),
            timestamp="2025-10-06T12:00:00Z",
        )

        # Mock the transform handler
        with patch(
            "src.features.monitoring.compress_entries.compress_entries_handler.TransformThinkingHandler.handle"
        ) as mock_transform:
            mock_transform.return_value = TransformThinkingResponse(
                transformed_lines=["Compressed text"],
                colors=[34],
                success=True,
                errors=[],
                original_lines=["Original text content"],
            )

            # Execute handler
            command = CompressEntriesCommand(entries=[entry], config=config)
            response = await CompressEntriesHandler.handle(command)

            # Verify only text map has content
            assert "uuid-3" not in response.compressed_thinking_map
            assert "uuid-3" in response.compressed_text_map
            assert response.compressed_text_map["uuid-3"] == "Compressed text"

            # Verify transform was called only once
            assert mock_transform.call_count == 1

    @pytest.mark.asyncio
    async def test_handle_entries_with_no_content(self) -> None:
        """Verify entries with no content are handled gracefully."""
        config = Config(
            sonnet_enabled=True,
            thinking_enabled=True,
            text_enabled=True,
        )

        # Create entry with no thinking or text content
        entry = ThinkingEntry(
            parentUuid="uuid-4",
            type="assistant",
            message=Message(
                role="assistant",
                content=[],
            ),
            timestamp="2025-10-06T12:00:00Z",
        )

        # Execute handler
        command = CompressEntriesCommand(entries=[entry], config=config)
        response = await CompressEntriesHandler.handle(command)

        # Verify maps are empty
        assert "uuid-4" not in response.compressed_thinking_map
        assert "uuid-4" not in response.compressed_text_map

    @pytest.mark.asyncio
    async def test_handle_multiple_entries(self) -> None:
        """Verify multiple entries are processed correctly."""
        config = Config(
            sonnet_enabled=True,
            thinking_enabled=True,
            text_enabled=True,
        )

        # Create multiple entries
        entries = [
            ThinkingEntry(
                parentUuid=f"uuid-{i}",
                type="assistant",
                message=Message(
                    role="assistant",
                    content=[
                        MessageContent(type="thinking", thinking=f"Thinking {i}"),
                        MessageContent(type="text", text=f"Text {i}"),
                    ],
                ),
                timestamp="2025-10-06T12:00:00Z",
            )
            for i in range(3)
        ]

        # Mock the transform handler
        with patch(
            "src.features.monitoring.compress_entries.compress_entries_handler.TransformThinkingHandler.handle"
        ) as mock_transform:
            # Setup mock to return compressed values
            async def mock_handle(cmd: Any, config: Any) -> TransformThinkingResponse:
                content = cmd.thinking_lines[0]
                return TransformThinkingResponse(
                    transformed_lines=[f"Compressed {content}"],
                    colors=[34],
                    success=True,
                    errors=[],
                    original_lines=[content],
                )

            mock_transform.side_effect = mock_handle

            # Execute handler
            command = CompressEntriesCommand(entries=entries, config=config)
            response = await CompressEntriesHandler.handle(command)

            # Verify all entries are compressed
            for i in range(3):
                uuid = f"uuid-{i}"
                assert uuid in response.compressed_thinking_map
                assert f"Thinking {i}" in response.compressed_thinking_map[uuid]
                assert uuid in response.compressed_text_map
                assert f"Text {i}" in response.compressed_text_map[uuid]

            # Verify transform was called for each entry (3 entries x 2 content types = 6 calls)
            assert mock_transform.call_count == 6

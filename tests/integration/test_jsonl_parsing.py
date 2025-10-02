# ABOUTME: Integration tests for JSONL file parsing
# ABOUTME: Tests thinking entry extraction from JSONL files

from __future__ import annotations

from pathlib import Path

import pytest

from src.features.monitoring.parse_thinking.parse_thinking_command import ParseThinkingCommand
from src.features.monitoring.parse_thinking.parse_thinking_handler import ParseThinkingHandler


@pytest.fixture
def fixtures_dir() -> Path:
    """Get fixtures directory path.

    Returns:
        Path to fixtures directory.
    """
    return Path(__file__).parent / "fixtures"


class TestJSONLFileParsing:
    """Test JSONL file parsing and thinking entry extraction."""

    def test_parse_simple_thinking_entries(self, fixtures_dir: Path) -> None:
        """Parse thinking entries from sample JSONL file."""
        jsonl_path = fixtures_dir / "sample_thinking.jsonl"
        assert jsonl_path.exists(), f"Fixture file not found: {jsonl_path}"

        command = ParseThinkingCommand(jsonl_path=jsonl_path, from_position=0)
        response = ParseThinkingHandler.handle(command)

        # Should parse 4 thinking entries (excluding the text-only entry)
        assert len(response.entries) == 4
        assert response.entries[0].parent_uuid == "uuid-001"
        assert response.entries[1].parent_uuid == "uuid-002"
        assert response.entries[2].parent_uuid == "uuid-003"
        assert response.entries[3].parent_uuid == "uuid-005"

        # Verify thinking content extraction
        thinking_1 = response.entries[0].get_thinking_content()
        assert thinking_1 == "This is a simple thinking entry for testing."

        thinking_2 = response.entries[1].get_thinking_content()
        assert "special characters" in thinking_2

        thinking_3 = response.entries[2].get_thinking_content()
        assert "你好世界" in thinking_3
        assert "🌍" in thinking_3

    def test_parse_multiple_thinking_same_parent(self, fixtures_dir: Path) -> None:
        """Parse multiple thinking entries for same parent UUID."""
        jsonl_path = fixtures_dir / "multi_thinking.jsonl"

        command = ParseThinkingCommand(jsonl_path=jsonl_path, from_position=0)
        response = ParseThinkingHandler.handle(command)

        assert len(response.entries) == 3
        # All should have same parent UUID
        assert all(entry.parent_uuid == "uuid-100" for entry in response.entries)

    def test_parse_no_thinking_entries(self, fixtures_dir: Path) -> None:
        """Parse JSONL file with no thinking entries."""
        jsonl_path = fixtures_dir / "empty_thinking.jsonl"

        command = ParseThinkingCommand(jsonl_path=jsonl_path, from_position=0)
        response = ParseThinkingHandler.handle(command)

        assert len(response.entries) == 0

    def test_parse_from_position(self, fixtures_dir: Path) -> None:
        """Parse JSONL starting from specific file position."""
        jsonl_path = fixtures_dir / "sample_thinking.jsonl"

        # First, get the full file size of first line
        with jsonl_path.open("r") as f:
            first_line = f.readline()
            first_line_end = len(first_line.encode("utf-8"))

        # Parse from after first line
        command = ParseThinkingCommand(jsonl_path=jsonl_path, from_position=first_line_end)
        response = ParseThinkingHandler.handle(command)

        # Should skip first entry
        assert len(response.entries) == 3
        assert response.entries[0].parent_uuid == "uuid-002"

    def test_parse_special_characters_unicode(self, fixtures_dir: Path) -> None:
        """Parse thinking entries with special characters and unicode."""
        jsonl_path = fixtures_dir / "sample_thinking.jsonl"

        command = ParseThinkingCommand(jsonl_path=jsonl_path, from_position=0)
        response = ParseThinkingHandler.handle(command)

        # Find unicode entry
        unicode_entry = next(e for e in response.entries if e.parent_uuid == "uuid-003")
        content = unicode_entry.get_thinking_content()

        assert content is not None
        assert "你好世界" in content
        assert "🌍" in content
        assert "émojis" in content
        assert "açcents" in content

    def test_parse_long_thinking_entry(self, fixtures_dir: Path) -> None:
        """Parse long thinking entry with multiple sentences."""
        jsonl_path = fixtures_dir / "sample_thinking.jsonl"

        command = ParseThinkingCommand(jsonl_path=jsonl_path, from_position=0)
        response = ParseThinkingHandler.handle(command)

        # Find long entry
        long_entry = next(e for e in response.entries if e.parent_uuid == "uuid-005")
        content = long_entry.get_thinking_content()

        assert content is not None
        assert len(content) > 100
        assert "multiple sentences" in content
        assert "compression service" in content

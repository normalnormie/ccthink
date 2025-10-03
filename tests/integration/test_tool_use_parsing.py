# ABOUTME: Integration tests for tool use parsing from JSONL files
# ABOUTME: Validates extraction and formatting of tool_use entries alongside thinking

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


class TestToolUseParsing:
    """Tool use parsing and chronological ordering verification."""

    def test_parse_tool_uses_with_thinking(self, fixtures_dir: Path) -> None:
        """Parse JSONL file containing both thinking entries and tool uses."""
        jsonl_path = fixtures_dir / "thinking_with_tool_uses.jsonl"
        assert jsonl_path.exists(), f"Fixture file not found: {jsonl_path}"

        command = ParseThinkingCommand(jsonl_path=jsonl_path, from_position=0)
        response = ParseThinkingHandler.handle(command)

        # Verify thinking entries parsed
        assert len(response.entries) == 2
        assert response.entries[0].parent_uuid == "uuid-001"
        assert response.entries[1].parent_uuid == "uuid-002"

        # Verify tool uses parsed
        assert len(response.tool_uses) == 4
        assert response.tool_uses[0].name == "Bash"
        assert response.tool_uses[1].name == "Write"
        assert response.tool_uses[2].name == "Read"
        assert response.tool_uses[3].name == "Task"

    def test_chronological_ordering(self, fixtures_dir: Path) -> None:
        """Verify that ordered_items maintains chronological order from JSONL file."""
        jsonl_path = fixtures_dir / "thinking_with_tool_uses.jsonl"

        command = ParseThinkingCommand(jsonl_path=jsonl_path, from_position=0)
        response = ParseThinkingHandler.handle(command)

        # Should have 6 total items (2 thinking + 4 tool uses)
        assert len(response.ordered_items) == 6

        # Verify chronological order matches JSONL line order
        assert response.ordered_items[0].thinking_entry is not None
        assert response.ordered_items[0].thinking_entry.parent_uuid == "uuid-001"

        assert response.ordered_items[1].tool_use is not None
        assert response.ordered_items[1].tool_use.name == "Bash"

        assert response.ordered_items[2].tool_use is not None
        assert response.ordered_items[2].tool_use.name == "Write"

        assert response.ordered_items[3].thinking_entry is not None
        assert response.ordered_items[3].thinking_entry.parent_uuid == "uuid-002"

        assert response.ordered_items[4].tool_use is not None
        assert response.ordered_items[4].tool_use.name == "Read"

        assert response.ordered_items[5].tool_use is not None
        assert response.ordered_items[5].tool_use.name == "Task"

    def test_tool_use_display_formatting(self, fixtures_dir: Path) -> None:
        """Verify tool use display formatting shows full content without truncation."""
        jsonl_path = fixtures_dir / "thinking_with_tool_uses.jsonl"

        command = ParseThinkingCommand(jsonl_path=jsonl_path, from_position=0)
        response = ParseThinkingHandler.handle(command)

        # Bash tool - full command shown
        bash_tool = response.tool_uses[0]
        assert bash_tool.format_tool_display() == "Bash(mkdir -p /home/user/project/src)"

        # Write tool - full path shown
        write_tool = response.tool_uses[1]
        assert write_tool.format_tool_display() == "Write(/home/user/project/src/main.py)"

        # Read tool - full path shown
        read_tool = response.tool_uses[2]
        assert read_tool.format_tool_display() == "Read(/home/user/project/src/main.py)"

        # Task tool - full description shown
        task_tool = response.tool_uses[3]
        assert task_tool.format_tool_display() == "Task(Validate code quality)"

    def test_only_tool_uses_no_thinking(self, fixtures_dir: Path) -> None:
        """Parse JSONL file containing only tool uses without thinking entries."""
        # Create fixture on the fly for this scenario
        jsonl_path = fixtures_dir / "only_tool_uses.jsonl"
        jsonl_path.write_text(
            '{"type":"tool_use","id":"toolu_01","name":"Bash","input":{"command":"ls"}}\n'
            '{"type":"tool_use","id":"toolu_02","name":"Read","input":{"file_path":"/tmp/file.txt"}}\n'
        )

        command = ParseThinkingCommand(jsonl_path=jsonl_path, from_position=0)
        response = ParseThinkingHandler.handle(command)

        assert len(response.entries) == 0
        assert len(response.tool_uses) == 2
        assert len(response.ordered_items) == 2

        # Cleanup
        jsonl_path.unlink()

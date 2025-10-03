# ABOUTME: Tool use entry models for parsing and displaying tool calls
# ABOUTME: Defines ToolUseEntry for extracting tool usage from JSONL files

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolUseEntry(BaseModel):
    """Tool use entry parsed from JSONL file."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
    )

    type: str = Field(..., description="Entry type (should be 'tool_use')")
    id: str = Field(..., description="Tool use ID")
    name: str = Field(..., description="Tool name (e.g., 'Bash', 'Write', 'Read')")
    input: dict[str, Any] = Field(..., description="Tool input parameters")

    def format_tool_display(self) -> str:  # noqa: PLR0911
        """Format tool use for display.

        Returns:
            Formatted string like 'Bash(mkdir ...)' or 'Write(file.py)'.
        """
        # Extract relevant parameter for each tool type
        if self.name == "Bash":
            command = self.input.get("command", "")
            return f"{self.name}({command})"

        if self.name in {"Write", "Read", "Edit", "MultiEdit"}:
            file_path = self.input.get("file_path", "")
            return f"{self.name}({file_path})"

        if self.name == "Glob":
            glob_pattern = self.input.get("pattern", "")  # noqm
            return f"{self.name}({glob_pattern})"

        if self.name == "Grep":
            grep_pattern = self.input.get("pattern", "")  # noqm
            return f"{self.name}({grep_pattern})"

        if self.name in {"WebFetch", "WebSearch"}:
            url_or_query = self.input.get("url") or self.input.get("query", "")
            return f"{self.name}({url_or_query})"

        if self.name == "Task":
            description = self.input.get("description", "")
            return f"{self.name}({description})"

        # Default: show tool name with ellipsis
        return f"{self.name}(...)"

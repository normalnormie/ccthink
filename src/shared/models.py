# ABOUTME: Shared Pydantic models for ccthink application
# ABOUTME: Defines configuration, message, and thinking entry data structures

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import orjson
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from pathlib import Path


def _default_disallowed_tools() -> list[str]:
    """Get default list of disallowed tools for compression.

    Returns:
        List of all available Claude Agent SDK tools to disable.
    """
    return [
        "Bash",
        "Read",
        "Write",
        "Edit",
        "MultiEdit",
        "Glob",
        "Grep",
        "WebFetch",
        "WebSearch",
        "Task",
        "LS",
        "ExitPlanMode",
        "NotebookRead",
        "NotebookEdit",
        "TodoWrite",
        "KillBash",
        "BashOutput",
        "SlashCommand",
    ]


class MessageContent(BaseModel):
    """Content structure within a message."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",
    )

    type: str = Field(..., description="Content type (e.g., 'thinking', 'text', 'tool_use')")
    thinking: str | None = Field(None, description="Thinking content if type is 'thinking'")
    text: str | None = Field(None, description="Text content if type is 'text'")


class Message(BaseModel):
    """Message structure from JSONL entries."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    role: str = Field(..., description="Message role (e.g., 'assistant', 'user')")
    content: list[MessageContent] | str = Field(..., description="Message content")


class ThinkingEntry(BaseModel):
    """Thinking entry parsed from JSONL file."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    parent_uuid: str = Field(..., description="Parent UUID of the thinking entry", alias="parentUuid")
    type: str = Field(..., description="Entry type (should be 'assistant')")
    message: Message = Field(..., description="Message containing thinking content")
    timestamp: str = Field(..., description="Timestamp of the entry")

    def get_thinking_content(self) -> str | None:
        """Extract thinking content from message.

        Returns:
            Thinking text if found, None otherwise.
        """
        if isinstance(self.message.content, list):
            for content_item in self.message.content:
                if isinstance(content_item, MessageContent) and content_item.type == "thinking":
                    return content_item.thinking
        return None

    def get_text_content(self) -> str | None:
        """Extract text content from message.

        Returns:
            Text content if found, None otherwise.
        """
        if isinstance(self.message.content, list):
            for content_item in self.message.content:
                if isinstance(content_item, MessageContent) and content_item.type == "text":
                    return content_item.text
        return None


class ClaudeAgentConfig(BaseModel):
    """Claude Agent SDK configuration options.

    Maps to ClaudeAgentOptions parameters in claude-agent-sdk.
    Only includes SDK-supported options.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        populate_by_name=True,
    )

    # Core options
    allowed_tools: list[str] = Field(
        default_factory=list, description="List of tool names that can be used", alias="allowedTools"
    )
    disallowed_tools: list[str] = Field(
        default_factory=_default_disallowed_tools,
        description="List of tools that cannot be used (all tools disabled for compression)",
        alias="disallowedTools",
    )
    system_prompt: str | None = Field(
        default="Ignore any project context and respond based solely on this query. Output only the compressed phrase.",
        description="Custom system prompt",
        alias="systemPrompt",
    )
    model: str | None = Field(default="sonnet", description="Specific Claude model to use")
    max_turns: int | None = Field(default=1, description="Maximum number of conversation turns", alias="maxTurns")

    # Permission options
    permission_mode: str | None = Field(
        default=None,
        description="Tool execution permission mode: default, acceptEdits, plan, bypassPermissions",
        alias="permissionMode",
    )

    # Session options
    continue_conversation: bool = Field(
        default=False, description="Continue the current conversation", alias="continueConversation"
    )
    resume: str | None = Field(default=None, description="Session ID to resume")

    # MCP server configuration
    mcp_servers: dict[str, Any] = Field(
        default_factory=dict, description="MCP server configurations", alias="mcpServers"
    )

    # Filesystem settings
    setting_sources: list[str] | None = Field(
        default=None,
        description="Which filesystem settings to load: user, project, local",
        alias="settingSources",
    )

    # Working directory
    cwd: str | None = Field(default=None, description="Current working directory")

    # Hooks configuration
    hooks: dict[str, Any] = Field(default_factory=dict, description="Event hooks configuration")

    # Subagents
    agents: dict[str, Any] = Field(default_factory=dict, description="Programmatically defined subagents")

    def to_agent_options_params(self) -> dict[str, Any]:
        """Convert config to ClaudeAgentOptions parameters.

        Returns:
            Dictionary of parameters for ClaudeAgentOptions initialization.
        """
        params: dict[str, Any] = {}

        # Map all non-None/non-empty fields
        if self.allowed_tools:
            params["allowed_tools"] = self.allowed_tools
        if self.disallowed_tools:
            params["disallowed_tools"] = self.disallowed_tools
        if self.system_prompt:
            params["system_prompt"] = self.system_prompt
        if self.model:
            params["model"] = self.model
        # Include max_turns if set (defaults to 1)
        if self.max_turns is not None:
            params["max_turns"] = self.max_turns
        if self.permission_mode:
            params["permission_mode"] = self.permission_mode
        if self.continue_conversation:
            params["continue_conversation"] = self.continue_conversation
        if self.resume:
            params["resume"] = self.resume
        if self.mcp_servers:
            params["mcp_servers"] = self.mcp_servers
        if self.setting_sources:
            params["setting_sources"] = self.setting_sources
        if self.cwd:
            params["cwd"] = self.cwd
        if self.hooks:
            params["hooks"] = self.hooks
        if self.agents:
            params["agents"] = self.agents

        return params


class Config(BaseModel):
    """Application configuration state."""

    model_config = ConfigDict(
        validate_assignment=True,
    )

    last_processed_uuid: str = Field(default="", description="UUID of last processed thinking entry")
    simulate: bool = Field(default=False, description="Simulate git operations without executing")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    waiting_for_thinking: bool = Field(default=False, description="Currently waiting for additional thinking")
    accumulated_thinking: list[str] = Field(default_factory=list, description="Accumulated thinking entries")
    waiting_target_uuid: str = Field(default="", description="Target UUID when waiting")
    last_file_position: int = Field(default=0, description="Last read position in JSONL file")
    monitored_file: str = Field(default="", description="Currently monitored JSONL file path")
    main_branch: str = Field(default="master", description="Main git branch name")
    quit_on_conflict: bool = Field(default=False, description="Quit if merge conflict occurs")
    projects_dir: str = Field(default="~/.claude/projects/", description="Claude projects directory")
    commit_enabled: bool = Field(default=False, description="Enable git commit operations")
    sonnet_enabled: bool = Field(default=False, description="Enable Sonnet phrase transformation")
    sonnet_streaming: bool = Field(default=True, description="Enable streaming output for compression")
    sonnet_colors: bool = Field(default=True, description="Enable colored output for compressed phrases")
    tool_uses: bool = Field(default=True, description="Display tool use calls during monitoring")
    thinking_enabled: bool = Field(default=True, description="Enable thinking content extraction and display")
    chat_text_enabled: bool = Field(default=False, description="Enable chat text content extraction and display")
    thinking_color: str = Field(default="#A5D8FF", description="Color for thinking content (CSS name or hex)")
    chat_text_color: str = Field(default="#FFFACD", description="Color for chat text content (CSS name or hex)")
    separator: str = Field(default="\n\n---\n\n", description="Separator between content entries in display")
    line_max_length: int = Field(default=55, description="Maximum line length for content output formatting")
    poll_interval_seconds: float = Field(default=1.0, description="Polling interval for JSONL file changes in seconds")
    compression_prompt: str = Field(
        default=(
            "Compress this phrase keeping details, tense, and voice, choosing an ANSI 256 color "
            'reflecting its sentiment, output as json {{"color":"","text":""}}: {phrase}'
        ),
        description="Template for phrase compression prompt. Must include {phrase} variable.",
    )
    claude_agent: ClaudeAgentConfig = Field(
        default_factory=ClaudeAgentConfig, description="Claude Code agent configuration"
    )

    @classmethod
    def load_from_file(cls, config_path: Path) -> Config:
        """Load configuration from JSON file.

        Handles backwards compatibility for text_enabled -> chat_text_enabled migration.

        Args:
            config_path: Path to configuration file.

        Returns:
            Loaded configuration instance.
        """
        if not config_path.exists():
            return cls()

        with config_path.open("rb") as f:
            data = orjson.loads(f.read())

            # Backwards compatibility: migrate text_enabled to chat_text_enabled
            if "text_enabled" in data and "chat_text_enabled" not in data:
                data["chat_text_enabled"] = data.pop("text_enabled")

            return cls.model_validate(data)

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to JSON file.

        Args:
            config_path: Path to configuration file.
        """
        with config_path.open("wb") as f:
            f.write(orjson.dumps(self.model_dump(by_alias=True), option=orjson.OPT_INDENT_2))

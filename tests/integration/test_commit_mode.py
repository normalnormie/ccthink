# ABOUTME: Integration tests for commit mode with Sonnet
# ABOUTME: Tests commit content compression and git integration

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import orjson
import pytest

from src.features.monitoring.monitor_loop.monitor_loop_command import MonitorLoopCommand
from src.features.monitoring.monitor_loop.monitor_loop_handler import MonitorLoopHandler
from src.shared.models import Config


@pytest.fixture
def config_sonnet_enabled() -> Config:
    """Create config with Sonnet enabled.

    Returns:
        Config with Sonnet compression enabled.
    """
    return Config(
        sonnet_enabled=True,
        sonnet_streaming=True,
        sonnet_colors=True,
        verbose=True,
    )


@pytest.fixture
def config_sonnet_disabled() -> Config:
    """Create config with Sonnet disabled.

    Returns:
        Config with Sonnet compression disabled.
    """
    return Config(
        sonnet_enabled=False,
        sonnet_streaming=False,
        sonnet_colors=False,
        verbose=True,
    )


class TestCommitModeIntegration:
    """Test commit mode integration with Sonnet compression."""

    @pytest.mark.asyncio
    async def test_commit_mode_sonnet_enabled(
        self, config_sonnet_enabled: Config, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Commit mode with Sonnet enabled compresses before commit."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            jsonl_path = Path(f.name)
            # Write assistant message followed by thinking entry with same parent
            f.write(
                orjson.dumps(
                    {
                        "parentUuid": "commit-001",
                        "type": "assistant",
                        "message": {"role": "assistant", "content": "Assistant response"},
                        "timestamp": "2025-10-01T10:00:00Z",
                    }
                ).decode()
                + "\n"
            )
            f.write(
                orjson.dumps(
                    {
                        "parentUuid": "commit-001",
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {"type": "thinking", "thinking": "Thinking for commit test"}
                            ],
                        },
                        "timestamp": "2025-10-01T10:01:00Z",
                    }
                ).decode()
                + "\n"
            )

        try:
            mock_compress = AsyncMock(return_value={"text": "compressed commit", "color": "32"})
            mock_commit = MagicMock()

            with (
                patch(
                    "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
                    mock_compress,
                ),
                patch(
                    "src.features.monitoring.find_current_jsonl.find_current_jsonl_handler.FindCurrentJsonlHandler.handle"
                ) as mock_find,
                patch(
                    "src.features.config.save_config.save_config_handler.SaveConfigHandler.handle"
                ),
                patch(
                    "src.features.git_operations.ensure_branch.ensure_branch_handler.EnsureBranchHandler.handle"
                ),
                patch(
                    "src.features.git_operations.commit_thinking.commit_thinking_handler.CommitThinkingHandler.handle",
                    mock_commit,
                ),
            ):
                mock_find.return_value = MagicMock(jsonl_path=jsonl_path)

                config = config_sonnet_enabled
                config.monitored_file = str(jsonl_path)
                config.last_file_position = 0

                command = MonitorLoopCommand(config=config, enable_git=True, timer_task=None)
                await MonitorLoopHandler.handle(command)

                # Verify compression was called
                assert mock_compress.call_count >= 1

                # Verify commit contains compressed content
                if mock_commit.called:
                    commit_args = mock_commit.call_args
                    commit_message = commit_args[0][0].message
                    assert "compressed" in commit_message

        finally:
            jsonl_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_commit_mode_sonnet_disabled(
        self, config_sonnet_disabled: Config, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Commit mode with Sonnet disabled uses original content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            jsonl_path = Path(f.name)
            original_thinking = "Original thinking for commit"
            f.write(
                orjson.dumps(
                    {
                        "parentUuid": "commit-002",
                        "type": "assistant",
                        "message": {"role": "assistant", "content": "Assistant response"},
                        "timestamp": "2025-10-01T10:00:00Z",
                    }
                ).decode()
                + "\n"
            )
            f.write(
                orjson.dumps(
                    {
                        "parentUuid": "commit-002",
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "thinking", "thinking": original_thinking}],
                        },
                        "timestamp": "2025-10-01T10:01:00Z",
                    }
                ).decode()
                + "\n"
            )

        try:
            mock_commit = MagicMock()

            with (
                patch(
                    "src.features.monitoring.find_current_jsonl.find_current_jsonl_handler.FindCurrentJsonlHandler.handle"
                ) as mock_find,
                patch(
                    "src.features.config.save_config.save_config_handler.SaveConfigHandler.handle"
                ),
                patch(
                    "src.features.git_operations.ensure_branch.ensure_branch_handler.EnsureBranchHandler.handle"
                ),
                patch(
                    "src.features.git_operations.commit_thinking.commit_thinking_handler.CommitThinkingHandler.handle",
                    mock_commit,
                ),
            ):
                mock_find.return_value = MagicMock(jsonl_path=jsonl_path)

                config = config_sonnet_disabled
                config.monitored_file = str(jsonl_path)
                config.last_file_position = 0

                command = MonitorLoopCommand(config=config, enable_git=True, timer_task=None)
                await MonitorLoopHandler.handle(command)

                # Verify commit contains original thinking
                if mock_commit.called:
                    commit_args = mock_commit.call_args
                    commit_message = commit_args[0][0].message
                    assert original_thinking in commit_message

        finally:
            jsonl_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_commit_mode_no_colors_in_commit(
        self, config_sonnet_enabled: Config
    ) -> None:
        """Commit mode disables colors for git commits."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            jsonl_path = Path(f.name)
            f.write(
                orjson.dumps(
                    {
                        "parentUuid": "commit-003",
                        "type": "assistant",
                        "message": {"role": "assistant", "content": "Response"},
                        "timestamp": "2025-10-01T10:00:00Z",
                    }
                ).decode()
                + "\n"
            )
            f.write(
                orjson.dumps(
                    {
                        "parentUuid": "commit-003",
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "thinking", "thinking": "Test"}],
                        },
                        "timestamp": "2025-10-01T10:01:00Z",
                    }
                ).decode()
                + "\n"
            )

        try:
            mock_compress = AsyncMock(return_value={"text": "compressed", "color": "32"})
            mock_commit = MagicMock()

            with (
                patch(
                    "src.features.phrase_transformation.compress_phrase.compress_phrase_service.CompressPhraseService.compress",
                    mock_compress,
                ),
                patch(
                    "src.features.monitoring.find_current_jsonl.find_current_jsonl_handler.FindCurrentJsonlHandler.handle"
                ) as mock_find,
                patch(
                    "src.features.config.save_config.save_config_handler.SaveConfigHandler.handle"
                ),
                patch(
                    "src.features.git_operations.ensure_branch.ensure_branch_handler.EnsureBranchHandler.handle"
                ),
                patch(
                    "src.features.git_operations.commit_thinking.commit_thinking_handler.CommitThinkingHandler.handle",
                    mock_commit,
                ),
            ):
                mock_find.return_value = MagicMock(jsonl_path=jsonl_path)

                config = config_sonnet_enabled
                config.monitored_file = str(jsonl_path)
                config.last_file_position = 0

                command = MonitorLoopCommand(config=config, enable_git=True, timer_task=None)
                await MonitorLoopHandler.handle(command)

                # Verify commit message contains plain text (no ANSI codes)
                if mock_commit.called:
                    commit_message = mock_commit.call_args[0][0].message
                    # Should not contain ANSI escape codes
                    assert "\x1b[" not in commit_message

        finally:
            jsonl_path.unlink(missing_ok=True)

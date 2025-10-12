# ABOUTME: Integration tests for display mode with Sonnet
# ABOUTME: Tests streaming display and logging integration

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
    """Create config with Sonnet enabled and streaming.

    Returns:
        Config with Sonnet compression enabled.
    """
    return Config(
        sonnet_enabled=True,
        sonnet_streaming=True,
        colors=True,
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
        colors=False,
        verbose=True,
    )


class TestDisplayModeIntegration:
    """Test display mode integration with Sonnet compression."""

    @pytest.mark.asyncio
    async def test_display_mode_sonnet_enabled_streaming(
        self, config_sonnet_enabled: Config, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Display mode with Sonnet enabled and streaming."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            jsonl_path = Path(f.name)
            f.write(
                orjson.dumps(
                    {
                        "parentUuid": "test-001",
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "thinking", "thinking": "Display mode test"}],
                        },
                        "timestamp": "2025-10-01T10:00:00Z",
                    }
                ).decode()
                + "\n"
            )

        try:
            mock_compress = AsyncMock(return_value={"text": "compressed display", "color": "32"})

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
                caplog.at_level("INFO"),
            ):
                mock_find.return_value = MagicMock(jsonl_path=jsonl_path)

                config = config_sonnet_enabled
                config.monitored_file = str(jsonl_path)
                config.last_file_position = 0

                command = MonitorLoopCommand(config=config, enable_git=False, timer_task=None)
                await MonitorLoopHandler.handle(command)

                # Verify compression was called
                mock_compress.assert_called_once()

                # Verify logs contain compressed output (without "Thinking: " prefix)
                log_messages = [rec.message for rec in caplog.records if rec.levelname == "INFO"]
                assert any("compressed" in msg for msg in log_messages)

        finally:
            jsonl_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_display_mode_sonnet_disabled(
        self, config_sonnet_disabled: Config, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Display mode with Sonnet disabled logs original content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            jsonl_path = Path(f.name)
            original_content = "Original thinking without compression"
            f.write(
                orjson.dumps(
                    {
                        "parentUuid": "test-002",
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "thinking", "thinking": original_content}],
                        },
                        "timestamp": "2025-10-01T10:00:00Z",
                    }
                ).decode()
                + "\n"
            )

        try:
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
                caplog.at_level("INFO"),
            ):
                mock_find.return_value = MagicMock(jsonl_path=jsonl_path)

                config = config_sonnet_disabled
                config.monitored_file = str(jsonl_path)
                config.last_file_position = 0

                command = MonitorLoopCommand(config=config, enable_git=False, timer_task=None)
                await MonitorLoopHandler.handle(command)

                # Verify original content is logged (without "Thinking: " prefix)
                log_messages = [rec.message for rec in caplog.records if rec.levelname == "INFO"]
                assert any(original_content in msg for msg in log_messages)

        finally:
            jsonl_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_display_mode_compression_errors_logged(
        self, config_sonnet_enabled: Config, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Display mode logs compression errors as warnings."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            jsonl_path = Path(f.name)
            f.write(
                orjson.dumps(
                    {
                        "parentUuid": "test-003",
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "thinking", "thinking": "Error test"}],
                        },
                        "timestamp": "2025-10-01T10:00:00Z",
                    }
                ).decode()
                + "\n"
            )

        try:
            mock_compress = AsyncMock(return_value={"error": "Service timeout"})

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
                caplog.at_level("WARNING"),
            ):
                mock_find.return_value = MagicMock(jsonl_path=jsonl_path)

                config = config_sonnet_enabled
                config.monitored_file = str(jsonl_path)
                config.last_file_position = 0

                command = MonitorLoopCommand(config=config, enable_git=False, timer_task=None)
                await MonitorLoopHandler.handle(command)

                # Verify error logged as warning
                warning_messages = [
                    rec.message for rec in caplog.records if rec.levelname == "WARNING"
                ]
                assert any("Service timeout" in msg for msg in warning_messages)

        finally:
            jsonl_path.unlink(missing_ok=True)

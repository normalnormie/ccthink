# ABOUTME: Integration tests for configuration persistence
# ABOUTME: Tests config save, load, and CLI arg integration

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson

if TYPE_CHECKING:
    from pathlib import Path

from src.shared.models import Config


class TestConfigurationPersistence:
    """Test configuration persistence across operations."""

    def test_config_save_and_load(self, tmp_path: Path) -> None:
        """Config saves to file and loads correctly."""
        config_path = tmp_path / "test_config.json"

        # Create config with Sonnet settings
        config = Config(
            sonnet_enabled=True,
            sonnet_streaming=False,
            sonnet_colors=True,
            verbose=True,
        )

        # Save to file
        config.save_to_file(config_path)

        # Load from file
        loaded_config = Config.load_from_file(config_path)

        # Verify all settings persisted
        assert loaded_config.sonnet_enabled is True
        assert loaded_config.sonnet_streaming is False
        assert loaded_config.sonnet_colors is True
        assert loaded_config.verbose is True

    def test_config_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Loading nonexistent config returns default."""
        config_path = tmp_path / "nonexistent.json"

        loaded_config = Config.load_from_file(config_path)

        # Should have default values
        assert loaded_config.sonnet_enabled is False
        assert loaded_config.sonnet_streaming is True
        assert loaded_config.sonnet_colors is True

    def test_config_all_sonnet_flags(self, tmp_path: Path) -> None:
        """All Sonnet-related flags persist correctly."""
        config_path = tmp_path / "sonnet_config.json"

        config = Config(
            sonnet_enabled=True,
            sonnet_streaming=True,
            sonnet_colors=True,
        )

        config.save_to_file(config_path)
        loaded = Config.load_from_file(config_path)

        assert loaded.sonnet_enabled is True
        assert loaded.sonnet_streaming is True
        assert loaded.sonnet_colors is True

    def test_config_sonnet_disabled_persists(self, tmp_path: Path) -> None:
        """Disabled Sonnet settings persist correctly."""
        config_path = tmp_path / "disabled_config.json"

        config = Config(
            sonnet_enabled=False,
            sonnet_streaming=False,
            sonnet_colors=False,
        )

        config.save_to_file(config_path)
        loaded = Config.load_from_file(config_path)

        assert loaded.sonnet_enabled is False
        assert loaded.sonnet_streaming is False
        assert loaded.sonnet_colors is False

    def test_config_partial_sonnet_settings(self, tmp_path: Path) -> None:
        """Partial Sonnet settings persist independently."""
        config_path = tmp_path / "partial_config.json"

        # Enabled but no streaming or colors
        config = Config(
            sonnet_enabled=True,
            sonnet_streaming=False,
            sonnet_colors=False,
        )

        config.save_to_file(config_path)
        loaded = Config.load_from_file(config_path)

        assert loaded.sonnet_enabled is True
        assert loaded.sonnet_streaming is False
        assert loaded.sonnet_colors is False

    def test_config_other_settings_unaffected(self, tmp_path: Path) -> None:
        """Sonnet settings don't affect other config values."""
        config_path = tmp_path / "mixed_config.json"

        config = Config(
            sonnet_enabled=True,
            sonnet_streaming=True,
            sonnet_colors=True,
            verbose=True,
            simulate=True,
            main_branch="main",
            quit_on_conflict=True,
        )

        config.save_to_file(config_path)
        loaded = Config.load_from_file(config_path)

        # Verify Sonnet settings
        assert loaded.sonnet_enabled is True
        assert loaded.sonnet_streaming is True
        assert loaded.sonnet_colors is True

        # Verify other settings preserved
        assert loaded.verbose is True
        assert loaded.simulate is True
        assert loaded.main_branch == "main"
        assert loaded.quit_on_conflict is True

    def test_config_json_format(self, tmp_path: Path) -> None:
        """Config saves in readable JSON format."""
        config_path = tmp_path / "format_config.json"

        config = Config(
            sonnet_enabled=True,
            sonnet_streaming=False,
            sonnet_colors=True,
        )

        config.save_to_file(config_path)

        # Read and verify JSON format
        with config_path.open("rb") as f:
            data = orjson.loads(f.read())

        assert "sonnet_enabled" in data
        assert "sonnet_streaming" in data
        assert "sonnet_colors" in data
        assert data["sonnet_enabled"] is True
        assert data["sonnet_streaming"] is False
        assert data["sonnet_colors"] is True

"""
Tests for Settings module.
"""
import pytest
import os
import tempfile
from pathlib import Path

from infrastructure.settings import Settings, VeoSettings


class TestSettings:
    """Tests for application settings."""

    def test_loads_from_env(self, monkeypatch):
        """Should load settings from environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("GOOGLE_API_KEYS", "key1,key2")
        monkeypatch.setenv("GOOGLE_PROJECT_ID", "my-project")

        settings = Settings()

        assert settings.openai_api_key == "sk-test-key"
        assert settings.google_project_id == "my-project"

    def test_parses_multiple_google_keys(self, monkeypatch):
        """Should parse comma-separated Google API keys."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("GOOGLE_API_KEYS", "key1,key2,key3")
        monkeypatch.setenv("GOOGLE_PROJECT_ID", "my-project")

        settings = Settings()

        assert settings.google_api_keys_list == ["key1", "key2", "key3"]

    def test_parses_keys_with_aliases(self, monkeypatch):
        """Should parse key:alias format."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("GOOGLE_API_KEYS", "abc123:prod-main,def456:test-backup")
        monkeypatch.setenv("GOOGLE_PROJECT_ID", "my-project")

        settings = Settings()

        # Keys only
        assert settings.google_api_keys_list == ["abc123", "def456"]

        # Full info with aliases (uses default project)
        infos = settings.google_api_key_infos
        assert len(infos) == 2
        assert infos[0].key == "abc123"
        assert infos[0].alias == "prod-main"
        assert infos[0].project_id == "my-project"  # Default project
        assert infos[1].key == "def456"
        assert infos[1].alias == "test-backup"

    def test_parses_mixed_format(self, monkeypatch):
        """Should handle mixed format (some with alias, some without)."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("GOOGLE_API_KEYS", "key1:prod,key2,key3:backup")
        monkeypatch.setenv("GOOGLE_PROJECT_ID", "my-project")

        settings = Settings()

        infos = settings.google_api_key_infos
        assert infos[0].alias == "prod"
        assert infos[1].alias == "key-1"  # Auto-generated
        assert infos[2].alias == "backup"

    def test_parses_keys_with_project_ids(self, monkeypatch):
        """Should parse key:alias:project_id format."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("GOOGLE_API_KEYS", "abc123:prod:project-a,def456:backup:project-b")

        settings = Settings()

        infos = settings.google_api_key_infos
        assert infos[0].key == "abc123"
        assert infos[0].alias == "prod"
        assert infos[0].project_id == "project-a"
        assert infos[1].key == "def456"
        assert infos[1].alias == "backup"
        assert infos[1].project_id == "project-b"

    def test_mixed_project_ids(self, monkeypatch):
        """Should mix per-key and default project IDs."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("GOOGLE_API_KEYS", "key1:prod:explicit-project,key2:backup")
        monkeypatch.setenv("GOOGLE_PROJECT_ID", "default-project")

        settings = Settings()

        infos = settings.google_api_key_infos
        assert infos[0].project_id == "explicit-project"  # Explicit
        assert infos[1].project_id == "default-project"   # Falls back to default

    def test_default_values(self, monkeypatch):
        """Should have sensible defaults."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("GOOGLE_API_KEYS", "key1")
        monkeypatch.setenv("GOOGLE_PROJECT_ID", "my-project")

        settings = Settings()

        assert settings.google_location == "us-central1"
        assert settings.output_dir == Path("./generated_videos")

    def test_veo_settings(self, monkeypatch):
        """Should parse Veo-specific settings."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("GOOGLE_API_KEYS", "key1")
        monkeypatch.setenv("GOOGLE_PROJECT_ID", "my-project")
        monkeypatch.setenv("VEO_KEY_ROTATION_STRATEGY", "least_used")
        monkeypatch.setenv("VEO_DAILY_LIMIT_PER_KEY", "5")
        monkeypatch.setenv("VEO_MAX_CONCURRENT_PER_KEY", "3")

        settings = Settings()

        assert settings.veo.rotation_strategy == "least_used"
        assert settings.veo.daily_limit_per_key == 5
        assert settings.veo.max_concurrent_per_key == 3


class TestVeoSettings:
    """Tests for Veo-specific settings."""

    def test_default_rotation_strategy(self):
        """Should default to round_robin."""
        veo = VeoSettings()
        assert veo.rotation_strategy == "round_robin"

    def test_default_limits(self):
        """Should have default limits."""
        veo = VeoSettings()
        assert veo.daily_limit_per_key == 10
        assert veo.max_concurrent_per_key == 2

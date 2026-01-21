"""Unit tests for ConfigurationManager."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from src.ai_product_enricher.engine.config_manager import (
    CacheConfig,
    ConfigurationManager,
    EnrichmentProfile,
    FieldsConfig,
    LLMConfig,
    PromptsConfig,
    WebSearchConfig,
)


class TestLLMConfig:
    """Tests for LLMConfig class."""

    def test_from_dict(self):
        """Test creating LLMConfig from dictionary."""
        data = {"temperature": 0.5, "max_tokens": 2000, "top_p": 0.9}
        config = LLMConfig.from_dict(data)

        assert config.temperature == 0.5
        assert config.max_tokens == 2000
        assert config.top_p == 0.9

    def test_from_dict_defaults(self):
        """Test that defaults are used for missing values."""
        config = LLMConfig.from_dict({})

        assert config.temperature == 0.3
        assert config.max_tokens == 4000
        assert config.top_p == 0.95

    def test_to_dict(self):
        """Test converting LLMConfig to dictionary."""
        config = LLMConfig(temperature=0.7, max_tokens=3000, top_p=0.8)
        data = config.to_dict()

        assert data["temperature"] == 0.7
        assert data["max_tokens"] == 3000
        assert data["top_p"] == 0.8


class TestCacheConfig:
    """Tests for CacheConfig class."""

    def test_from_dict(self):
        """Test creating CacheConfig from dictionary."""
        data = {"enabled": False, "ttl_seconds": 7200}
        config = CacheConfig.from_dict(data)

        assert config.enabled is False
        assert config.ttl_seconds == 7200

    def test_to_dict(self):
        """Test converting CacheConfig to dictionary."""
        config = CacheConfig(enabled=True, ttl_seconds=1800)
        data = config.to_dict()

        assert data["enabled"] is True
        assert data["ttl_seconds"] == 1800


class TestEnrichmentProfile:
    """Tests for EnrichmentProfile class."""

    def test_from_dict_full(self):
        """Test creating EnrichmentProfile from complete dictionary."""
        data = {
            "name": "test_profile",
            "description": "Test profile",
            "version": "1.0",
            "is_default": True,
            "prompts": {"system": "custom_system", "user": "custom_user"},
            "fields": {
                "preset": "default",
                "enabled": ["manufacturer", "category"],
                "custom": ["custom_field"],
            },
            "llm": {"temperature": 0.5, "max_tokens": 3000, "top_p": 0.9},
            "cache": {"enabled": True, "ttl_seconds": 7200},
            "web_search": {"enabled": True, "max_results": 10},
        }
        profile = EnrichmentProfile.from_dict(data)

        assert profile.name == "test_profile"
        assert profile.description == "Test profile"
        assert profile.is_default is True
        assert profile.prompts.system == "custom_system"
        assert profile.fields.enabled == ["manufacturer", "category"]
        assert profile.llm.temperature == 0.5
        assert profile.cache.ttl_seconds == 7200
        assert profile.web_search.max_results == 10

    def test_to_dict(self):
        """Test converting EnrichmentProfile to dictionary."""
        profile = EnrichmentProfile(
            name="test",
            description="Test",
            version="1.0",
            is_default=False,
        )
        data = profile.to_dict()

        assert data["name"] == "test"
        assert "prompts" in data
        assert "fields" in data
        assert "llm" in data
        assert "cache" in data


class TestConfigurationManager:
    """Tests for ConfigurationManager class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory with profiles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create profiles directories
            profiles_dir = config_dir / "profiles"
            custom_dir = profiles_dir / "custom"
            profiles_dir.mkdir(parents=True)
            custom_dir.mkdir(parents=True)

            # Create default profile
            default_profile = {
                "name": "default",
                "description": "Default profile",
                "version": "1.0",
                "is_default": True,
                "prompts": {"system": "default", "user": "default"},
                "fields": {
                    "preset": "default",
                    "enabled": ["manufacturer", "trademark", "category"],
                    "custom": [],
                },
                "llm": {"temperature": 0.3, "max_tokens": 4000, "top_p": 0.95},
                "cache": {"enabled": True, "ttl_seconds": 3600},
                "web_search": {"enabled": True, "max_results": 5},
            }
            with open(profiles_dir / "default.yaml", "w", encoding="utf-8") as f:
                yaml.dump(default_profile, f, allow_unicode=True)

            yield config_dir

    def test_load_profiles(self, temp_config_dir):
        """Test loading profiles from YAML files."""
        manager = ConfigurationManager(temp_config_dir)

        assert "default" in manager.list_profiles()
        profile = manager.get_profile("default")
        assert profile is not None
        assert profile.name == "default"

    def test_get_profile(self, temp_config_dir):
        """Test getting a specific profile."""
        manager = ConfigurationManager(temp_config_dir)

        profile = manager.get_profile("default")
        assert profile is not None
        assert profile.prompts.system == "default"
        assert profile.llm.temperature == 0.3

    def test_default_profile_always_exists(self):
        """Test that default profile is created when no config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigurationManager(Path(tmpdir))

            assert "default" in manager.list_profiles()
            profile = manager.get_profile("default")
            assert profile is not None

    def test_get_active_profile(self, temp_config_dir):
        """Test getting the active profile."""
        manager = ConfigurationManager(temp_config_dir)

        active = manager.get_active_profile()
        assert active is not None
        assert active.is_default is True

    def test_set_active_profile(self, temp_config_dir):
        """Test setting the active profile."""
        manager = ConfigurationManager(temp_config_dir)

        # Create a second profile
        new_profile = manager.create_profile_from_current("second", "Second profile")
        manager.save_profile(new_profile)

        # Set it as active
        result = manager.set_active_profile("second")
        assert result is True

        # Verify
        active = manager.get_active_profile()
        assert active.name == "second"

    def test_set_active_profile_nonexistent(self, temp_config_dir):
        """Test setting a nonexistent profile as active."""
        manager = ConfigurationManager(temp_config_dir)

        result = manager.set_active_profile("nonexistent")
        assert result is False

    def test_save_profile(self, temp_config_dir):
        """Test saving a profile."""
        manager = ConfigurationManager(temp_config_dir)

        new_profile = EnrichmentProfile(
            name="saved",
            description="Saved profile",
            version="1.0",
        )

        result = manager.save_profile(new_profile, overwrite=True)
        assert result is True

        # Verify it was saved
        loaded = manager.get_profile("saved")
        assert loaded is not None
        assert loaded.description == "Saved profile"

    def test_save_profile_no_overwrite(self, temp_config_dir):
        """Test that save_profile respects overwrite=False."""
        manager = ConfigurationManager(temp_config_dir)

        # First save
        profile1 = EnrichmentProfile(name="no_overwrite", description="First")
        result1 = manager.save_profile(profile1, overwrite=False)
        assert result1 is True

        # Try to overwrite
        profile2 = EnrichmentProfile(name="no_overwrite", description="Second")
        result2 = manager.save_profile(profile2, overwrite=False)
        assert result2 is False

    def test_delete_profile(self, temp_config_dir):
        """Test deleting a profile."""
        manager = ConfigurationManager(temp_config_dir)

        # Create a profile to delete
        profile = EnrichmentProfile(name="to_delete", description="Will be deleted")
        manager.save_profile(profile, overwrite=True)

        # Delete it
        result = manager.delete_profile("to_delete")
        assert result is True

        # Verify it's gone
        loaded = manager.get_profile("to_delete")
        assert loaded is None

    def test_cannot_delete_default(self, temp_config_dir):
        """Test that default profile cannot be deleted."""
        manager = ConfigurationManager(temp_config_dir)

        result = manager.delete_profile("default")
        assert result is False

        # Verify it still exists
        loaded = manager.get_profile("default")
        assert loaded is not None

    def test_create_profile_from_current(self, temp_config_dir):
        """Test creating a new profile based on current active profile."""
        manager = ConfigurationManager(temp_config_dir)

        # Modify active profile
        active = manager.get_active_profile()
        active.llm.temperature = 0.7

        # Create new profile from it
        new_profile = manager.create_profile_from_current("derived", "Derived profile")

        assert new_profile.name == "derived"
        assert new_profile.llm.temperature == 0.7
        assert new_profile.is_default is False

    def test_update_profile_setting(self, temp_config_dir):
        """Test updating a single profile setting."""
        manager = ConfigurationManager(temp_config_dir)

        result = manager.update_profile_setting("default", "llm", "temperature", 0.8)
        assert result is True

        profile = manager.get_profile("default")
        assert profile.llm.temperature == 0.8

    def test_update_profile_setting_invalid(self, temp_config_dir):
        """Test updating invalid profile setting."""
        manager = ConfigurationManager(temp_config_dir)

        # Invalid profile
        result1 = manager.update_profile_setting("nonexistent", "llm", "temperature", 0.8)
        assert result1 is False

        # Invalid section
        result2 = manager.update_profile_setting("default", "invalid", "key", "value")
        assert result2 is False

        # Invalid key
        result3 = manager.update_profile_setting("default", "llm", "invalid_key", "value")
        assert result3 is False

    def test_reload(self, temp_config_dir):
        """Test reloading profiles."""
        manager = ConfigurationManager(temp_config_dir)

        # Add a new profile file
        new_profile = {
            "name": "new_profile",
            "description": "New profile",
            "version": "1.0",
            "is_default": False,
            "prompts": {"system": "default", "user": "default"},
            "fields": {"preset": "default", "enabled": [], "custom": []},
            "llm": {"temperature": 0.5, "max_tokens": 2000, "top_p": 0.9},
            "cache": {"enabled": True, "ttl_seconds": 3600},
            "web_search": {"enabled": True, "max_results": 5},
        }
        with open(temp_config_dir / "profiles" / "new.yaml", "w", encoding="utf-8") as f:
            yaml.dump(new_profile, f, allow_unicode=True)

        # Reload
        manager.reload()

        # Check new profile is loaded
        assert "new_profile" in manager.list_profiles()

    def test_get_all_profiles(self, temp_config_dir):
        """Test getting all profiles."""
        manager = ConfigurationManager(temp_config_dir)

        # Create additional profile
        profile = EnrichmentProfile(name="extra", description="Extra")
        manager.save_profile(profile, overwrite=True)

        all_profiles = manager.get_all_profiles()
        assert "default" in all_profiles
        assert "extra" in all_profiles

    def test_delete_active_profile_switches_to_default(self, temp_config_dir):
        """Test that deleting active profile switches to default."""
        manager = ConfigurationManager(temp_config_dir)

        # Create and activate a profile
        profile = EnrichmentProfile(name="active_to_delete", description="Will be deleted")
        manager.save_profile(profile, overwrite=True)
        manager.set_active_profile("active_to_delete")

        # Delete it
        manager.delete_profile("active_to_delete")

        # Check that default is now active
        active = manager.get_active_profile()
        assert active.name == "default"

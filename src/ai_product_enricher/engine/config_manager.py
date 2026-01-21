"""Configuration Manager for enrichment profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LLMConfig:
    """LLM configuration settings."""

    temperature: float = 0.3
    max_tokens: int = 4000
    top_p: float = 0.95

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LLMConfig:
        """Create LLMConfig from dictionary."""
        return cls(
            temperature=data.get("temperature", 0.3),
            max_tokens=data.get("max_tokens", 4000),
            top_p=data.get("top_p", 0.95),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }


@dataclass
class CacheConfig:
    """Cache configuration settings."""

    enabled: bool = True
    ttl_seconds: int = 3600

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheConfig:
        """Create CacheConfig from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            ttl_seconds=data.get("ttl_seconds", 3600),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "ttl_seconds": self.ttl_seconds,
        }


@dataclass
class WebSearchConfig:
    """Web search configuration settings."""

    enabled: bool = True
    max_results: int = 5

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WebSearchConfig:
        """Create WebSearchConfig from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            max_results=data.get("max_results", 5),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "max_results": self.max_results,
        }


@dataclass
class PromptsConfig:
    """Prompts configuration."""

    system: str = "default"
    user: str = "default"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptsConfig:
        """Create PromptsConfig from dictionary."""
        return cls(
            system=data.get("system", "default"),
            user=data.get("user", "default"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "system": self.system,
            "user": self.user,
        }


@dataclass
class FieldsConfig:
    """Fields configuration."""

    preset: str = "default"
    enabled: list[str] = field(default_factory=lambda: [
        "manufacturer",
        "trademark",
        "category",
        "model_name",
        "description",
        "features",
        "specifications",
        "seo_keywords",
    ])
    custom: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FieldsConfig:
        """Create FieldsConfig from dictionary."""
        return cls(
            preset=data.get("preset", "default"),
            enabled=data.get("enabled", [
                "manufacturer",
                "trademark",
                "category",
                "model_name",
                "description",
                "features",
                "specifications",
                "seo_keywords",
            ]),
            custom=data.get("custom", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "preset": self.preset,
            "enabled": self.enabled,
            "custom": self.custom,
        }


@dataclass
class EnrichmentProfile:
    """Complete enrichment profile."""

    name: str
    description: str = ""
    version: str = "1.0"
    is_default: bool = False
    prompts: PromptsConfig = field(default_factory=PromptsConfig)
    fields: FieldsConfig = field(default_factory=FieldsConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    web_search: WebSearchConfig = field(default_factory=WebSearchConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnrichmentProfile:
        """Create EnrichmentProfile from dictionary."""
        return cls(
            name=data.get("name", "unknown"),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            is_default=data.get("is_default", False),
            prompts=PromptsConfig.from_dict(data.get("prompts", {})),
            fields=FieldsConfig.from_dict(data.get("fields", {})),
            llm=LLMConfig.from_dict(data.get("llm", {})),
            cache=CacheConfig.from_dict(data.get("cache", {})),
            web_search=WebSearchConfig.from_dict(data.get("web_search", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "is_default": self.is_default,
            "prompts": self.prompts.to_dict(),
            "fields": self.fields.to_dict(),
            "llm": self.llm.to_dict(),
            "cache": self.cache.to_dict(),
            "web_search": self.web_search.to_dict(),
        }


class ConfigurationManager:
    """Manager for enrichment profiles and configuration."""

    def __init__(self, config_dir: Path | str | None = None) -> None:
        """Initialize the configuration manager.

        Args:
            config_dir: Path to config directory. If None, uses default location.
        """
        if config_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)
        self.profiles_dir = self.config_dir / "profiles"
        self.custom_dir = self.profiles_dir / "custom"

        self._profiles: dict[str, EnrichmentProfile] = {}
        self._active_profile_name: str = "default"

        self._load_profiles()

    def _load_profiles(self) -> None:
        """Load all profiles from YAML files."""
        self._profiles = {}

        # Load from profiles directory
        if self.profiles_dir.exists():
            for yaml_file in self.profiles_dir.glob("*.yaml"):
                self._load_profile_file(yaml_file)

            # Load custom profiles
            if self.custom_dir.exists():
                for yaml_file in self.custom_dir.glob("*.yaml"):
                    self._load_profile_file(yaml_file)

        # Ensure default profile always exists
        if "default" not in self._profiles:
            self._create_default_profile()

        # Find and set active profile
        for profile in self._profiles.values():
            if profile.is_default:
                self._active_profile_name = profile.name
                break

    def _load_profile_file(self, file_path: Path) -> None:
        """Load a single profile from YAML file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    profile = EnrichmentProfile.from_dict(data)
                    self._profiles[profile.name] = profile
        except Exception as e:
            print(f"Error loading profile from {file_path}: {e}")

    def _create_default_profile(self) -> None:
        """Create a default profile in memory."""
        self._profiles["default"] = EnrichmentProfile(
            name="default",
            description="Стандартный профиль обогащения (создан в памяти)",
            version="1.0",
            is_default=True,
        )

    def get_profile(self, name: str) -> EnrichmentProfile | None:
        """Get a profile by name."""
        return self._profiles.get(name)

    def get_active_profile(self) -> EnrichmentProfile:
        """Get the currently active profile."""
        profile = self._profiles.get(self._active_profile_name)
        if profile is None:
            profile = self._profiles.get("default")
        if profile is None:
            self._create_default_profile()
            profile = self._profiles["default"]
        return profile

    def set_active_profile(self, name: str) -> bool:
        """Set the active profile.

        Args:
            name: Name of the profile to activate.

        Returns:
            True if profile was activated, False if not found.
        """
        if name in self._profiles:
            # Update is_default flags
            for profile in self._profiles.values():
                profile.is_default = (profile.name == name)
            self._active_profile_name = name
            return True
        return False

    def list_profiles(self) -> list[str]:
        """List all available profile names."""
        return list(self._profiles.keys())

    def get_all_profiles(self) -> dict[str, EnrichmentProfile]:
        """Get all loaded profiles."""
        return self._profiles.copy()

    def save_profile(self, profile: EnrichmentProfile, overwrite: bool = False) -> bool:
        """Save a profile to YAML file.

        Args:
            profile: The profile to save.
            overwrite: Whether to overwrite existing file.

        Returns:
            True if saved successfully, False otherwise.
        """
        # Determine target directory
        if profile.name == "default":
            target_dir = self.profiles_dir
        else:
            target_dir = self.custom_dir

        # Ensure directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / f"{profile.name}.yaml"

        if file_path.exists() and not overwrite:
            return False

        try:
            data = profile.to_dict()
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            # Update in-memory cache
            self._profiles[profile.name] = profile

            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False

    def delete_profile(self, name: str) -> bool:
        """Delete a profile.

        Args:
            name: Name of the profile to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        # Protect default profile
        if name == "default":
            return False

        # Don't delete active profile
        if name == self._active_profile_name:
            self._active_profile_name = "default"

        # Try to delete file
        file_path = self.custom_dir / f"{name}.yaml"
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass

        # Also check main profiles dir (shouldn't be there but just in case)
        file_path = self.profiles_dir / f"{name}.yaml"
        try:
            if file_path.exists() and name != "default":
                file_path.unlink()
        except Exception:
            pass

        # Remove from memory
        if name in self._profiles:
            del self._profiles[name]
            return True

        return False

    def create_profile_from_current(self, new_name: str, description: str = "") -> EnrichmentProfile:
        """Create a new profile based on the current active profile.

        Args:
            new_name: Name for the new profile.
            description: Description for the new profile.

        Returns:
            The newly created profile.
        """
        current = self.get_active_profile()

        new_profile = EnrichmentProfile(
            name=new_name,
            description=description or f"Создан на основе профиля '{current.name}'",
            version="1.0",
            is_default=False,
            prompts=PromptsConfig(
                system=current.prompts.system,
                user=current.prompts.user,
            ),
            fields=FieldsConfig(
                preset=current.fields.preset,
                enabled=current.fields.enabled.copy(),
                custom=current.fields.custom.copy(),
            ),
            llm=LLMConfig(
                temperature=current.llm.temperature,
                max_tokens=current.llm.max_tokens,
                top_p=current.llm.top_p,
            ),
            cache=CacheConfig(
                enabled=current.cache.enabled,
                ttl_seconds=current.cache.ttl_seconds,
            ),
            web_search=WebSearchConfig(
                enabled=current.web_search.enabled,
                max_results=current.web_search.max_results,
            ),
        )

        self._profiles[new_name] = new_profile
        return new_profile

    def update_profile_setting(
        self,
        profile_name: str,
        section: str,
        key: str,
        value: Any,
    ) -> bool:
        """Update a single setting in a profile.

        Args:
            profile_name: Name of the profile to update.
            section: Section name (prompts, fields, llm, cache, web_search).
            key: Key within the section.
            value: New value.

        Returns:
            True if updated successfully, False otherwise.
        """
        profile = self._profiles.get(profile_name)
        if not profile:
            return False

        section_obj = getattr(profile, section, None)
        if section_obj is None:
            return False

        if hasattr(section_obj, key):
            setattr(section_obj, key, value)
            return True

        return False

    def reload(self) -> None:
        """Reload all profiles from disk."""
        self._load_profiles()

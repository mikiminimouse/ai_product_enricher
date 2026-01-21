"""Field Registry for managing enrichment field definitions."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class FieldExample:
    """Example of field extraction."""

    input: str
    output: Any


@dataclass
class FieldDefinition:
    """Definition of an enrichment field."""

    name: str
    display_name: str
    description: str
    type: str  # string, array, object
    required: bool = False
    extraction_hints: list[str] = field(default_factory=list)
    examples: list[FieldExample] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> FieldDefinition:
        """Create FieldDefinition from dictionary."""
        examples = []
        for ex in data.get("examples", []):
            examples.append(FieldExample(input=ex["input"], output=ex["output"]))

        return cls(
            name=name,
            display_name=data.get("display_name", name),
            description=data.get("description", ""),
            type=data.get("type", "string"),
            required=data.get("required", False),
            extraction_hints=data.get("extraction_hints", []),
            examples=examples,
            validation=data.get("validation", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result: dict[str, Any] = {
            "display_name": self.display_name,
            "description": self.description,
            "type": self.type,
            "required": self.required,
        }
        if self.extraction_hints:
            result["extraction_hints"] = self.extraction_hints
        if self.examples:
            result["examples"] = [
                {"input": ex.input, "output": ex.output} for ex in self.examples
            ]
        if self.validation:
            result["validation"] = self.validation
        return result


@dataclass
class FieldSet:
    """A set of field definitions loaded from YAML."""

    name: str
    description: str
    version: str
    fields: dict[str, FieldDefinition]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FieldSet:
        """Create FieldSet from dictionary."""
        fields = {}
        for field_name, field_data in data.get("fields", {}).items():
            fields[field_name] = FieldDefinition.from_dict(field_name, field_data)

        return cls(
            name=data.get("name", "unknown"),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            fields=fields,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "fields": {name: f.to_dict() for name, f in self.fields.items()},
        }


class FieldRegistry:
    """Registry for managing field definitions."""

    def __init__(self, config_dir: Path | str | None = None) -> None:
        """Initialize the registry.

        Args:
            config_dir: Path to config directory. If None, uses default location.
        """
        if config_dir is None:
            # Try to find config dir relative to project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)
        self.fields_dir = self.config_dir / "fields"
        self.custom_dir = self.fields_dir / "custom"

        self._field_sets: dict[str, FieldSet] = {}
        self._load_field_sets()

    def _load_field_sets(self) -> None:
        """Load all field sets from YAML files."""
        self._field_sets = {}

        # Load from fields directory
        if self.fields_dir.exists():
            for yaml_file in self.fields_dir.glob("*.yaml"):
                self._load_field_set_file(yaml_file)

            # Load custom fields
            if self.custom_dir.exists():
                for yaml_file in self.custom_dir.glob("*.yaml"):
                    self._load_field_set_file(yaml_file, is_custom=True)

        # If no field sets loaded, create default in memory
        if not self._field_sets:
            self._create_default_field_set()

    def _load_field_set_file(self, file_path: Path, is_custom: bool = False) -> None:
        """Load a single field set from YAML file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    field_set = FieldSet.from_dict(data)
                    if is_custom:
                        field_set.name = f"custom:{field_set.name}"
                    self._field_sets[field_set.name] = field_set
        except Exception as e:
            # Log error but continue loading other files
            print(f"Error loading field set from {file_path}: {e}")

    def _create_default_field_set(self) -> None:
        """Create a default field set in memory when no config files exist."""
        default_fields = {
            "manufacturer": FieldDefinition(
                name="manufacturer",
                display_name="Производитель",
                description="Компания-производитель товара",
                type="string",
            ),
            "trademark": FieldDefinition(
                name="trademark",
                display_name="Торговая марка",
                description="Бренд или торговая марка товара",
                type="string",
            ),
            "category": FieldDefinition(
                name="category",
                display_name="Категория",
                description="Товарная категория",
                type="string",
            ),
            "model_name": FieldDefinition(
                name="model_name",
                display_name="Модель",
                description="Название модели или артикул",
                type="string",
            ),
            "description": FieldDefinition(
                name="description",
                display_name="Описание",
                description="Краткое описание товара",
                type="string",
            ),
            "features": FieldDefinition(
                name="features",
                display_name="Характеристики",
                description="Ключевые особенности товара",
                type="array",
            ),
            "specifications": FieldDefinition(
                name="specifications",
                display_name="Технические характеристики",
                description="Словарь технических параметров",
                type="object",
            ),
            "seo_keywords": FieldDefinition(
                name="seo_keywords",
                display_name="SEO ключевые слова",
                description="Ключевые слова для поисковой оптимизации",
                type="array",
            ),
        }

        self._field_sets["default"] = FieldSet(
            name="default",
            description="Стандартный набор полей (создан в памяти)",
            version="1.0",
            fields=default_fields,
        )

    def get_field_set(self, name: str = "default") -> FieldSet | None:
        """Get a field set by name."""
        return self._field_sets.get(name)

    def get_field(self, field_name: str, field_set_name: str = "default") -> FieldDefinition | None:
        """Get a specific field definition."""
        field_set = self.get_field_set(field_set_name)
        if field_set:
            return field_set.fields.get(field_name)
        return None

    def get_all_field_sets(self) -> dict[str, FieldSet]:
        """Get all loaded field sets."""
        return self._field_sets.copy()

    def get_fields_for_extraction(
        self,
        field_names: list[str],
        field_set_name: str = "default",
    ) -> list[FieldDefinition]:
        """Get field definitions for a list of field names.

        Args:
            field_names: List of field names to retrieve.
            field_set_name: Name of the field set to use.

        Returns:
            List of FieldDefinition objects for the requested fields.
        """
        field_set = self.get_field_set(field_set_name)
        if not field_set:
            return []

        result = []
        for name in field_names:
            field_def = field_set.fields.get(name)
            if field_def:
                result.append(field_def)

        return result

    def add_custom_field(
        self,
        field_def: FieldDefinition,
        custom_set_name: str = "custom",
    ) -> None:
        """Add a custom field to a custom field set.

        Args:
            field_def: The field definition to add.
            custom_set_name: Name of the custom field set (without 'custom:' prefix).
        """
        full_name = f"custom:{custom_set_name}"

        if full_name not in self._field_sets:
            self._field_sets[full_name] = FieldSet(
                name=full_name,
                description=f"Custom fields: {custom_set_name}",
                version="1.0",
                fields={},
            )

        self._field_sets[full_name].fields[field_def.name] = field_def

    def remove_custom_field(
        self,
        field_name: str,
        custom_set_name: str = "custom",
    ) -> bool:
        """Remove a custom field from a custom field set.

        Args:
            field_name: Name of the field to remove.
            custom_set_name: Name of the custom field set.

        Returns:
            True if field was removed, False if not found.
        """
        full_name = f"custom:{custom_set_name}"

        if full_name in self._field_sets:
            if field_name in self._field_sets[full_name].fields:
                del self._field_sets[full_name].fields[field_name]
                return True
        return False

    def save_custom_fields(self, custom_set_name: str = "custom") -> bool:
        """Save custom fields to YAML file.

        Args:
            custom_set_name: Name of the custom field set to save.

        Returns:
            True if saved successfully, False otherwise.
        """
        full_name = f"custom:{custom_set_name}"

        if full_name not in self._field_sets:
            return False

        # Ensure custom directory exists
        self.custom_dir.mkdir(parents=True, exist_ok=True)

        file_path = self.custom_dir / f"{custom_set_name}.yaml"

        try:
            field_set = self._field_sets[full_name]
            # Save without the 'custom:' prefix in the file
            data = field_set.to_dict()
            data["name"] = custom_set_name  # Remove prefix for storage

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            return True
        except Exception as e:
            print(f"Error saving custom fields: {e}")
            return False

    def load_custom_fields(self, custom_set_name: str = "custom") -> bool:
        """Reload custom fields from YAML file.

        Args:
            custom_set_name: Name of the custom field set to load.

        Returns:
            True if loaded successfully, False otherwise.
        """
        file_path = self.custom_dir / f"{custom_set_name}.yaml"

        if not file_path.exists():
            return False

        try:
            self._load_field_set_file(file_path, is_custom=True)
            return True
        except Exception:
            return False

    def list_available_fields(self, field_set_name: str = "default") -> list[str]:
        """List all available field names in a field set.

        Args:
            field_set_name: Name of the field set.

        Returns:
            List of field names.
        """
        field_set = self.get_field_set(field_set_name)
        if field_set:
            return list(field_set.fields.keys())
        return []

    def reload(self) -> None:
        """Reload all field sets from disk."""
        self._load_field_sets()

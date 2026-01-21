"""Unit tests for FieldRegistry."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from src.ai_product_enricher.engine.field_registry import (
    FieldDefinition,
    FieldExample,
    FieldRegistry,
    FieldSet,
)


class TestFieldDefinition:
    """Tests for FieldDefinition class."""

    def test_from_dict_basic(self):
        """Test creating FieldDefinition from dictionary."""
        data = {
            "display_name": "Производитель",
            "description": "Компания-производитель",
            "type": "string",
            "required": True,
        }
        field = FieldDefinition.from_dict("manufacturer", data)

        assert field.name == "manufacturer"
        assert field.display_name == "Производитель"
        assert field.description == "Компания-производитель"
        assert field.type == "string"
        assert field.required is True

    def test_from_dict_with_examples(self):
        """Test creating FieldDefinition with examples."""
        data = {
            "display_name": "Производитель",
            "description": "Компания-производитель",
            "type": "string",
            "examples": [
                {"input": "iPhone 15 Pro", "output": "Apple"},
                {"input": "Galaxy S24", "output": "Samsung"},
            ],
        }
        field = FieldDefinition.from_dict("manufacturer", data)

        assert len(field.examples) == 2
        assert field.examples[0].input == "iPhone 15 Pro"
        assert field.examples[0].output == "Apple"

    def test_to_dict(self):
        """Test converting FieldDefinition to dictionary."""
        field = FieldDefinition(
            name="category",
            display_name="Категория",
            description="Товарная категория",
            type="string",
            extraction_hints=["Hint 1", "Hint 2"],
        )
        data = field.to_dict()

        assert data["display_name"] == "Категория"
        assert data["type"] == "string"
        assert len(data["extraction_hints"]) == 2


class TestFieldSet:
    """Tests for FieldSet class."""

    def test_from_dict(self):
        """Test creating FieldSet from dictionary."""
        data = {
            "name": "test_set",
            "description": "Test field set",
            "version": "1.0",
            "fields": {
                "field1": {
                    "display_name": "Field 1",
                    "description": "First field",
                    "type": "string",
                },
                "field2": {
                    "display_name": "Field 2",
                    "description": "Second field",
                    "type": "array",
                },
            },
        }
        field_set = FieldSet.from_dict(data)

        assert field_set.name == "test_set"
        assert field_set.description == "Test field set"
        assert len(field_set.fields) == 2
        assert "field1" in field_set.fields
        assert "field2" in field_set.fields

    def test_to_dict(self):
        """Test converting FieldSet to dictionary."""
        field_set = FieldSet(
            name="test",
            description="Test set",
            version="1.0",
            fields={
                "test_field": FieldDefinition(
                    name="test_field",
                    display_name="Test",
                    description="Test field",
                    type="string",
                ),
            },
        )
        data = field_set.to_dict()

        assert data["name"] == "test"
        assert "test_field" in data["fields"]


class TestFieldRegistry:
    """Tests for FieldRegistry class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            fields_dir = config_dir / "fields"
            fields_dir.mkdir(parents=True)

            # Create a test field set
            test_data = {
                "name": "default",
                "description": "Test field set",
                "version": "1.0",
                "fields": {
                    "manufacturer": {
                        "display_name": "Производитель",
                        "description": "Компания-производитель",
                        "type": "string",
                    },
                    "category": {
                        "display_name": "Категория",
                        "description": "Товарная категория",
                        "type": "string",
                    },
                },
            }
            with open(fields_dir / "default.yaml", "w", encoding="utf-8") as f:
                yaml.dump(test_data, f, allow_unicode=True)

            yield config_dir

    def test_load_field_sets(self, temp_config_dir):
        """Test loading field sets from YAML files."""
        registry = FieldRegistry(temp_config_dir)

        assert "default" in registry.get_all_field_sets()
        field_set = registry.get_field_set("default")
        assert field_set is not None
        assert len(field_set.fields) == 2

    def test_get_field(self, temp_config_dir):
        """Test getting a specific field."""
        registry = FieldRegistry(temp_config_dir)

        field = registry.get_field("manufacturer", "default")
        assert field is not None
        assert field.display_name == "Производитель"

    def test_get_fields_for_extraction(self, temp_config_dir):
        """Test getting multiple fields for extraction."""
        registry = FieldRegistry(temp_config_dir)

        fields = registry.get_fields_for_extraction(["manufacturer", "category"])
        assert len(fields) == 2
        assert fields[0].name in ["manufacturer", "category"]

    def test_default_field_set_created(self):
        """Test that default field set is created when no config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty directory - no config files
            registry = FieldRegistry(Path(tmpdir))

            assert "default" in registry.get_all_field_sets()
            field_set = registry.get_field_set("default")
            assert field_set is not None
            assert len(field_set.fields) > 0

    def test_add_custom_field(self, temp_config_dir):
        """Test adding a custom field."""
        registry = FieldRegistry(temp_config_dir)

        custom_field = FieldDefinition(
            name="custom_field",
            display_name="Custom Field",
            description="A custom field",
            type="string",
        )
        registry.add_custom_field(custom_field, "my_custom")

        # Check it was added
        assert "custom:my_custom" in registry.get_all_field_sets()
        field_set = registry.get_field_set("custom:my_custom")
        assert "custom_field" in field_set.fields

    def test_remove_custom_field(self, temp_config_dir):
        """Test removing a custom field."""
        registry = FieldRegistry(temp_config_dir)

        # Add a field first
        custom_field = FieldDefinition(
            name="to_remove",
            display_name="To Remove",
            description="Will be removed",
            type="string",
        )
        registry.add_custom_field(custom_field, "removable")

        # Remove it
        result = registry.remove_custom_field("to_remove", "removable")
        assert result is True

        # Check it's gone
        field_set = registry.get_field_set("custom:removable")
        assert "to_remove" not in field_set.fields

    def test_save_and_load_custom_fields(self, temp_config_dir):
        """Test saving and loading custom fields."""
        registry = FieldRegistry(temp_config_dir)

        # Add custom field
        custom_field = FieldDefinition(
            name="persistent_field",
            display_name="Persistent Field",
            description="Will be saved",
            type="string",
        )
        registry.add_custom_field(custom_field, "persistent")

        # Save
        result = registry.save_custom_fields("persistent")
        assert result is True

        # Create new registry and load
        registry2 = FieldRegistry(temp_config_dir)

        # Check it was loaded
        assert "custom:persistent" in registry2.get_all_field_sets()
        field_set = registry2.get_field_set("custom:persistent")
        assert "persistent_field" in field_set.fields

    def test_list_available_fields(self, temp_config_dir):
        """Test listing available field names."""
        registry = FieldRegistry(temp_config_dir)

        fields = registry.list_available_fields("default")
        assert "manufacturer" in fields
        assert "category" in fields

    def test_reload(self, temp_config_dir):
        """Test reloading field sets."""
        registry = FieldRegistry(temp_config_dir)

        # Add a new field set file
        new_data = {
            "name": "extra",
            "description": "Extra fields",
            "version": "1.0",
            "fields": {
                "extra_field": {
                    "display_name": "Extra",
                    "description": "Extra field",
                    "type": "string",
                },
            },
        }
        with open(temp_config_dir / "fields" / "extra.yaml", "w", encoding="utf-8") as f:
            yaml.dump(new_data, f, allow_unicode=True)

        # Reload
        registry.reload()

        # Check new field set is loaded
        assert "extra" in registry.get_all_field_sets()

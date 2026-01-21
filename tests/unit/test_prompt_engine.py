"""Unit tests for PromptEngine."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from src.ai_product_enricher.engine.field_registry import FieldRegistry
from src.ai_product_enricher.engine.prompt_engine import (
    PromptEngine,
    PromptTemplate,
)


class TestPromptTemplate:
    """Tests for PromptTemplate class."""

    def test_from_dict_basic(self):
        """Test creating PromptTemplate from dictionary."""
        data = {
            "name": "test_template",
            "description": "Test template",
            "version": "1.0",
            "language": "ru",
            "template": "Hello {{ name }}!",
        }
        template = PromptTemplate.from_dict(data)

        assert template.name == "test_template"
        assert template.description == "Test template"
        assert template.language == "ru"
        assert "{{ name }}" in template.template

    def test_to_dict(self):
        """Test converting PromptTemplate to dictionary."""
        template = PromptTemplate(
            name="test",
            description="Test",
            version="1.0",
            template="Template content",
        )
        data = template.to_dict()

        assert data["name"] == "test"
        assert data["template"] == "Template content"


class TestPromptEngine:
    """Tests for PromptEngine class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory with templates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create prompts directories
            system_dir = config_dir / "prompts" / "system"
            user_dir = config_dir / "prompts" / "user"
            system_dir.mkdir(parents=True)
            user_dir.mkdir(parents=True)

            # Create fields directory for FieldRegistry
            fields_dir = config_dir / "fields"
            fields_dir.mkdir(parents=True)

            # Create test field set
            fields_data = {
                "name": "default",
                "description": "Test fields",
                "version": "1.0",
                "fields": {
                    "manufacturer": {
                        "display_name": "Производитель",
                        "description": "Компания-производитель",
                        "type": "string",
                    },
                    "category": {
                        "display_name": "Категория",
                        "description": "Категория товара",
                        "type": "string",
                    },
                },
            }
            with open(fields_dir / "default.yaml", "w", encoding="utf-8") as f:
                yaml.dump(fields_data, f, allow_unicode=True)

            # Create test system template
            system_data = {
                "name": "default",
                "description": "Default system prompt",
                "version": "1.0",
                "language": "ru",
                "template": """Язык: {{ language_name }}
{% for field in fields %}
Поле: {{ field.display_name }} ({{ field.name }})
{% endfor %}
""",
            }
            with open(system_dir / "default.yaml", "w", encoding="utf-8") as f:
                yaml.dump(system_data, f, allow_unicode=True)

            # Create test user template
            user_data = {
                "name": "default",
                "description": "Default user prompt",
                "version": "1.0",
                "template": """Товар: {{ product_name }}
{% if product_description %}Описание: {{ product_description }}{% endif %}
Поля: {{ fields_list | join(', ') }}
""",
            }
            with open(user_dir / "default.yaml", "w", encoding="utf-8") as f:
                yaml.dump(user_data, f, allow_unicode=True)

            yield config_dir

    def test_load_templates(self, temp_config_dir):
        """Test loading templates from YAML files."""
        engine = PromptEngine(temp_config_dir)

        assert "default" in engine.list_system_templates()
        assert "default" in engine.list_user_templates()

    def test_get_system_template(self, temp_config_dir):
        """Test getting a system template."""
        engine = PromptEngine(temp_config_dir)

        template = engine.get_system_template("default")
        assert template is not None
        assert template.name == "default"
        assert "{{ language_name }}" in template.template

    def test_get_user_template(self, temp_config_dir):
        """Test getting a user template."""
        engine = PromptEngine(temp_config_dir)

        template = engine.get_user_template("default")
        assert template is not None
        assert template.name == "default"
        assert "{{ product_name }}" in template.template

    def test_render_system_prompt(self, temp_config_dir):
        """Test rendering a system prompt."""
        engine = PromptEngine(temp_config_dir)
        registry = FieldRegistry(temp_config_dir)

        rendered = engine.render_system_prompt(
            template_name="default",
            field_names=["manufacturer", "category"],
            field_registry=registry,
        )

        assert "Russian" in rendered
        assert "Производитель" in rendered
        assert "Категория" in rendered

    def test_render_user_prompt(self, temp_config_dir):
        """Test rendering a user prompt."""
        engine = PromptEngine(temp_config_dir)

        rendered = engine.render_user_prompt(
            template_name="default",
            product_name="iPhone 15 Pro",
            product_description="Флагманский смартфон",
            field_names=["manufacturer", "category"],
        )

        assert "iPhone 15 Pro" in rendered
        assert "Флагманский смартфон" in rendered
        assert "manufacturer" in rendered

    def test_render_user_prompt_without_description(self, temp_config_dir):
        """Test rendering user prompt without description."""
        engine = PromptEngine(temp_config_dir)

        rendered = engine.render_user_prompt(
            template_name="default",
            product_name="iPhone 15 Pro",
            field_names=["manufacturer"],
        )

        assert "iPhone 15 Pro" in rendered
        assert "Описание:" not in rendered

    def test_default_templates_created(self):
        """Test that default templates are created when no config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = PromptEngine(Path(tmpdir))

            assert "default" in engine.list_system_templates()
            assert "default" in engine.list_user_templates()

    def test_preview_template(self, temp_config_dir):
        """Test previewing a template with sample data."""
        engine = PromptEngine(temp_config_dir)

        # Preview system template
        system_preview = engine.preview_template("system", "default")
        assert "Russian" in system_preview

        # Preview user template
        user_preview = engine.preview_template("user", "default")
        assert "Apple iPhone 15 Pro Max" in user_preview

    def test_save_template(self, temp_config_dir):
        """Test saving a template."""
        engine = PromptEngine(temp_config_dir)

        new_template = PromptTemplate(
            name="custom",
            description="Custom template",
            version="1.0",
            template="Custom: {{ product_name }}",
        )

        result = engine.save_template(new_template, "user", overwrite=True)
        assert result is True

        # Verify it was saved
        loaded = engine.get_user_template("custom")
        assert loaded is not None
        assert "Custom:" in loaded.template

    def test_save_template_no_overwrite(self, temp_config_dir):
        """Test that save_template respects overwrite=False."""
        engine = PromptEngine(temp_config_dir)

        # First save
        template1 = PromptTemplate(
            name="no_overwrite",
            description="First version",
            version="1.0",
            template="First",
        )
        result1 = engine.save_template(template1, "user", overwrite=False)
        assert result1 is True

        # Try to overwrite
        template2 = PromptTemplate(
            name="no_overwrite",
            description="Second version",
            version="2.0",
            template="Second",
        )
        result2 = engine.save_template(template2, "user", overwrite=False)
        assert result2 is False

    def test_delete_template(self, temp_config_dir):
        """Test deleting a template."""
        engine = PromptEngine(temp_config_dir)

        # Create a template to delete
        template = PromptTemplate(
            name="to_delete",
            description="Will be deleted",
            version="1.0",
            template="Delete me",
        )
        engine.save_template(template, "user", overwrite=True)

        # Delete it
        result = engine.delete_template("to_delete", "user")
        assert result is True

        # Verify it's gone
        loaded = engine.get_user_template("to_delete")
        assert loaded is None

    def test_cannot_delete_default(self, temp_config_dir):
        """Test that default template cannot be deleted."""
        engine = PromptEngine(temp_config_dir)

        result = engine.delete_template("default", "system")
        assert result is False

        # Verify it still exists
        loaded = engine.get_system_template("default")
        assert loaded is not None

    def test_language_names_fixed(self, temp_config_dir):
        """Test that LANGUAGE_NAMES is fixed to Russian only."""
        engine = PromptEngine(temp_config_dir)

        assert engine.LANGUAGE_NAMES == {"ru": "Russian"}

    def test_render_with_web_search(self, temp_config_dir):
        """Test rendering with web_search_enabled flag."""
        # Create a template that uses web_search_enabled
        engine = PromptEngine(temp_config_dir)

        template = PromptTemplate(
            name="with_search",
            description="Template with search",
            version="1.0",
            template="""{% if web_search_enabled %}Web search is ON{% else %}Web search is OFF{% endif %}""",
        )
        engine.save_template(template, "system", overwrite=True)

        # Render with web search enabled
        rendered_on = engine.render_system_prompt(
            template_name="with_search",
            field_names=[],
            web_search_enabled=True,
        )
        assert "Web search is ON" in rendered_on

        # Render with web search disabled
        rendered_off = engine.render_system_prompt(
            template_name="with_search",
            field_names=[],
            web_search_enabled=False,
        )
        assert "Web search is OFF" in rendered_off

    def test_reload(self, temp_config_dir):
        """Test reloading templates."""
        engine = PromptEngine(temp_config_dir)

        # Add a new template file
        new_template = {
            "name": "new_template",
            "description": "New template",
            "version": "1.0",
            "template": "New content",
        }
        with open(temp_config_dir / "prompts" / "system" / "new.yaml", "w", encoding="utf-8") as f:
            yaml.dump(new_template, f, allow_unicode=True)

        # Reload
        engine.reload()

        # Check new template is loaded
        assert "new_template" in engine.list_system_templates()

    def test_invalid_template_raises(self, temp_config_dir):
        """Test that invalid template name raises error."""
        engine = PromptEngine(temp_config_dir)

        with pytest.raises(ValueError, match="not found"):
            engine.render_system_prompt(template_name="nonexistent")

        with pytest.raises(ValueError, match="not found"):
            engine.render_user_prompt(template_name="nonexistent", product_name="Test")

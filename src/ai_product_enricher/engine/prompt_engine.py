"""Prompt Engine for dynamic prompt generation using Jinja2 templates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, BaseLoader, TemplateError

from .field_registry import FieldDefinition, FieldRegistry


@dataclass
class PromptVariable:
    """Definition of a template variable."""

    name: str
    description: str
    type: str
    required: bool = True
    default: Any = None


@dataclass
class PromptTemplate:
    """A prompt template loaded from YAML."""

    name: str
    description: str
    version: str
    template: str
    language: str = "ru"
    variables: list[PromptVariable] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptTemplate:
        """Create PromptTemplate from dictionary."""
        variables = []
        for var_data in data.get("variables", []):
            variables.append(
                PromptVariable(
                    name=var_data.get("name", ""),
                    description=var_data.get("description", ""),
                    type=var_data.get("type", "string"),
                    required=var_data.get("required", True),
                    default=var_data.get("default"),
                )
            )

        return cls(
            name=data.get("name", "unknown"),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            template=data.get("template", ""),
            language=data.get("language", "ru"),
            variables=variables,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "language": self.language,
            "template": self.template,
        }
        if self.variables:
            result["variables"] = [
                {
                    "name": v.name,
                    "description": v.description,
                    "type": v.type,
                    "required": v.required,
                    "default": v.default,
                }
                for v in self.variables
            ]
        return result


class PromptEngine:
    """Engine for rendering prompts from Jinja2 templates."""

    # Fixed language configuration - only Russian
    LANGUAGE_NAMES: dict[str, str] = {"ru": "Russian"}

    def __init__(self, config_dir: Path | str | None = None) -> None:
        """Initialize the prompt engine.

        Args:
            config_dir: Path to config directory. If None, uses default location.
        """
        if config_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)
        self.prompts_dir = self.config_dir / "prompts"

        # Initialize Jinja2 environment
        self._env = Environment(
            loader=BaseLoader(),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,
        )
        # Add custom filter for JSON serialization
        self._env.filters["tojson"] = lambda x: json.dumps(x, ensure_ascii=False)

        self._system_templates: dict[str, PromptTemplate] = {}
        self._user_templates: dict[str, PromptTemplate] = {}

        self._load_templates()

    def _load_templates(self) -> None:
        """Load all templates from YAML files."""
        self._system_templates = {}
        self._user_templates = {}

        # Load system templates
        system_dir = self.prompts_dir / "system"
        if system_dir.exists():
            for yaml_file in system_dir.glob("*.yaml"):
                self._load_template_file(yaml_file, self._system_templates)

        # Load user templates
        user_dir = self.prompts_dir / "user"
        if user_dir.exists():
            for yaml_file in user_dir.glob("*.yaml"):
                self._load_template_file(yaml_file, self._user_templates)

        # Create defaults if nothing loaded
        if not self._system_templates:
            self._create_default_system_template()
        if not self._user_templates:
            self._create_default_user_template()

    def _load_template_file(
        self,
        file_path: Path,
        target_dict: dict[str, PromptTemplate],
    ) -> None:
        """Load a single template from YAML file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    template = PromptTemplate.from_dict(data)
                    target_dict[template.name] = template
        except Exception as e:
            print(f"Error loading template from {file_path}: {e}")

    def _create_default_system_template(self) -> None:
        """Create a default system template in memory."""
        template = """Ты — эксперт по обогащению продуктовых данных.

## Язык ответа
Отвечай на русском языке ({{ language_name }}).

## Поля для извлечения
{% for field in fields %}
### {{ field.display_name }} (`{{ field.name }}`)
{{ field.description }}
Тип: {{ field.type }}
{% endfor %}

## Формат ответа
Верни результат в формате JSON:
```json
{
{% for field in fields %}
  "{{ field.name }}": <{{ field.type }}>{% if not loop.last %},{% endif %}

{% endfor %}
}
```
"""
        self._system_templates["default"] = PromptTemplate(
            name="default",
            description="Стандартный системный промпт (создан в памяти)",
            version="1.0",
            template=template,
        )

    def _create_default_user_template(self) -> None:
        """Create a default user template in memory."""
        template = """Обогати информацию о товаре:

**Название**: {{ product_name }}
{% if product_description %}
**Описание**: {{ product_description }}
{% endif %}

Извлеки поля: {{ fields_list | join(', ') }}

Верни результат в формате JSON.
"""
        self._user_templates["default"] = PromptTemplate(
            name="default",
            description="Стандартный пользовательский промпт (создан в памяти)",
            version="1.0",
            template=template,
        )

    def get_system_template(self, name: str = "default") -> PromptTemplate | None:
        """Get a system template by name."""
        return self._system_templates.get(name)

    def get_user_template(self, name: str = "default") -> PromptTemplate | None:
        """Get a user template by name."""
        return self._user_templates.get(name)

    def list_system_templates(self) -> list[str]:
        """List all available system template names."""
        return list(self._system_templates.keys())

    def list_user_templates(self) -> list[str]:
        """List all available user template names."""
        return list(self._user_templates.keys())

    def render_system_prompt(
        self,
        template_name: str = "default",
        field_names: list[str] | None = None,
        field_set_name: str = "default",
        field_registry: FieldRegistry | None = None,
        web_search_enabled: bool = False,
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """Render a system prompt with field definitions.

        Args:
            template_name: Name of the system template to use.
            field_names: List of field names to include. If None, uses all fields.
            field_set_name: Name of the field set to use.
            field_registry: FieldRegistry instance. If None, creates a new one.
            web_search_enabled: Whether web search is enabled.
            extra_context: Additional context variables for the template.

        Returns:
            Rendered system prompt string.
        """
        template_obj = self.get_system_template(template_name)
        if not template_obj:
            raise ValueError(f"System template '{template_name}' not found")

        # Get field definitions
        if field_registry is None:
            field_registry = FieldRegistry(self.config_dir)

        if field_names is None:
            field_names = field_registry.list_available_fields(field_set_name)

        fields = field_registry.get_fields_for_extraction(field_names, field_set_name)

        # Prepare context
        context: dict[str, Any] = {
            "fields": fields,
            "language_name": self.LANGUAGE_NAMES.get("ru", "Russian"),
            "web_search_enabled": web_search_enabled,
        }

        if extra_context:
            context.update(extra_context)

        # Render template
        try:
            jinja_template = self._env.from_string(template_obj.template)
            return jinja_template.render(**context)
        except TemplateError as e:
            raise ValueError(f"Error rendering template: {e}") from e

    def render_user_prompt(
        self,
        template_name: str = "default",
        product_name: str = "",
        product_description: str | None = None,
        field_names: list[str] | None = None,
        context_data: dict[str, Any] | None = None,
    ) -> str:
        """Render a user prompt for product enrichment.

        Args:
            template_name: Name of the user template to use.
            product_name: Name of the product.
            product_description: Optional product description.
            field_names: List of fields to extract.
            context_data: Additional context data.

        Returns:
            Rendered user prompt string.
        """
        template_obj = self.get_user_template(template_name)
        if not template_obj:
            raise ValueError(f"User template '{template_name}' not found")

        if field_names is None:
            field_names = []

        # Prepare context
        context: dict[str, Any] = {
            "product_name": product_name,
            "product_description": product_description,
            "fields_list": field_names,
            "context_data": context_data,
        }

        # Render template
        try:
            jinja_template = self._env.from_string(template_obj.template)
            return jinja_template.render(**context)
        except TemplateError as e:
            raise ValueError(f"Error rendering template: {e}") from e

    def preview_template(
        self,
        template_type: str,
        template_name: str = "default",
        field_registry: FieldRegistry | None = None,
    ) -> str:
        """Preview a template with sample data.

        Args:
            template_type: "system" or "user"
            template_name: Name of the template.
            field_registry: Optional FieldRegistry instance.

        Returns:
            Rendered preview string.
        """
        if template_type == "system":
            return self.render_system_prompt(
                template_name=template_name,
                field_names=["manufacturer", "trademark", "category", "description"],
                field_registry=field_registry,
                web_search_enabled=True,
            )
        elif template_type == "user":
            return self.render_user_prompt(
                template_name=template_name,
                product_name="Apple iPhone 15 Pro Max 256GB",
                product_description="Флагманский смартфон Apple",
                field_names=["manufacturer", "trademark", "category", "description"],
                context_data={"country_origin": "CN"},
            )
        else:
            raise ValueError(f"Unknown template type: {template_type}")

    def save_template(
        self,
        template: PromptTemplate,
        template_type: str,
        overwrite: bool = False,
    ) -> bool:
        """Save a template to YAML file.

        Args:
            template: The template to save.
            template_type: "system" or "user"
            overwrite: Whether to overwrite existing file.

        Returns:
            True if saved successfully, False otherwise.
        """
        if template_type == "system":
            target_dir = self.prompts_dir / "system"
        elif template_type == "user":
            target_dir = self.prompts_dir / "user"
        else:
            return False

        # Ensure directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / f"{template.name}.yaml"

        if file_path.exists() and not overwrite:
            return False

        try:
            data = template.to_dict()
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            # Update in-memory cache
            if template_type == "system":
                self._system_templates[template.name] = template
            else:
                self._user_templates[template.name] = template

            return True
        except Exception as e:
            print(f"Error saving template: {e}")
            return False

    def delete_template(self, template_name: str, template_type: str) -> bool:
        """Delete a template.

        Args:
            template_name: Name of the template to delete.
            template_type: "system" or "user"

        Returns:
            True if deleted successfully, False otherwise.
        """
        # Protect default templates
        if template_name == "default":
            return False

        if template_type == "system":
            target_dir = self.prompts_dir / "system"
            target_dict = self._system_templates
        elif template_type == "user":
            target_dir = self.prompts_dir / "user"
            target_dict = self._user_templates
        else:
            return False

        file_path = target_dir / f"{template_name}.yaml"

        try:
            if file_path.exists():
                file_path.unlink()

            if template_name in target_dict:
                del target_dict[template_name]

            return True
        except Exception as e:
            print(f"Error deleting template: {e}")
            return False

    def reload(self) -> None:
        """Reload all templates from disk."""
        self._load_templates()

"""Gradio WebUI for AI Product Enricher."""

from __future__ import annotations

import json
import time
from typing import Any

import gradio as gr

from ..engine import (
    ConfigurationManager,
    EnrichmentProfile,
    FieldDefinition,
    FieldRegistry,
    PromptEngine,
    PromptTemplate,
)


# Country codes for dropdown
COUNTRY_CHOICES = [
    ("Россия (RU)", "RU"),
    ("Китай (CN)", "CN"),
    ("США (US)", "US"),
    ("Южная Корея (KR)", "KR"),
    ("Япония (JP)", "JP"),
    ("Германия (DE)", "DE"),
    ("Тайвань (TW)", "TW"),
    ("Не указано", ""),
]


class EnricherWebUI:
    """Gradio WebUI for product enrichment testing and configuration."""

    def __init__(
        self,
        enricher_service: Any | None = None,
        config_dir: str | None = None,
    ) -> None:
        """Initialize the WebUI.

        Args:
            enricher_service: Optional ProductEnricherService instance for enrichment.
            config_dir: Optional path to config directory.
        """
        self.enricher = enricher_service
        self.field_registry = FieldRegistry(config_dir)
        self.prompt_engine = PromptEngine(config_dir)
        self.config_manager = ConfigurationManager(config_dir)

    def _get_available_fields(self) -> list[str]:
        """Get list of available field names."""
        return self.field_registry.list_available_fields("default")

    def _get_field_choices(self) -> list[tuple[str, str]]:
        """Get field choices for checkbox group."""
        field_set = self.field_registry.get_field_set("default")
        if not field_set:
            return []
        return [
            (f.display_name, f.name)
            for f in field_set.fields.values()
        ]

    def _get_default_fields(self) -> list[str]:
        """Get default enabled fields."""
        profile = self.config_manager.get_active_profile()
        return profile.fields.enabled

    # ============================================
    # Tab 1: Testing
    # ============================================

    def _enrich_product(
        self,
        profile_name: str,
        product_name: str,
        product_description: str,
        country_origin: str,
        selected_fields: list[str],
        use_web_search: bool,
    ) -> tuple[str, str, str, str]:
        """Enrich a product and return results.

        Returns:
            Tuple of (result_json, metadata_json, system_prompt, user_prompt)
        """
        start_time = time.time()

        # Validate input
        if not product_name.strip():
            return (
                json.dumps({"error": "Название товара обязательно"}, ensure_ascii=False, indent=2),
                "{}",
                "",
                "",
            )

        # Get profile
        profile = self.config_manager.get_profile(profile_name)
        if not profile:
            profile = self.config_manager.get_active_profile()

        # Use profile fields if none selected
        if not selected_fields:
            selected_fields = profile.fields.enabled

        # Generate prompts for preview
        try:
            system_prompt = self.prompt_engine.render_system_prompt(
                template_name=profile.prompts.system,
                field_names=selected_fields,
                web_search_enabled=use_web_search,
            )
            user_prompt = self.prompt_engine.render_user_prompt(
                template_name=profile.prompts.user,
                product_name=product_name,
                product_description=product_description if product_description else None,
                field_names=selected_fields,
                context_data={"country_origin": country_origin} if country_origin else None,
            )
        except Exception as e:
            system_prompt = f"Ошибка генерации промпта: {e}"
            user_prompt = ""

        # If no enricher service, return mock result
        if self.enricher is None:
            mock_result = {
                "status": "demo_mode",
                "message": "Enricher service не подключен. Запустите с --with-enricher",
                "product": {
                    "name": product_name,
                    "description": product_description,
                    "country_origin": country_origin,
                },
                "requested_fields": selected_fields,
                "prompts_generated": True,
            }
            metadata = {
                "demo_mode": True,
                "profile_used": profile_name,
                "fields_requested": len(selected_fields),
                "web_search_enabled": use_web_search,
                "processing_time_ms": int((time.time() - start_time) * 1000),
            }
            return (
                json.dumps(mock_result, ensure_ascii=False, indent=2),
                json.dumps(metadata, ensure_ascii=False, indent=2),
                system_prompt,
                user_prompt,
            )

        # Call actual enricher service
        try:
            from ..models import EnrichmentOptions, ProductInput

            product_input = ProductInput(
                name=product_name,
                description=product_description if product_description else None,
                country_origin=country_origin if country_origin else None,
            )

            options = EnrichmentOptions(
                include_web_search=use_web_search,
                language="ru",
                fields=selected_fields,
            )

            # Call enricher asynchronously
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.enricher.enrich_product(product_input, options)
                )
            finally:
                loop.close()

            result_json = json.dumps(
                result.enriched.model_dump() if hasattr(result, "enriched") else result,
                ensure_ascii=False,
                indent=2,
            )

            metadata = {
                "profile_used": profile_name,
                "model_used": getattr(result, "model_used", "unknown"),
                "llm_provider": getattr(result, "llm_provider", "unknown"),
                "tokens_used": getattr(result, "tokens_used", 0),
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "web_search_used": getattr(result, "web_search_used", False),
                "cached": getattr(result, "cached", False),
            }

            return (
                result_json,
                json.dumps(metadata, ensure_ascii=False, indent=2),
                system_prompt,
                user_prompt,
            )

        except Exception as e:
            error_result = {"error": str(e)}
            metadata = {
                "profile_used": profile_name,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "error": True,
            }
            return (
                json.dumps(error_result, ensure_ascii=False, indent=2),
                json.dumps(metadata, ensure_ascii=False, indent=2),
                system_prompt,
                user_prompt,
            )

    # ============================================
    # Tab 2: Field Configuration
    # ============================================

    def _get_fields_dataframe(self, field_set_name: str = "default") -> list[list[str]]:
        """Get fields as dataframe for display."""
        field_set = self.field_registry.get_field_set(field_set_name)
        if not field_set:
            return []

        rows = []
        for name, field_def in field_set.fields.items():
            rows.append([
                name,
                field_def.display_name,
                field_def.type,
                field_def.description[:100] + "..." if len(field_def.description) > 100 else field_def.description,
            ])
        return rows

    def _get_field_details(self, field_name: str) -> tuple[str, str, str, str, str, str]:
        """Get detailed field information for editing."""
        field_def = self.field_registry.get_field("default", field_name)
        if not field_def:
            return "", "", "", "", "", ""

        hints = "\n".join(field_def.extraction_hints)
        examples = ""
        for ex in field_def.examples:
            output_str = json.dumps(ex.output, ensure_ascii=False) if isinstance(ex.output, (dict, list)) else str(ex.output)
            examples += f"Input: {ex.input}\nOutput: {output_str}\n\n"

        return (
            field_def.name,
            field_def.display_name,
            field_def.type,
            field_def.description,
            hints,
            examples.strip(),
        )

    def _save_custom_field(
        self,
        name: str,
        display_name: str,
        field_type: str,
        description: str,
        hints: str,
        examples: str,
    ) -> str:
        """Save a custom field definition."""
        if not name or not display_name:
            return "Ошибка: имя и отображаемое имя обязательны"

        # Parse hints
        hint_list = [h.strip() for h in hints.split("\n") if h.strip()]

        # Parse examples (simplified format)
        example_list = []
        if examples.strip():
            # Try to parse examples in "Input: ...\nOutput: ..." format
            parts = examples.split("\n\n")
            for part in parts:
                lines = part.strip().split("\n")
                if len(lines) >= 2:
                    input_line = lines[0].replace("Input:", "").strip()
                    output_line = lines[1].replace("Output:", "").strip()
                    try:
                        output_val = json.loads(output_line)
                    except json.JSONDecodeError:
                        output_val = output_line
                    from ..engine.field_registry import FieldExample
                    example_list.append(FieldExample(input=input_line, output=output_val))

        field_def = FieldDefinition(
            name=name,
            display_name=display_name,
            type=field_type,
            description=description,
            extraction_hints=hint_list,
            examples=example_list,
        )

        self.field_registry.add_custom_field(field_def)
        if self.field_registry.save_custom_fields():
            return f"Поле '{name}' успешно сохранено"
        return "Ошибка сохранения поля"

    # ============================================
    # Tab 3: Prompt Editor
    # ============================================

    def _get_template_content(self, template_type: str, template_name: str) -> str:
        """Get template content for editing."""
        if template_type == "system":
            template = self.prompt_engine.get_system_template(template_name)
        else:
            template = self.prompt_engine.get_user_template(template_name)

        if template:
            return template.template
        return ""

    def _preview_template(self, template_type: str, template_name: str) -> str:
        """Preview a template with sample data."""
        try:
            return self.prompt_engine.preview_template(template_type, template_name, self.field_registry)
        except Exception as e:
            return f"Ошибка preview: {e}"

    def _save_template(
        self,
        template_type: str,
        template_name: str,
        template_content: str,
        description: str,
    ) -> str:
        """Save a template."""
        if not template_name or not template_content:
            return "Ошибка: имя и содержимое шаблона обязательны"

        template = PromptTemplate(
            name=template_name,
            description=description or f"Шаблон {template_name}",
            version="1.0",
            template=template_content,
        )

        if self.prompt_engine.save_template(template, template_type, overwrite=True):
            return f"Шаблон '{template_name}' успешно сохранен"
        return "Ошибка сохранения шаблона"

    # ============================================
    # Tab 4: Profiles
    # ============================================

    def _get_profile_settings(self, profile_name: str) -> tuple[str, str, str, str, float, int, bool, int, bool]:
        """Get profile settings for display."""
        profile = self.config_manager.get_profile(profile_name)
        if not profile:
            profile = self.config_manager.get_active_profile()

        return (
            profile.name,
            profile.description,
            profile.prompts.system,
            profile.prompts.user,
            profile.llm.temperature,
            profile.llm.max_tokens,
            profile.cache.enabled,
            profile.cache.ttl_seconds,
            profile.web_search.enabled,
        )

    def _save_profile(
        self,
        name: str,
        description: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        cache_enabled: bool,
        cache_ttl: int,
        web_search_enabled: bool,
        enabled_fields: list[str],
    ) -> str:
        """Save profile settings."""
        if not name:
            return "Ошибка: имя профиля обязательно"

        profile = self.config_manager.get_profile(name)
        if not profile:
            profile = self.config_manager.create_profile_from_current(name, description)

        profile.description = description
        profile.prompts.system = system_prompt
        profile.prompts.user = user_prompt
        profile.llm.temperature = temperature
        profile.llm.max_tokens = max_tokens
        profile.cache.enabled = cache_enabled
        profile.cache.ttl_seconds = cache_ttl
        profile.web_search.enabled = web_search_enabled
        if enabled_fields:
            profile.fields.enabled = enabled_fields

        if self.config_manager.save_profile(profile, overwrite=True):
            return f"Профиль '{name}' успешно сохранен"
        return "Ошибка сохранения профиля"

    def _create_new_profile(self, new_name: str, base_profile: str) -> str:
        """Create a new profile based on existing one."""
        if not new_name:
            return "Ошибка: имя нового профиля обязательно"

        if new_name in self.config_manager.list_profiles():
            return f"Ошибка: профиль '{new_name}' уже существует"

        self.config_manager.set_active_profile(base_profile)
        new_profile = self.config_manager.create_profile_from_current(
            new_name,
            f"Создан на основе профиля '{base_profile}'",
        )

        if self.config_manager.save_profile(new_profile):
            return f"Профиль '{new_name}' успешно создан"
        return "Ошибка создания профиля"

    def _delete_profile(self, profile_name: str) -> str:
        """Delete a profile."""
        if profile_name == "default":
            return "Ошибка: нельзя удалить профиль по умолчанию"

        if self.config_manager.delete_profile(profile_name):
            return f"Профиль '{profile_name}' успешно удален"
        return "Ошибка удаления профиля"

    # ============================================
    # Build UI
    # ============================================

    def create_app(self) -> gr.Blocks:
        """Create the Gradio application."""
        with gr.Blocks(
            title="AI Product Enricher",
            theme=gr.themes.Soft(),
        ) as app:
            gr.Markdown("# AI Product Enricher - WebUI")
            gr.Markdown("Конфигурируемая платформа для обогащения продуктовых данных")

            with gr.Tabs():
                # ============================================
                # Tab 1: Testing
                # ============================================
                with gr.TabItem("Тестирование"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            profile_dropdown = gr.Dropdown(
                                choices=self.config_manager.list_profiles(),
                                value="default",
                                label="Профиль",
                            )
                            product_name_input = gr.Textbox(
                                label="Название товара",
                                placeholder="Apple iPhone 15 Pro Max 256GB",
                                lines=1,
                            )
                            product_desc_input = gr.Textbox(
                                label="Описание (опционально)",
                                placeholder="Дополнительное описание товара...",
                                lines=2,
                            )
                            country_dropdown = gr.Dropdown(
                                choices=COUNTRY_CHOICES,
                                value="",
                                label="Страна происхождения",
                            )
                            fields_checkbox = gr.CheckboxGroup(
                                choices=self._get_field_choices(),
                                value=self._get_default_fields(),
                                label="Поля для извлечения",
                            )
                            web_search_checkbox = gr.Checkbox(
                                value=True,
                                label="Использовать веб-поиск",
                            )
                            enrich_button = gr.Button(
                                "Обогатить",
                                variant="primary",
                            )

                        with gr.Column(scale=2):
                            result_json = gr.JSON(label="Результат обогащения")
                            metadata_json = gr.JSON(label="Метаданные")

                    with gr.Accordion("Промпты (preview)", open=False):
                        with gr.Row():
                            system_prompt_preview = gr.Textbox(
                                label="Системный промпт",
                                lines=15,
                                interactive=False,
                            )
                            user_prompt_preview = gr.Textbox(
                                label="Пользовательский промпт",
                                lines=15,
                                interactive=False,
                            )

                    enrich_button.click(
                        fn=self._enrich_product,
                        inputs=[
                            profile_dropdown,
                            product_name_input,
                            product_desc_input,
                            country_dropdown,
                            fields_checkbox,
                            web_search_checkbox,
                        ],
                        outputs=[
                            result_json,
                            metadata_json,
                            system_prompt_preview,
                            user_prompt_preview,
                        ],
                    )

                # ============================================
                # Tab 2: Field Configuration
                # ============================================
                with gr.TabItem("Настройка полей"):
                    with gr.Row():
                        field_set_dropdown = gr.Dropdown(
                            choices=list(self.field_registry.get_all_field_sets().keys()),
                            value="default",
                            label="Набор полей",
                        )
                        refresh_fields_btn = gr.Button("Обновить", scale=0)

                    fields_table = gr.Dataframe(
                        headers=["Имя", "Отображаемое имя", "Тип", "Описание"],
                        value=self._get_fields_dataframe(),
                        interactive=False,
                        wrap=True,
                    )

                    gr.Markdown("### Редактор поля")
                    with gr.Row():
                        with gr.Column():
                            field_name_input = gr.Textbox(label="Имя поля (field name)")
                            field_display_name = gr.Textbox(label="Отображаемое имя")
                            field_type_dropdown = gr.Dropdown(
                                choices=["string", "array", "object"],
                                value="string",
                                label="Тип данных",
                            )
                        with gr.Column():
                            field_description = gr.Textbox(
                                label="Описание",
                                lines=4,
                            )

                    with gr.Row():
                        with gr.Column():
                            field_hints = gr.Textbox(
                                label="Подсказки для извлечения (по одной на строку)",
                                lines=4,
                            )
                        with gr.Column():
                            field_examples = gr.Textbox(
                                label="Примеры (Input: ... / Output: ...)",
                                lines=4,
                            )

                    with gr.Row():
                        load_field_btn = gr.Button("Загрузить поле")
                        save_field_btn = gr.Button("Сохранить поле", variant="primary")
                        field_status = gr.Textbox(label="Статус", interactive=False)

                    def load_field_from_table(evt: gr.SelectData):
                        if evt.index and len(evt.index) >= 1:
                            row_idx = evt.index[0]
                            fields_data = self._get_fields_dataframe()
                            if row_idx < len(fields_data):
                                field_name = fields_data[row_idx][0]
                                return self._get_field_details(field_name)
                        return "", "", "", "", "", ""

                    fields_table.select(
                        fn=load_field_from_table,
                        outputs=[
                            field_name_input,
                            field_display_name,
                            field_type_dropdown,
                            field_description,
                            field_hints,
                            field_examples,
                        ],
                    )

                    save_field_btn.click(
                        fn=self._save_custom_field,
                        inputs=[
                            field_name_input,
                            field_display_name,
                            field_type_dropdown,
                            field_description,
                            field_hints,
                            field_examples,
                        ],
                        outputs=[field_status],
                    )

                    def refresh_fields(field_set_name):
                        self.field_registry.reload()
                        return self._get_fields_dataframe(field_set_name)

                    refresh_fields_btn.click(
                        fn=refresh_fields,
                        inputs=[field_set_dropdown],
                        outputs=[fields_table],
                    )

                # ============================================
                # Tab 3: Prompt Editor
                # ============================================
                with gr.TabItem("Редактор промптов"):
                    with gr.Row():
                        template_type_radio = gr.Radio(
                            choices=["system", "user"],
                            value="system",
                            label="Тип шаблона",
                        )
                        template_dropdown = gr.Dropdown(
                            choices=self.prompt_engine.list_system_templates(),
                            value="default",
                            label="Шаблон",
                        )

                    template_editor = gr.Code(
                        label="Шаблон (Jinja2)",
                        language="jinja2",
                        lines=20,
                    )

                    template_description = gr.Textbox(
                        label="Описание шаблона",
                        lines=1,
                    )

                    with gr.Row():
                        load_template_btn = gr.Button("Загрузить")
                        preview_template_btn = gr.Button("Preview")
                        save_template_btn = gr.Button("Сохранить", variant="primary")
                        template_status = gr.Textbox(label="Статус", interactive=False)

                    template_preview = gr.Textbox(
                        label="Preview результат",
                        lines=15,
                        interactive=False,
                    )

                    def update_template_choices(template_type):
                        if template_type == "system":
                            choices = self.prompt_engine.list_system_templates()
                        else:
                            choices = self.prompt_engine.list_user_templates()
                        return gr.update(choices=choices, value=choices[0] if choices else "default")

                    template_type_radio.change(
                        fn=update_template_choices,
                        inputs=[template_type_radio],
                        outputs=[template_dropdown],
                    )

                    load_template_btn.click(
                        fn=self._get_template_content,
                        inputs=[template_type_radio, template_dropdown],
                        outputs=[template_editor],
                    )

                    preview_template_btn.click(
                        fn=self._preview_template,
                        inputs=[template_type_radio, template_dropdown],
                        outputs=[template_preview],
                    )

                    save_template_btn.click(
                        fn=self._save_template,
                        inputs=[
                            template_type_radio,
                            template_dropdown,
                            template_editor,
                            template_description,
                        ],
                        outputs=[template_status],
                    )

                # ============================================
                # Tab 4: Profiles
                # ============================================
                with gr.TabItem("Профили"):
                    with gr.Row():
                        profiles_dropdown = gr.Dropdown(
                            choices=self.config_manager.list_profiles(),
                            value="default",
                            label="Профиль",
                        )
                        refresh_profiles_btn = gr.Button("Обновить", scale=0)

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Основные настройки")
                            profile_name_input = gr.Textbox(label="Имя профиля")
                            profile_description = gr.Textbox(label="Описание", lines=2)

                            gr.Markdown("### Промпты")
                            profile_system_prompt = gr.Dropdown(
                                choices=self.prompt_engine.list_system_templates(),
                                label="Системный промпт",
                            )
                            profile_user_prompt = gr.Dropdown(
                                choices=self.prompt_engine.list_user_templates(),
                                label="Пользовательский промпт",
                            )

                        with gr.Column():
                            gr.Markdown("### LLM параметры")
                            profile_temperature = gr.Slider(
                                minimum=0,
                                maximum=1,
                                step=0.1,
                                value=0.3,
                                label="Temperature",
                            )
                            profile_max_tokens = gr.Number(
                                value=4000,
                                label="Max Tokens",
                            )

                            gr.Markdown("### Кэширование")
                            profile_cache_enabled = gr.Checkbox(
                                value=True,
                                label="Кэширование включено",
                            )
                            profile_cache_ttl = gr.Number(
                                value=3600,
                                label="TTL (секунды)",
                            )

                            gr.Markdown("### Веб-поиск")
                            profile_web_search = gr.Checkbox(
                                value=True,
                                label="Веб-поиск включен",
                            )

                    gr.Markdown("### Поля")
                    profile_fields = gr.CheckboxGroup(
                        choices=self._get_field_choices(),
                        value=self._get_default_fields(),
                        label="Включенные поля",
                    )

                    with gr.Row():
                        load_profile_btn = gr.Button("Загрузить профиль")
                        save_profile_btn = gr.Button("Сохранить профиль", variant="primary")
                        profile_status = gr.Textbox(label="Статус", interactive=False)

                    gr.Markdown("---")
                    gr.Markdown("### Создание нового профиля")
                    with gr.Row():
                        new_profile_name = gr.Textbox(label="Имя нового профиля")
                        base_profile_dropdown = gr.Dropdown(
                            choices=self.config_manager.list_profiles(),
                            value="default",
                            label="На основе профиля",
                        )
                        create_profile_btn = gr.Button("Создать", variant="secondary")
                        create_status = gr.Textbox(label="Статус", interactive=False)

                    gr.Markdown("### Удаление профиля")
                    with gr.Row():
                        delete_profile_dropdown = gr.Dropdown(
                            choices=[p for p in self.config_manager.list_profiles() if p != "default"],
                            label="Профиль для удаления",
                        )
                        delete_profile_btn = gr.Button("Удалить", variant="stop")
                        delete_status = gr.Textbox(label="Статус", interactive=False)

                    def load_profile_settings(profile_name):
                        settings = self._get_profile_settings(profile_name)
                        profile = self.config_manager.get_profile(profile_name)
                        fields = profile.fields.enabled if profile else []
                        return settings + (fields,)

                    load_profile_btn.click(
                        fn=load_profile_settings,
                        inputs=[profiles_dropdown],
                        outputs=[
                            profile_name_input,
                            profile_description,
                            profile_system_prompt,
                            profile_user_prompt,
                            profile_temperature,
                            profile_max_tokens,
                            profile_cache_enabled,
                            profile_cache_ttl,
                            profile_web_search,
                            profile_fields,
                        ],
                    )

                    save_profile_btn.click(
                        fn=self._save_profile,
                        inputs=[
                            profile_name_input,
                            profile_description,
                            profile_system_prompt,
                            profile_user_prompt,
                            profile_temperature,
                            profile_max_tokens,
                            profile_cache_enabled,
                            profile_cache_ttl,
                            profile_web_search,
                            profile_fields,
                        ],
                        outputs=[profile_status],
                    )

                    create_profile_btn.click(
                        fn=self._create_new_profile,
                        inputs=[new_profile_name, base_profile_dropdown],
                        outputs=[create_status],
                    )

                    delete_profile_btn.click(
                        fn=self._delete_profile,
                        inputs=[delete_profile_dropdown],
                        outputs=[delete_status],
                    )

                    def refresh_profiles():
                        self.config_manager.reload()
                        profiles = self.config_manager.list_profiles()
                        deletable = [p for p in profiles if p != "default"]
                        return (
                            gr.update(choices=profiles),
                            gr.update(choices=profiles),
                            gr.update(choices=deletable),
                        )

                    refresh_profiles_btn.click(
                        fn=refresh_profiles,
                        outputs=[profiles_dropdown, base_profile_dropdown, delete_profile_dropdown],
                    )

        return app


def create_app(
    enricher_service: Any | None = None,
    config_dir: str | None = None,
) -> gr.Blocks:
    """Create the Gradio WebUI application.

    Args:
        enricher_service: Optional ProductEnricherService instance.
        config_dir: Optional path to config directory.

    Returns:
        Gradio Blocks application.
    """
    webui = EnricherWebUI(enricher_service, config_dir)
    return webui.create_app()

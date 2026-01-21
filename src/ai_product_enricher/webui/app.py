"""Gradio WebUI for AI Product Enricher."""

from __future__ import annotations

import json
import time
from typing import Any

import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes

from ..engine import (
    ConfigurationManager,
    EnrichmentProfile,
    FieldDefinition,
    FieldRegistry,
    PromptEngine,
    PromptTemplate,
)


# ============================================
# Custom Theme: Креативный AI стиль
# ============================================
class ProductEnricherTheme(Base):
    """Custom theme for AI Product Enricher with violet/purple accent colors."""

    def __init__(
        self,
        *,
        primary_hue: colors.Color = colors.violet,
        secondary_hue: colors.Color = colors.purple,
        neutral_hue: colors.Color = colors.slate,
        font: fonts.Font | str = fonts.GoogleFont("Inter"),
        font_mono: fonts.Font | str = fonts.GoogleFont("JetBrains Mono"),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            font=font,
            font_mono=font_mono,
        )

        # Apply custom styling
        super().set(
            # Body
            body_background_fill="linear-gradient(135deg, *neutral_50 0%, *neutral_100 100%)",
            body_background_fill_dark="linear-gradient(135deg, *neutral_900 0%, *neutral_950 100%)",

            # Buttons
            button_primary_background_fill="linear-gradient(135deg, *primary_500, *secondary_500)",
            button_primary_background_fill_hover="linear-gradient(135deg, *primary_600, *secondary_600)",
            button_primary_text_color="white",
            button_primary_border_color="transparent",
            button_primary_shadow="0 4px 14px 0 rgba(139, 92, 246, 0.39)",
            button_primary_shadow_hover="0 6px 20px 0 rgba(139, 92, 246, 0.5)",
            button_secondary_background_fill="*neutral_100",
            button_secondary_background_fill_hover="*neutral_200",
            button_secondary_border_color="*neutral_300",
            button_border_width="1px",
            button_large_radius="*radius_lg",
            button_small_radius="*radius_md",

            # Inputs
            input_background_fill="white",
            input_background_fill_dark="*neutral_800",
            input_border_color="*neutral_200",
            input_border_color_focus="*primary_400",
            input_border_width="1.5px",
            input_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            input_shadow_focus="0 0 0 3px rgba(139, 92, 246, 0.15)",
            input_radius="*radius_md",

            # Blocks
            block_background_fill="white",
            block_background_fill_dark="*neutral_850",
            block_border_width="1px",
            block_border_color="*neutral_200",
            block_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
            block_title_text_color="*primary_700",
            block_title_text_weight="600",
            block_label_text_color="*neutral_700",
            block_radius="*radius_lg",
            block_padding="*spacing_lg",

            # Sliders
            slider_color="*primary_500",

            # Checkboxes
            checkbox_background_color_selected="*primary_500",
            checkbox_border_color_selected="*primary_600",

            # Tables
            table_border_color="*neutral_200",
            table_even_background_fill="*neutral_50",
            table_odd_background_fill="white",

            # Spacing
            layout_gap="*spacing_lg",
            section_header_text_weight="600",
        )


# ============================================
# Custom CSS
# ============================================
CUSTOM_CSS = """
/* Градиентный заголовок */
.main-header {
    background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 50%, #7C3AED 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700;
    font-size: 2.5rem !important;
    margin-bottom: 0.5rem !important;
    text-align: center;
}

.sub-header {
    color: #64748B;
    text-align: center;
    font-size: 1.1rem;
    margin-bottom: 1.5rem !important;
}

/* Стилизация вкладок */
.tabs > .tab-nav > button {
    font-weight: 500;
    padding: 12px 24px !important;
    border-radius: 8px 8px 0 0;
    transition: all 0.2s ease;
}

.tabs > .tab-nav > button.selected {
    background: linear-gradient(135deg, #8B5CF6, #A855F7) !important;
    color: white !important;
    border-bottom: none !important;
}

.tabs > .tab-nav > button:hover:not(.selected) {
    background: rgba(139, 92, 246, 0.1);
}

/* Hover-эффекты на кнопках */
.primary-btn {
    transition: all 0.3s ease !important;
}

.primary-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px 0 rgba(139, 92, 246, 0.45) !important;
}

/* Focus-эффекты на inputs */
input:focus, textarea:focus {
    border-color: #8B5CF6 !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
}

/* JSON-блоки с акцентной границей */
.json-output {
    border-left: 4px solid #8B5CF6 !important;
    background: linear-gradient(90deg, rgba(139, 92, 246, 0.05) 0%, transparent 100%) !important;
}

/* Секции с заголовками */
.section-header {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    color: #7C3AED !important;
    border-bottom: 2px solid #E2E8F0;
    padding-bottom: 8px;
    margin-bottom: 16px !important;
}

/* Группы с визуальным разделением */
.input-group {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.03) 0%, rgba(168, 85, 247, 0.06) 100%) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 2px 12px rgba(139, 92, 246, 0.08) !important;
    border: 1px solid rgba(139, 92, 246, 0.15) !important;
}

.output-group {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.02) 0%, rgba(168, 85, 247, 0.05) 100%) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    border: 1px solid rgba(139, 92, 246, 0.12) !important;
}

/* Блоки Gradio внутри групп */
.input-group .block,
.output-group .block,
.profile-card .block {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* Формы внутри групп */
.input-group .form,
.output-group .form,
.profile-card .form {
    background: transparent !important;
}

/* Поля ввода */
.input-group input,
.input-group textarea,
.output-group input,
.output-group textarea,
.profile-card input,
.profile-card textarea {
    background: rgba(255, 255, 255, 0.7) !important;
    border: 1px solid rgba(139, 92, 246, 0.2) !important;
}

.input-group input:focus,
.input-group textarea:focus,
.output-group input:focus,
.output-group textarea:focus,
.profile-card input:focus,
.profile-card textarea:focus {
    background: rgba(255, 255, 255, 0.9) !important;
    border-color: #8B5CF6 !important;
}

/* Статусные сообщения */
.status-success {
    color: #10B981 !important;
    background: rgba(16, 185, 129, 0.1) !important;
    border: 1px solid #10B981 !important;
    border-radius: 8px;
    padding: 8px 12px;
}

.status-error {
    color: #EF4444 !important;
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid #EF4444 !important;
    border-radius: 8px;
    padding: 8px 12px;
}

/* Accordion стилизация */
.accordion {
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    overflow: hidden;
}

.accordion > .label-wrap {
    background: linear-gradient(90deg, rgba(139, 92, 246, 0.05) 0%, transparent 100%);
    padding: 16px !important;
}

/* Таблица с улучшенным видом */
.dataframe {
    border-radius: 8px !important;
    overflow: hidden;
}

.dataframe th {
    background: linear-gradient(135deg, #8B5CF6, #A855F7) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px !important;
}

.dataframe td {
    padding: 10px 12px !important;
}

.dataframe tr:hover {
    background: rgba(139, 92, 246, 0.08) !important;
}

/* Код редактор */
.code-editor {
    border: 2px solid #E2E8F0 !important;
    border-radius: 12px !important;
}

.code-editor:focus-within {
    border-color: #8B5CF6 !important;
}

/* Мобильная адаптивность */
@media (max-width: 768px) {
    .main-header {
        font-size: 1.8rem !important;
    }

    .tabs > .tab-nav > button {
        padding: 8px 16px !important;
        font-size: 0.9rem;
    }

    .input-group, .output-group {
        padding: 12px;
    }
}

/* Иконки в кнопках */
.icon-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

/* Разделитель секций */
.section-divider {
    border-top: 2px solid #E2E8F0;
    margin: 24px 0;
    position: relative;
}

.section-divider::after {
    content: '';
    position: absolute;
    left: 0;
    top: -2px;
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, #8B5CF6, #A855F7);
}

/* Профили карточки */
.profile-card {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.04) 0%, rgba(168, 85, 247, 0.07) 100%) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    border: 1px solid rgba(139, 92, 246, 0.15) !important;
    transition: all 0.2s ease !important;
}

.profile-card:hover {
    border-color: rgba(139, 92, 246, 0.4) !important;
    box-shadow: 0 4px 16px rgba(139, 92, 246, 0.2) !important;
}

/* Колонки Gradio */
.column {
    background: transparent !important;
}

/* JSON блоки */
.json-output {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.02) 0%, rgba(255, 255, 255, 0.5) 100%) !important;
}

/* Глобальные блоки */
.block.svelte-1plpy97 {
    background: transparent !important;
}

/* Подсказки */
.hint-text {
    color: #94A3B8;
    font-size: 0.85rem;
    font-style: italic;
}

/* Цвет текста в полях ввода - светлый для читаемости на тёмном фоне */
input, textarea, .svelte-1hguek3 {
    color: #E2E8F0 !important;
}

input::placeholder, textarea::placeholder {
    color: #94A3B8 !important;
}

/* Disabled textarea (для Preview) */
textarea:disabled, textarea[disabled] {
    color: #1E293B !important;
    background: rgba(255, 255, 255, 0.9) !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #1E293B !important;
}

/* Стили чекбоксов */
.svelte-yb2gcx input[type="checkbox"] {
    appearance: none;
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    border: 2px solid #CBD5E1;
    border-radius: 4px;
    background: white;
    cursor: pointer;
    position: relative;
    transition: all 0.2s ease;
}

.svelte-yb2gcx input[type="checkbox"]:checked {
    background: #E2E8F0;
    border-color: #94A3B8;
}

.svelte-yb2gcx input[type="checkbox"]:checked::after {
    content: '✓';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #1E293B;
    font-size: 12px;
    font-weight: bold;
}

.svelte-yb2gcx input[type="checkbox"]:hover {
    border-color: #8B5CF6;
}

.svelte-yb2gcx label.selected {
    background: rgba(139, 92, 246, 0.1);
    border-radius: 6px;
    padding: 4px 8px;
    margin: 2px 0;
}

/* Общие стили для CheckboxGroup */
.wrap.svelte-yb2gcx {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.svelte-yb2gcx label {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    color: #E2E8F0;
}

/* Текст span в label checkbox */
.svelte-yb2gcx span.ml-2,
.svelte-yb2gcx label span {
    color: #E2E8F0 !important;
}

.svelte-yb2gcx label:hover {
    background: rgba(139, 92, 246, 0.08);
}

/* Стили для Dropdown - тёмный стиль */
input[role="listbox"],
.svelte-1xfsv4t,
.border-none.svelte-1xfsv4t {
    color: #E2E8F0 !important;
    background: transparent !important;
}

/* Выпадающий список опций */
[data-testid="dropdown-options"],
.dropdown-options,
ul[role="listbox"] {
    background: white !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

/* Опции в dropdown */
[data-testid="dropdown-options"] li,
ul[role="listbox"] li,
.dropdown-options li {
    color: #1E293B !important;
    padding: 8px 12px !important;
}

[data-testid="dropdown-options"] li:hover,
ul[role="listbox"] li:hover,
.dropdown-options li:hover {
    background: rgba(139, 92, 246, 0.1) !important;
}

[data-testid="dropdown-options"] li[aria-selected="true"],
ul[role="listbox"] li[aria-selected="true"],
.dropdown-options li.selected {
    background: rgba(139, 92, 246, 0.15) !important;
    font-weight: 500;
}

/* Стрелка dropdown - светлая */
.dropdown-arrow,
.icon-wrap svg {
    fill: #94A3B8 !important;
}

.icon-wrap svg path {
    fill: #94A3B8 !important;
}

/* Label в dropdown container */
.svelte-1xfsv4t.container span[data-testid="block-info"],
.svelte-1xfsv4t span.svelte-1gfkn6j {
    color: #94A3B8 !important;
}

/* Secondary wrap для dropdown - тёмный стиль */
.secondary-wrap.svelte-1xfsv4t,
.svelte-1xfsv4t.container {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
}

.secondary-wrap.svelte-1xfsv4t:focus-within {
    border-color: #8B5CF6 !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
}
"""


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
                "model_used": result.metadata.model_used,
                "llm_provider": result.metadata.llm_provider,
                "tokens_used": result.metadata.tokens_used,
                "processing_time_ms": result.metadata.processing_time_ms,
                "web_search_used": result.metadata.web_search_used,
                "cached": result.metadata.cached,
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
        field_def = self.field_registry.get_field(field_name, "default")
        if not field_def:
            return "", "", "", "", "", ""

        # Конвертируем hints в строки (могут быть словари)
        hints_list = []
        for hint in field_def.extraction_hints:
            if isinstance(hint, dict):
                hints_list.append(json.dumps(hint, ensure_ascii=False))
            else:
                hints_list.append(str(hint))
        hints = "\n".join(hints_list)

        # Формируем примеры
        examples = ""
        for ex in field_def.examples:
            # Конвертируем input в строку если это словарь
            input_str = json.dumps(ex.input, ensure_ascii=False) if isinstance(ex.input, (dict, list)) else str(ex.input)
            output_str = json.dumps(ex.output, ensure_ascii=False) if isinstance(ex.output, (dict, list)) else str(ex.output)
            examples += f"Input: {input_str}\nOutput: {output_str}\n\n"

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
        # Note: In Gradio 6.0+, theme and css should be passed to launch()
        # We store them as attributes for use in launch()
        theme = ProductEnricherTheme()

        with gr.Blocks(
            title="AI Product Enricher",
        ) as app:
            # Store theme and css for launch()
            app._custom_theme = theme
            app._custom_css = CUSTOM_CSS
            # Заголовок с градиентом
            gr.Markdown(
                "# AI Product Enricher",
                elem_classes=["main-header"],
            )
            gr.Markdown(
                "Конфигурируемая платформа для обогащения продуктовых данных с мульти-LLM архитектурой",
                elem_classes=["sub-header"],
            )

            with gr.Tabs(elem_classes=["tabs"]):
                # ============================================
                # Tab 1: Testing
                # ============================================
                with gr.TabItem("🧪 Тестирование", id="testing-tab"):
                    with gr.Row(equal_height=False):
                        # Левая колонка - ввод данных
                        with gr.Column(scale=1, elem_classes=["input-group"]):
                            gr.Markdown("### 📝 Данные товара", elem_classes=["section-header"])

                            profile_dropdown = gr.Dropdown(
                                choices=self.config_manager.list_profiles(),
                                value="default",
                                label="Профиль конфигурации",
                                info="Выберите профиль с предустановленными настройками",
                            )

                            product_name_input = gr.Textbox(
                                label="Название товара",
                                placeholder="Например: Apple iPhone 15 Pro Max 256GB Black Titanium",
                                lines=1,
                                info="Полное наименование из прайс-листа или госзакупок",
                            )

                            product_desc_input = gr.Textbox(
                                label="Описание (опционально)",
                                placeholder="Дополнительные характеристики или описание товара...",
                                lines=2,
                            )

                            country_dropdown = gr.Dropdown(
                                choices=COUNTRY_CHOICES,
                                value="",
                                label="🌍 Страна происхождения",
                                info="Определяет выбор LLM: RU → GigaChat, остальные → GLM-4.7",
                            )

                            gr.Markdown("### 🎯 Настройки обогащения", elem_classes=["section-header"])

                            fields_checkbox = gr.CheckboxGroup(
                                choices=self._get_field_choices(),
                                value=self._get_default_fields(),
                                label="Поля для извлечения",
                            )

                            web_search_checkbox = gr.Checkbox(
                                value=True,
                                label="🔍 Использовать веб-поиск",
                                info="Позволяет LLM искать актуальную информацию",
                            )

                            enrich_button = gr.Button(
                                "🚀 Обогатить товар",
                                variant="primary",
                                size="lg",
                                elem_classes=["primary-btn"],
                            )

                        # Правая колонка - результаты
                        with gr.Column(scale=2, elem_classes=["output-group"]):
                            gr.Markdown("### 📊 Результаты", elem_classes=["section-header"])

                            result_json = gr.JSON(
                                label="Обогащённые данные",
                                elem_classes=["json-output"],
                            )

                            metadata_json = gr.JSON(
                                label="Метаданные запроса",
                                elem_classes=["json-output"],
                            )

                    with gr.Accordion("👁️ Промпты (preview)", open=False, elem_classes=["accordion"]):
                        with gr.Row():
                            system_prompt_preview = gr.Textbox(
                                label="📋 Системный промпт",
                                lines=15,
                                interactive=False,
                            )
                            user_prompt_preview = gr.Textbox(
                                label="📋 Пользовательский промпт",
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
                with gr.TabItem("⚙️ Настройка полей", id="fields-tab"):
                    gr.Markdown("### 📋 Доступные поля", elem_classes=["section-header"])

                    with gr.Group(elem_classes=["input-group"]):
                        with gr.Row():
                            field_set_dropdown = gr.Dropdown(
                                choices=list(self.field_registry.get_all_field_sets().keys()),
                                value="default",
                                label="Набор полей",
                                scale=4,
                            )
                            refresh_fields_btn = gr.Button(
                                "🔄 Обновить",
                                scale=1,
                                variant="secondary",
                            )

                        fields_table = gr.Dataframe(
                            headers=["Имя", "Отображаемое имя", "Тип", "Описание"],
                            value=self._get_fields_dataframe(),
                            interactive=False,
                            wrap=True,
                            elem_classes=["dataframe"],
                        )
                        gr.Markdown(
                            "*Кликните на строку таблицы, чтобы загрузить поле в редактор*",
                            elem_classes=["hint-text"],
                        )

                    gr.Markdown("### ✏️ Редактор поля", elem_classes=["section-header"])

                    with gr.Group(elem_classes=["input-group"]):
                        # Dropdown для выбора поля
                        with gr.Row():
                            field_selector = gr.Dropdown(
                                choices=self._get_available_fields(),
                                label="Выберите поле для редактирования",
                                scale=4,
                            )
                            load_selected_field_btn = gr.Button(
                                "📥 Загрузить",
                                scale=1,
                                variant="secondary",
                            )

                        with gr.Row():
                            with gr.Column():
                                field_name_input = gr.Textbox(
                                    label="Имя поля (field name)",
                                    placeholder="например: manufacturer",
                                    info="Уникальный идентификатор поля (латиница, без пробелов)",
                                )
                                field_display_name = gr.Textbox(
                                    label="Отображаемое имя",
                                    placeholder="например: Производитель",
                                )
                                field_type_dropdown = gr.Dropdown(
                                    choices=["string", "array", "object"],
                                    value="string",
                                    label="Тип данных",
                                    info="string — текст, array — список, object — структура",
                                )
                            with gr.Column():
                                field_description = gr.Textbox(
                                    label="Описание",
                                    lines=5,
                                    placeholder="Подробное описание поля для LLM...",
                                )

                        with gr.Row():
                            with gr.Column():
                                field_hints = gr.Textbox(
                                    label="💡 Подсказки для извлечения",
                                    lines=4,
                                    placeholder="По одной подсказке на строку...\nНапример:\n- Ищи в начале названия\n- Проверь официальный сайт",
                                )
                            with gr.Column():
                                field_examples = gr.Textbox(
                                    label="📚 Примеры",
                                    lines=4,
                                    placeholder="Input: iPhone 15 Pro Max\nOutput: Apple\n\nInput: Galaxy S24 Ultra\nOutput: Samsung",
                                )

                        with gr.Row():
                            save_field_btn = gr.Button(
                                "💾 Сохранить поле",
                                variant="primary",
                                elem_classes=["primary-btn"],
                            )

                        field_status = gr.Textbox(
                            label="Статус",
                            interactive=False,
                            elem_id="field-status",
                        )

                    def load_field_from_table(evt: gr.SelectData):
                        # Отладка: выводим все атрибуты события
                        print(f"DEBUG select event: index={evt.index}, value={evt.value}, row_value={evt.row_value}")

                        # В Gradio 6.x row_value содержит данные всей строки
                        if evt.row_value and len(evt.row_value) > 0:
                            field_name = evt.row_value[0]  # Первый столбец - имя поля
                            print(f"DEBUG: Loading field '{field_name}'")
                            result = self._get_field_details(field_name)
                            print(f"DEBUG: Field details result: {result}")
                            return result
                        print("DEBUG: row_value is empty or None")
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

                    # Обработчик для Dropdown выбора поля
                    def load_field_from_dropdown(field_name):
                        if field_name:
                            return self._get_field_details(field_name)
                        return "", "", "", "", "", ""

                    # Загрузка при клике на кнопку
                    load_selected_field_btn.click(
                        fn=load_field_from_dropdown,
                        inputs=[field_selector],
                        outputs=[
                            field_name_input,
                            field_display_name,
                            field_type_dropdown,
                            field_description,
                            field_hints,
                            field_examples,
                        ],
                    )

                    # Автозагрузка при выборе поля в dropdown
                    field_selector.change(
                        fn=load_field_from_dropdown,
                        inputs=[field_selector],
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
                with gr.TabItem("📝 Редактор промптов", id="prompts-tab"):
                    gr.Markdown("### 🎨 Шаблоны промптов", elem_classes=["section-header"])
                    gr.Markdown(
                        "Редактируйте Jinja2-шаблоны для системных и пользовательских промптов",
                        elem_classes=["hint-text"],
                    )

                    with gr.Group(elem_classes=["input-group"]):
                        with gr.Row():
                            template_type_radio = gr.Radio(
                                choices=["system", "user"],
                                value="system",
                                label="Тип шаблона",
                                info="system — инструкции для LLM, user — запрос на обогащение",
                            )
                            template_dropdown = gr.Dropdown(
                                choices=self.prompt_engine.list_system_templates(),
                                value="default",
                                label="Шаблон",
                                scale=2,
                            )

                        template_editor = gr.Code(
                            label="📄 Шаблон (Jinja2)",
                            language="jinja2",
                            lines=20,
                            elem_classes=["code-editor"],
                        )

                        template_description = gr.Textbox(
                            label="Описание шаблона",
                            lines=1,
                            placeholder="Краткое описание назначения шаблона...",
                        )

                        with gr.Row():
                            load_template_btn = gr.Button("📥 Загрузить", variant="secondary")
                            preview_template_btn = gr.Button("👁️ Preview", variant="secondary")
                            save_template_btn = gr.Button(
                                "💾 Сохранить",
                                variant="primary",
                                elem_classes=["primary-btn"],
                            )

                        template_status = gr.Textbox(
                            label="Статус",
                            interactive=False,
                            elem_id="template-status",
                        )

                    gr.Markdown("### 👁️ Предпросмотр", elem_classes=["section-header"])

                    with gr.Group(elem_classes=["output-group"]):
                        template_preview = gr.Textbox(
                            label="Результат рендеринга с тестовыми данными",
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
                with gr.TabItem("👤 Профили", id="profiles-tab"):
                    gr.Markdown("### 📂 Управление профилями", elem_classes=["section-header"])

                    with gr.Group(elem_classes=["input-group"]):
                        with gr.Row():
                            profiles_dropdown = gr.Dropdown(
                                choices=self.config_manager.list_profiles(),
                                value="default",
                                label="Выбор профиля",
                                scale=4,
                            )
                            refresh_profiles_btn = gr.Button(
                                "🔄 Обновить",
                                scale=1,
                                variant="secondary",
                            )

                    with gr.Row(equal_height=False):
                        with gr.Column(elem_classes=["profile-card"]):
                            gr.Markdown("### ⚙️ Основные настройки", elem_classes=["section-header"])
                            profile_name_input = gr.Textbox(
                                label="Имя профиля",
                                placeholder="например: production",
                            )
                            profile_description = gr.Textbox(
                                label="Описание",
                                lines=2,
                                placeholder="Описание назначения профиля...",
                            )

                            gr.Markdown("### 📝 Промпты", elem_classes=["section-header"])
                            profile_system_prompt = gr.Dropdown(
                                choices=self.prompt_engine.list_system_templates(),
                                label="Системный промпт",
                                info="Шаблон инструкций для LLM",
                            )
                            profile_user_prompt = gr.Dropdown(
                                choices=self.prompt_engine.list_user_templates(),
                                label="Пользовательский промпт",
                                info="Шаблон запроса на обогащение",
                            )

                        with gr.Column(elem_classes=["profile-card"]):
                            gr.Markdown("### 🤖 LLM параметры", elem_classes=["section-header"])
                            profile_temperature = gr.Slider(
                                minimum=0,
                                maximum=1,
                                step=0.1,
                                value=0.3,
                                label="Temperature",
                                info="0 — детерминированный, 1 — креативный",
                            )
                            profile_max_tokens = gr.Number(
                                value=4000,
                                label="Max Tokens",
                                info="Максимальная длина ответа",
                            )

                            gr.Markdown("### 💾 Кэширование", elem_classes=["section-header"])
                            profile_cache_enabled = gr.Checkbox(
                                value=True,
                                label="✅ Кэширование включено",
                            )
                            profile_cache_ttl = gr.Number(
                                value=3600,
                                label="TTL (секунды)",
                                info="Время жизни кэша",
                            )

                            gr.Markdown("### 🔍 Веб-поиск", elem_classes=["section-header"])
                            profile_web_search = gr.Checkbox(
                                value=True,
                                label="✅ Веб-поиск включен",
                            )

                    gr.Markdown("### 🎯 Поля для извлечения", elem_classes=["section-header"])
                    with gr.Group(elem_classes=["input-group"]):
                        profile_fields = gr.CheckboxGroup(
                            choices=self._get_field_choices(),
                            value=self._get_default_fields(),
                            label="Включенные поля",
                        )

                    with gr.Row():
                        load_profile_btn = gr.Button("📥 Загрузить профиль", variant="secondary")
                        save_profile_btn = gr.Button(
                            "💾 Сохранить профиль",
                            variant="primary",
                            elem_classes=["primary-btn"],
                        )

                    profile_status = gr.Textbox(
                        label="Статус",
                        interactive=False,
                        elem_id="profile-status",
                    )

                    gr.HTML('<div class="section-divider"></div>')

                    gr.Markdown("### ➕ Создание нового профиля", elem_classes=["section-header"])
                    with gr.Group(elem_classes=["input-group"]):
                        with gr.Row():
                            new_profile_name = gr.Textbox(
                                label="Имя нового профиля",
                                placeholder="например: ecommerce",
                                scale=2,
                            )
                            base_profile_dropdown = gr.Dropdown(
                                choices=self.config_manager.list_profiles(),
                                value="default",
                                label="На основе профиля",
                                scale=2,
                            )
                            create_profile_btn = gr.Button(
                                "➕ Создать",
                                variant="secondary",
                                scale=1,
                            )
                        create_status = gr.Textbox(
                            label="Статус",
                            interactive=False,
                        )

                    gr.Markdown("### 🗑️ Удаление профиля", elem_classes=["section-header"])
                    with gr.Group(elem_classes=["input-group"]):
                        with gr.Row():
                            delete_profile_dropdown = gr.Dropdown(
                                choices=[p for p in self.config_manager.list_profiles() if p != "default"],
                                label="Профиль для удаления",
                                info="Профиль 'default' нельзя удалить",
                                scale=3,
                            )
                            delete_profile_btn = gr.Button(
                                "🗑️ Удалить",
                                variant="stop",
                                scale=1,
                            )
                        delete_status = gr.Textbox(
                            label="Статус",
                            interactive=False,
                        )

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

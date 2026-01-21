"""Engine Layer for AI Product Enricher.

This module provides the core engine components for configurable product enrichment:
- FieldRegistry: Manages field definitions for extraction
- PromptEngine: Handles Jinja2 template rendering for prompts
- ConfigurationManager: Manages enrichment profiles and settings
"""

from .config_manager import (
    CacheConfig,
    ConfigurationManager,
    EnrichmentProfile,
    FieldsConfig,
    LLMConfig,
    PromptsConfig,
    WebSearchConfig,
)
from .field_registry import (
    FieldDefinition,
    FieldExample,
    FieldRegistry,
    FieldSet,
)
from .prompt_engine import (
    PromptEngine,
    PromptTemplate,
    PromptVariable,
)

__all__ = [
    # Field Registry
    "FieldRegistry",
    "FieldSet",
    "FieldDefinition",
    "FieldExample",
    # Prompt Engine
    "PromptEngine",
    "PromptTemplate",
    "PromptVariable",
    # Configuration Manager
    "ConfigurationManager",
    "EnrichmentProfile",
    "PromptsConfig",
    "FieldsConfig",
    "LLMConfig",
    "CacheConfig",
    "WebSearchConfig",
]

"""WebUI module for AI Product Enricher.

This module provides a Gradio-based web interface for:
- Testing product enrichment
- Configuring field definitions
- Editing prompt templates
- Managing enrichment profiles
"""

from .app import EnricherWebUI, create_app

__all__ = [
    "EnricherWebUI",
    "create_app",
]

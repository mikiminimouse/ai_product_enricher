"""Entry point for AI Product Enricher WebUI.

Usage:
    # Only WebUI (demo mode, no enricher)
    python -m src.ai_product_enricher.main_webui

    # WebUI with enricher service
    python -m src.ai_product_enricher.main_webui --with-enricher

    # Custom port and share publicly
    python -m src.ai_product_enricher.main_webui --port 7860 --share
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def main() -> None:
    """Main entry point for WebUI."""
    parser = argparse.ArgumentParser(
        description="AI Product Enricher WebUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m src.ai_product_enricher.main_webui
    python -m src.ai_product_enricher.main_webui --with-enricher
    python -m src.ai_product_enricher.main_webui --port 7860 --share
        """,
    )
    parser.add_argument(
        "--with-enricher",
        action="store_true",
        help="Enable enricher service for actual product enrichment",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run the WebUI on (default: 7860)",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public shareable link",
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default=None,
        help="Path to config directory",
    )

    args = parser.parse_args()

    # Initialize enricher service if requested
    enricher_service = None
    if args.with_enricher:
        try:
            from src.ai_product_enricher.api.dependencies import get_enricher_service

            enricher_service = get_enricher_service()
            print("Enricher service initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize enricher service: {e}")
            print("Running in demo mode without enricher")

    # Create and launch app
    from src.ai_product_enricher.webui import create_app

    app = create_app(
        enricher_service=enricher_service,
        config_dir=args.config_dir,
    )

    print(f"\nStarting AI Product Enricher WebUI on port {args.port}")
    if args.with_enricher:
        print("Mode: Full (with enricher service)")
    else:
        print("Mode: Demo (without enricher service)")
    print("\n")

    # Get custom theme and css from app attributes (Gradio 6.0+ compatibility)
    theme = getattr(app, "_custom_theme", None)
    css = getattr(app, "_custom_css", None)

    app.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
        show_error=True,
        theme=theme,
        css=css,
    )


if __name__ == "__main__":
    main()

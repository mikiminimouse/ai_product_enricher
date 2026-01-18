"""Product models for AI Product Enricher."""

from typing import Any

from pydantic import BaseModel, Field


class ProductInput(BaseModel):
    """Input model for product to be enriched."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Product name (required)",
    )
    category: str | None = Field(
        default=None,
        max_length=200,
        description="Product category",
    )
    brand: str | None = Field(
        default=None,
        max_length=200,
        description="Product brand",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Existing product description",
    )
    sku: str | None = Field(
        default=None,
        max_length=100,
        description="Stock Keeping Unit (article)",
    )
    attributes: dict[str, Any] | None = Field(
        default=None,
        description="Additional product attributes",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "iPhone 15 Pro Max",
                    "category": "smartphones",
                    "brand": "Apple",
                    "description": "Flagship smartphone",
                    "sku": "IPHN15PM-256-BLK",
                    "attributes": {"color": "black", "storage": "256GB"},
                }
            ]
        }
    }

    def get_search_query(self) -> str:
        """Generate a search query for web search."""
        parts = [self.name]
        if self.brand:
            parts.insert(0, self.brand)
        if self.category:
            parts.append(self.category)
        return " ".join(parts)

    def to_prompt_context(self) -> str:
        """Convert product to context string for LLM prompt."""
        lines = [f"Product Name: {self.name}"]
        if self.brand:
            lines.append(f"Brand: {self.brand}")
        if self.category:
            lines.append(f"Category: {self.category}")
        if self.description:
            lines.append(f"Existing Description: {self.description}")
        if self.sku:
            lines.append(f"SKU: {self.sku}")
        if self.attributes:
            attrs = ", ".join(f"{k}: {v}" for k, v in self.attributes.items())
            lines.append(f"Attributes: {attrs}")
        return "\n".join(lines)

"""Product models for AI Product Enricher."""

from pydantic import BaseModel, Field


class ProductInput(BaseModel):
    """Input model for product to be enriched.

    Simplified input - user provides only name and optional description
    from price list or procurement documents. LLM will extract brand,
    category, and other structured data automatically.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Product name from price list or procurement document",
    )
    description: str | None = Field(
        default=None,
        max_length=10000,
        description="Free-form description that may contain specifications, attributes, brand info",
    )
    country_origin: str | None = Field(
        default=None,
        min_length=2,
        max_length=3,
        description="Country of origin (ISO 3166-1 alpha-2/3), e.g. 'RU', 'CN', 'US'",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Смартфон Apple iPhone 15 Pro Max 256GB Black",
                    "description": "Флагманский смартфон с чипом A17 Pro, титановым корпусом",
                    "country_origin": "CN",
                },
                {
                    "name": "Ноутбук ASUS ROG Strix G16 G614JI-N3132",
                    "description": None,
                    "country_origin": None,
                },
                {
                    "name": "Яндекс Станция Макс",
                    "description": "Умная колонка с Алисой",
                    "country_origin": "RU",
                },
            ]
        }
    }

    def get_search_query(self) -> str:
        """Generate a search query for web search."""
        # Use full name as search query - it usually contains brand and model
        return self.name

    def to_prompt_context(self) -> str:
        """Convert product to context string for LLM prompt."""
        lines = [f"Product Name (from price list): {self.name}"]
        if self.description:
            lines.append(f"Additional Description: {self.description}")
        return "\n".join(lines)

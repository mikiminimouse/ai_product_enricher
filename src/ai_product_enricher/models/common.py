"""Common models shared across the application."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail model for API responses."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error details")


class APIResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    success: bool = Field(..., description="Whether the request was successful")
    data: T | None = Field(default=None, description="Response data")
    error: ErrorDetail | None = Field(default=None, description="Error details if not successful")

    @classmethod
    def ok(cls, data: T) -> "APIResponse[T]":
        """Create a successful response."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: ErrorDetail) -> "APIResponse[T]":
        """Create a failed response."""
        return cls(success=False, error=error)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1

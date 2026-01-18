"""Custom exceptions for AI Product Enricher."""

from typing import Any


class AIProductEnricherError(Exception):
    """Base exception for AI Product Enricher."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(AIProductEnricherError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={**(details or {}), "field": field} if field else details,
        )
        self.field = field


class ZhipuAPIError(AIProductEnricherError):
    """Raised when Zhipu AI API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        api_error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="ZHIPU_API_ERROR",
            details={
                **(details or {}),
                "status_code": status_code,
                "api_error_code": api_error_code,
            },
        )
        self.status_code = status_code
        self.api_error_code = api_error_code


class RateLimitError(AIProductEnricherError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            details={**(details or {}), "retry_after": retry_after},
        )
        self.retry_after = retry_after


class EnrichmentError(AIProductEnricherError):
    """Raised when product enrichment fails."""

    def __init__(
        self,
        message: str,
        product_name: str | None = None,
        stage: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="ENRICHMENT_ERROR",
            details={
                **(details or {}),
                "product_name": product_name,
                "stage": stage,
            },
        )
        self.product_name = product_name
        self.stage = stage


class CacheError(AIProductEnricherError):
    """Raised when cache operations fail."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="CACHE_ERROR",
            details={**(details or {}), "operation": operation},
        )
        self.operation = operation


class ConfigurationError(AIProductEnricherError):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={**(details or {}), "config_key": config_key},
        )
        self.config_key = config_key

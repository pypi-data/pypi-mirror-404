"""Custom exceptions for API operations."""


class PlannerAPIError(Exception):
    """Base exception for Planner API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            status_code: HTTP status code if applicable.
        """
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(PlannerAPIError):
    """Raised when authentication fails or token is invalid."""

    pass


class RateLimitError(PlannerAPIError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            retry_after: Seconds to wait before retrying.
        """
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ResourceNotFoundError(PlannerAPIError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        """Initialize the exception."""
        super().__init__(message, status_code=404)


class ETagMismatchError(PlannerAPIError):
    """Raised when ETag doesn't match (resource was modified)."""

    def __init__(
        self, message: str = "Resource was modified by another user"
    ) -> None:
        """Initialize the exception."""
        super().__init__(message, status_code=409)


class PermissionDeniedError(PlannerAPIError):
    """Raised when user doesn't have permission."""

    def __init__(self, message: str = "Permission denied") -> None:
        """Initialize the exception."""
        super().__init__(message, status_code=403)

"""Custom exceptions for the HeyGen MCP package."""


class HeyGenError(Exception):
    """Base exception for HeyGen API errors."""

    pass


class HeyGenAPIError(HeyGenError):
    """Exception raised when the HeyGen API returns an error."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class HeyGenAuthError(HeyGenAPIError):
    """Exception raised for authentication errors."""

    pass


class HeyGenRateLimitError(HeyGenAPIError):
    """Exception raised when API rate limit is exceeded."""

    pass


class HeyGenNotFoundError(HeyGenAPIError):
    """Exception raised when a resource is not found."""

    pass


class HeyGenValidationError(HeyGenError):
    """Exception raised for validation errors."""

    pass

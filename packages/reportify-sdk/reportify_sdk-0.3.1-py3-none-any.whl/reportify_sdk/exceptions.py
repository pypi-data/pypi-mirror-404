"""
Reportify SDK Exceptions

Custom exception classes for handling API errors.
"""


class ReportifyError(Exception):
    """Base exception for Reportify SDK"""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(ReportifyError):
    """Raised when API key is invalid or missing"""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class RateLimitError(ReportifyError):
    """Raised when rate limit is exceeded"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class NotFoundError(ReportifyError):
    """Raised when requested resource is not found"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class APIError(ReportifyError):
    """Raised for general API errors"""

    pass

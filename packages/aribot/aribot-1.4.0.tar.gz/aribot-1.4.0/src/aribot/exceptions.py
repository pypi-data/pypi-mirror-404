"""Aribot SDK Exceptions - by Aristiun & Ayurak"""


class AribotError(Exception):
    """Base exception for Aribot SDK"""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.message)


class AuthenticationError(AribotError):
    """Invalid or missing API key"""
    pass


class RateLimitError(AribotError):
    """API rate limit exceeded"""

    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ValidationError(AribotError):
    """Invalid request parameters"""

    def __init__(self, message: str, errors: list = None, **kwargs):
        super().__init__(message, **kwargs)
        self.errors = errors or []


class NotFoundError(AribotError):
    """Resource not found"""
    pass


class ServerError(AribotError):
    """Server-side error"""
    pass

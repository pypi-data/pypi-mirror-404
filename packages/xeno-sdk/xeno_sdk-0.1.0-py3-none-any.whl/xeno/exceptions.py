"""Xeno SDK Exceptions"""

from typing import Optional, Dict, Any


class XenoError(Exception):
    """Base exception for Xeno SDK errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class AuthenticationError(XenoError):
    """Raised when authentication fails (invalid API key)"""

    pass


class RateLimitError(XenoError):
    """Raised when rate limit is exceeded"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message, status_code, response)
        self.retry_after = retry_after


class APIError(XenoError):
    """Raised when the API returns an error"""

    pass


class InvalidRequestError(XenoError):
    """Raised when the request is invalid"""

    pass


class InsufficientCreditsError(XenoError):
    """Raised when there are not enough credits"""

    pass

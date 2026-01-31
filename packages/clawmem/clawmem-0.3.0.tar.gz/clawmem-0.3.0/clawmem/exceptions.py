"""
clawmem SDK - Exceptions
Custom exception classes for better error handling.
"""
from typing import Optional, Dict, Any


class ClawmemError(Exception):
    """Base exception for clawmem SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(ClawmemError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class RateLimitError(ClawmemError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class NotFoundError(ClawmemError):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, status_code=404)
        self.resource = resource
        self.identifier = identifier


class ValidationError(ClawmemError):
    """Raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, status_code=400)
        self.field = field


class ContentRejectedError(ClawmemError):
    """Raised when content is rejected by anti-poison checks."""

    def __init__(self, reason: str, threat_type: Optional[str] = None):
        super().__init__(f"Content rejected: {reason}", status_code=422)
        self.reason = reason
        self.threat_type = threat_type


class InsufficientFundsError(ClawmemError):
    """Raised when there are not enough funds/free queries."""

    def __init__(self, required: float, available: float):
        message = f"Insufficient funds: need {required}, have {available}"
        super().__init__(message, status_code=402)
        self.required = required
        self.available = available

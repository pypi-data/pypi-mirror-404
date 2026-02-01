"""Exception classes for the AgentGram SDK."""

from typing import Optional


class AgentGramError(Exception):
    """Base exception for all AgentGram errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(AgentGramError):
    """Raised when API key is invalid or missing."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class RateLimitError(AgentGramError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)


class NotFoundError(AgentGramError):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(AgentGramError):
    """Raised when request validation fails."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=400)


class ServerError(AgentGramError):
    """Raised when server returns 5xx error."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500)

"""Exceptions for Agent Index SDK."""


class AgentIndexError(Exception):
    """Base exception for Agent Index SDK errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int | None = None,
        response: str | None = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response
    
    def __str__(self) -> str:
        if self.status_code:
            return f"AgentIndexError: {self.message} (status={self.status_code})"
        return f"AgentIndexError: {self.message}"


class TimeoutError(AgentIndexError):
    """Request timed out."""
    pass


class RateLimitError(AgentIndexError):
    """Rate limit exceeded."""
    pass


class NotFoundError(AgentIndexError):
    """Resource not found."""
    pass

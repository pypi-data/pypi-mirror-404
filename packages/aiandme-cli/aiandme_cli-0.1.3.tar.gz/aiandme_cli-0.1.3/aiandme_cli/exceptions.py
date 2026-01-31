"""AIandMe SDK exceptions."""


class AIandMeError(Exception):
    """Base exception for AIandMe SDK."""

    pass


class AuthenticationError(AIandMeError):
    """Raised when authentication fails or token is expired."""

    pass


class NotAuthenticatedError(AIandMeError):
    """Raised when trying to make API calls without authentication."""

    pass


class APIError(AIandMeError):
    """Raised when API returns an error response."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""

    pass


class ForbiddenError(APIError):
    """Raised when access to a resource is denied (401/403)."""

    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429)."""

    pass


class ValidationError(AIandMeError):
    """Raised when input validation fails."""

    pass


class ConfigurationError(AIandMeError):
    """Raised when SDK configuration is invalid."""

    pass

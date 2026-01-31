"""Exception hierarchy for expt-logger."""


class ExptLoggerError(Exception):
    """Base exception for all expt-logger errors."""

    pass


class APIError(ExptLoggerError):
    """Exception raised when an API request fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(APIError):
    """Exception raised for authentication failures (401)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class ConfigurationError(ExptLoggerError):
    """Exception raised for invalid configuration."""

    pass


class ValidationError(ExptLoggerError):
    """Exception raised for invalid input data."""

    pass

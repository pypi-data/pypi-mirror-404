"""Tests for exception hierarchy."""

from expt_logger.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ExptLoggerError,
)


def test_base_exception():
    """Test ExptLoggerError base exception."""
    error = ExptLoggerError("test message")
    assert str(error) == "test message"
    assert isinstance(error, Exception)


def test_api_error_with_status_code():
    """Test APIError with status code."""
    error = APIError("request failed", status_code=500)
    assert str(error) == "request failed"
    assert error.status_code == 500
    assert isinstance(error, ExptLoggerError)


def test_api_error_without_status_code():
    """Test APIError without status code."""
    error = APIError("request failed")
    assert str(error) == "request failed"
    assert error.status_code is None


def test_authentication_error():
    """Test AuthenticationError."""
    error = AuthenticationError()
    assert str(error) == "Authentication failed"
    assert error.status_code == 401
    assert isinstance(error, APIError)
    assert isinstance(error, ExptLoggerError)


def test_authentication_error_custom_message():
    """Test AuthenticationError with custom message."""
    error = AuthenticationError("invalid API key")
    assert str(error) == "invalid API key"
    assert error.status_code == 401


def test_configuration_error():
    """Test ConfigurationError."""
    error = ConfigurationError("invalid config")
    assert str(error) == "invalid config"
    assert isinstance(error, ExptLoggerError)


def test_exception_inheritance():
    """Test exception inheritance hierarchy."""
    # AuthenticationError is a subclass of APIError
    assert issubclass(AuthenticationError, APIError)
    # APIError is a subclass of ExptLoggerError
    assert issubclass(APIError, ExptLoggerError)
    # ConfigurationError is a subclass of ExptLoggerError
    assert issubclass(ConfigurationError, ExptLoggerError)
    # All are subclasses of Exception
    assert issubclass(ExptLoggerError, Exception)

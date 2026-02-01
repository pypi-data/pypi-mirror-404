"""Tests for the Cufinder exceptions."""

import pytest
from cufinder.exceptions import (
    CufinderError, AuthenticationError, ValidationError,
    RateLimitError, CreditLimitError, NetworkError
)


class TestCufinderError:
    """Test cases for CufinderError."""

    def test_cufinder_error_creation(self):
        """Test creating a CufinderError."""
        error = CufinderError("Test error", "TEST_ERROR", 400)
        assert error.message == "Test error"
        assert error.error_type == "TEST_ERROR"
        assert error.status_code == 400
        assert error.details == {}

    def test_cufinder_error_with_details(self):
        """Test creating a CufinderError with details."""
        details = {"field": "value"}
        error = CufinderError("Test error", "TEST_ERROR", 400, details)
        assert error.details == details

    def test_cufinder_error_str(self):
        """Test string representation of CufinderError."""
        error = CufinderError("Test error", "TEST_ERROR", 400)
        assert "[TEST_ERROR] Test error (Status: 400)" in str(error)

    def test_cufinder_error_str_no_status(self):
        """Test string representation without status code."""
        error = CufinderError("Test error", "TEST_ERROR")
        assert "[TEST_ERROR] Test error" in str(error)

    def test_cufinder_error_to_dict(self):
        """Test converting error to dictionary."""
        details = {"field": "value"}
        error = CufinderError("Test error", "TEST_ERROR", 400, details)
        result = error.to_dict()
        
        assert result["error_type"] == "TEST_ERROR"
        assert result["message"] == "Test error"
        assert result["status_code"] == 400
        assert result["details"] == details


class TestAuthenticationError:
    """Test cases for AuthenticationError."""

    def test_authentication_error_creation(self):
        """Test creating an AuthenticationError."""
        error = AuthenticationError("Invalid API key")
        assert error.message == "Invalid API key"
        assert error.error_type == "AUTHENTICATION_ERROR"
        assert error.status_code == 401

    def test_authentication_error_default_message(self):
        """Test AuthenticationError with default message."""
        error = AuthenticationError()
        assert error.message == "Authentication failed"
        assert error.error_type == "AUTHENTICATION_ERROR"
        assert error.status_code == 401


class TestValidationError:
    """Test cases for ValidationError."""

    def test_validation_error_creation(self):
        """Test creating a ValidationError."""
        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.error_type == "VALIDATION_ERROR"
        assert error.status_code == 400

    def test_validation_error_with_details(self):
        """Test ValidationError with details."""
        details = {"field": "required"}
        error = ValidationError("Invalid input", details)
        assert error.details == details

    def test_validation_error_default_message(self):
        """Test ValidationError with default message."""
        error = ValidationError()
        assert error.message == "Validation failed"
        assert error.error_type == "VALIDATION_ERROR"
        assert error.status_code == 400


class TestRateLimitError:
    """Test cases for RateLimitError."""

    def test_rate_limit_error_creation(self):
        """Test creating a RateLimitError."""
        error = RateLimitError("Rate limit exceeded", 60)
        assert error.message == "Rate limit exceeded"
        assert error.error_type == "RATE_LIMIT_ERROR"
        assert error.status_code == 429
        assert error.retry_after == 60

    def test_rate_limit_error_without_retry_after(self):
        """Test RateLimitError without retry_after."""
        error = RateLimitError("Rate limit exceeded")
        assert error.retry_after is None

    def test_rate_limit_error_default_message(self):
        """Test RateLimitError with default message."""
        error = RateLimitError()
        assert error.message == "Rate limit exceeded"
        assert error.error_type == "RATE_LIMIT_ERROR"
        assert error.status_code == 429


class TestCreditLimitError:
    """Test cases for CreditLimitError."""

    def test_credit_limit_error_creation(self):
        """Test creating a CreditLimitError."""
        error = CreditLimitError("No credits remaining")
        assert error.message == "No credits remaining"
        assert error.error_type == "CREDIT_LIMIT_ERROR"
        assert error.status_code == 402

    def test_credit_limit_error_default_message(self):
        """Test CreditLimitError with default message."""
        error = CreditLimitError()
        assert error.message == "Credit limit exceeded"
        assert error.error_type == "CREDIT_LIMIT_ERROR"
        assert error.status_code == 402


class TestNetworkError:
    """Test cases for NetworkError."""

    def test_network_error_creation(self):
        """Test creating a NetworkError."""
        error = NetworkError("Connection failed", 500)
        assert error.message == "Connection failed"
        assert error.error_type == "NETWORK_ERROR"
        assert error.status_code == 500

    def test_network_error_default_message(self):
        """Test NetworkError with default message."""
        error = NetworkError()
        assert error.message == "Network error"
        assert error.error_type == "NETWORK_ERROR"
        assert error.status_code == 0

    def test_network_error_default_status(self):
        """Test NetworkError with default status."""
        error = NetworkError("Custom message")
        assert error.message == "Custom message"
        assert error.status_code == 0


class TestExceptionHierarchy:
    """Test cases for exception hierarchy."""

    def test_all_exceptions_inherit_from_cufinder_error(self):
        """Test that all exceptions inherit from CufinderError."""
        exceptions = [
            AuthenticationError(),
            ValidationError(),
            RateLimitError(),
            CreditLimitError(),
            NetworkError()
        ]
        
        for exc in exceptions:
            assert isinstance(exc, CufinderError)

    def test_exception_attributes(self):
        """Test that all exceptions have required attributes."""
        exceptions = [
            AuthenticationError(),
            ValidationError(),
            RateLimitError(),
            CreditLimitError(),
            NetworkError()
        ]
        
        for exc in exceptions:
            assert hasattr(exc, 'message')
            assert hasattr(exc, 'error_type')
            assert hasattr(exc, 'status_code')
            assert hasattr(exc, 'details')
            assert hasattr(exc, 'to_dict')

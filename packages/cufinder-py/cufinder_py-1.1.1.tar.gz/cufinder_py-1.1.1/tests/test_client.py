"""Tests for the Cufinder client."""

import pytest
from unittest.mock import Mock, patch

from cufinder.client import CufinderClient
from cufinder.exceptions import ValidationError, AuthenticationError


class TestCUFinderClient:
    """Test cases for CUFinderClient."""

    def test_init_with_valid_api_key(self):
        """Test client initialization with valid API key."""
        client = CufinderClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.cufinder.io/v2"
        assert client.timeout == 30

    def test_init_without_api_key(self):
        """Test client initialization without API key raises error."""
        with pytest.raises(ValidationError, match="API key is required"):
            CufinderClient(api_key="")

    def test_init_with_custom_config(self):
        """Test client initialization with custom configuration."""
        client = CufinderClient(
            api_key="test-key",
            base_url="https://custom.api.com",
            timeout=60,
            max_retries=5
        )
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60
        assert client.max_retries == 5

    @patch('cufinder.client.requests.Session')
    def test_post_request_success(self, mock_session):
        """Test successful POST request."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"domain": "example.com"}
        mock_session.return_value.request.return_value = mock_response

        client = CufinderClient(api_key="test-key")
        result = client.post("/test", {"key": "value"})

        assert result == {"domain": "example.com"}

    @patch('cufinder.client.requests.Session')
    def test_post_request_authentication_error(self, mock_session):
        """Test POST request with authentication error."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_response.json.return_value = {"message": "Invalid API key"}
        mock_session.return_value.request.return_value = mock_response

        client = CufinderClient(api_key="test-key")
        
        with pytest.raises(AuthenticationError, match="Invalid API key"):
            client.post("/test", {"key": "value"})

    def test_get_api_key_masked(self):
        """Test API key masking for security."""
        client = CufinderClient(api_key="test-api-key-12345")
        masked_key = client.get_api_key()
        assert masked_key == "test...2345"

    def test_get_api_key_short(self):
        """Test API key masking for short keys."""
        client = CufinderClient(api_key="short")
        masked_key = client.get_api_key()
        assert masked_key == "****"

    def test_set_api_key(self):
        """Test setting new API key."""
        client = CufinderClient(api_key="old-key")
        client.set_api_key("new-key")
        assert client.api_key == "new-key"

    def test_set_api_key_empty(self):
        """Test setting empty API key raises error."""
        client = CufinderClient(api_key="test-key")
        
        with pytest.raises(ValidationError, match="API key cannot be empty"):
            client.set_api_key("")

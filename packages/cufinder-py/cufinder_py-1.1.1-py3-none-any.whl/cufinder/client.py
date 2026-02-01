"""HTTP client for the CUFinder API."""

from typing import Any, Dict, Optional

from .base_api_client import BaseApiClient, CufinderClientConfig, RequestConfig
from .exceptions import ValidationError


class CufinderClient(BaseApiClient):
    """
    Main CUFinder API client class.
    
    Provides a type-safe interface for interacting with the CUFinder B2B data enrichment API.
    Follows SOLID principles:
    - Single Responsibility: Handles HTTP communication only
    - Open/Closed: Extensible through service classes
    - Liskov Substitution: Can be replaced with mock implementations
    - Interface Segregation: Provides focused interfaces
    - Dependency Inversion: Depends on abstractions, not concretions
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.cufinder.io/v2",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize the CUFinder client.
        
        Args:
            api_key: Your CUFinder API key
            base_url: Base URL for the API (default: https://api.cufinder.io/v2)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries for failed requests (default: 3)
        """
        if not api_key:
            raise ValidationError("API key is required")

        # Initialize base client
        config = CufinderClientConfig(timeout=timeout * 1000)  # Convert to milliseconds
        super().__init__(config, api_key)
        
        # Store additional properties for backward compatibility
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Make a raw HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            url: Request URL (relative to base_url)
            params: Query parameters
            data: Request body data
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Response data as dictionary
            
        Raises:
            CufinderError: If the request fails
        """
        # Build full URL
        if url.startswith("http"):
            full_url = url
        else:
            full_url = f"{self.base_url}/{url.lstrip('/')}"

        # Use base client's request method
        config = RequestConfig(
            method=method,
            url=full_url,
            params=params,
            data=data,
            headers=headers,
            timeout=timeout * 1000 if timeout else None,  # Convert to milliseconds
        )
        
        response = super().request(config)
        return response.data

    def post(
        self,
        url: str,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", url, data=data, headers=headers)
    
    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", url, params=params, headers=headers)
    
    def put(
        self,
        url: str,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", url, data=data, headers=headers)
    
    def patch(
        self,
        url: str,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a PATCH request."""
        return self.request("PATCH", url, data=data, headers=headers)
    
    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", url, headers=headers)

    def get_base_url(self) -> str:
        """Get the base URL."""
        return self.base_url

    def set_base_url(self, base_url: str) -> None:
        """Update the base URL."""
        self.base_url = base_url.rstrip("/")

"""Base API client class for CUFinder
Provides a type-safe interface for interacting with the CUFinder B2B data enrichment API
Follows SOLID principles:
- Single Responsibility: Handles HTTP communication only
- Open/Closed: Extensible through service classes
- Liskov Substitution: Can be replaced with mock implementations
- Interface Segregation: Provides focused interfaces
- Dependency Inversion: Depends on abstractions, not concretions
"""

import time
import uuid
from typing import Any, Dict, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    AuthenticationError,
    CreditLimitError,
    CufinderError,
    NetworkError,
    NotFoundError,
    PayloadError,
    RateLimitError,
    ServerError,
)


class RequestConfig:
    """Request configuration for API calls"""
    def __init__(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: Optional[int] = None,
    ):
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.params = params
        self.data = data
        self.timeout = timeout


class Response:
    """Response wrapper for API calls"""
    def __init__(
        self,
        data: Any,
        status: int,
        status_text: str,
        headers: Dict[str, str],
    ):
        self.data = data
        self.status = status
        self.status_text = status_text
        self.headers = headers


class CufinderClientConfig:
    """Client configuration"""
    def __init__(self, timeout: Optional[int] = None):
        self.timeout = timeout


class BaseApiClient:
    """Base API client class for CUFinder"""

    def __init__(self, config: CufinderClientConfig, api_key: str):
        if not api_key:
            raise AuthenticationError('API key is required')

        self.api_key = api_key
        self.config = config

        # Initialize HTTP client
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({
            'x-api-key': api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'cufinder-py/1.1.1',
        })

        # Set default timeout
        self.session.timeout = config.timeout or 30000

    def request(self, config: RequestConfig) -> Response:
        """
        Make a raw HTTP request to the API
        
        Args:
            config: Request configuration
            
        Returns:
            Response: API response
            
        Raises:
            CufinderError: If the request fails
        """
        try:
            # Build full URL
            if config.url.startswith("http"):
                full_url = config.url
            else:
                full_url = f"https://api.cufinder.io/v2/{config.url.lstrip('/')}"

            # Prepare headers
            request_headers = self.session.headers.copy()
            request_headers.update(config.headers)
            
            # Add request ID for tracking
            request_headers['X-Request-ID'] = self._generate_request_id()

            response = self.session.request(
                method=config.method.upper(),
                url=full_url,
                params=config.params,
                data=config.data,
                headers=request_headers,
                timeout=config.timeout or self.session.timeout,
            )

            # Handle HTTP errors
            if not response.ok:
                raise self._handle_response_error(response)

            return Response(
                data=response.json(),
                status=response.status_code,
                status_text=response.reason,
                headers=dict(response.headers),
            )

        except requests.exceptions.RequestException as error:
            raise self._handle_request_error(error)
        except Exception as error:
            raise self._handle_request_error(error)

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Make a GET request
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response: API response
        """
        return self.request(RequestConfig(
            method='GET',
            url=url,
            params=params,
            headers=headers,
        ))

    def post(
        self,
        url: str,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Make a POST request
        
        Args:
            url: Request URL
            data: Request body
            headers: Additional headers
            
        Returns:
            Response: API response
        """
        return self.request(RequestConfig(
            method='POST',
            url=url,
            data=data,
            headers=headers,
        ))

    def put(
        self,
        url: str,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Make a PUT request
        
        Args:
            url: Request URL
            data: Request body
            headers: Additional headers
            
        Returns:
            Response: API response
        """
        return self.request(RequestConfig(
            method='PUT',
            url=url,
            data=data,
            headers=headers,
        ))

    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Make a DELETE request
        
        Args:
            url: Request URL
            headers: Additional headers
            
        Returns:
            Response: API response
        """
        return self.request(RequestConfig(
            method='DELETE',
            url=url,
            headers=headers,
        ))

    def patch(
        self,
        url: str,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Make a PATCH request
        
        Args:
            url: Request URL
            data: Request body
            headers: Additional headers
            
        Returns:
            Response: API response
        """
        return self.request(RequestConfig(
            method='PATCH',
            url=url,
            data=data,
            headers=headers,
        ))

    def get_api_key(self) -> str:
        """
        Get the current API key (masked for security)
        
        Returns:
            str: Masked API key
        """
        api_key = self.session.headers.get('x-api-key', '')
        if not api_key:
            return ''

        return (f"{api_key[:4]}...{api_key[-4:]}" 
                if len(api_key) > 8 
                else '****')

    def get_base_url(self) -> str:
        """
        Get the base URL
        
        Returns:
            str: Base URL
        """
        return 'https://api.cufinder.io/v2'

    def set_api_key(self, api_key: str) -> None:
        """
        Update the API key
        
        Args:
            api_key: New API key
            
        Raises:
            AuthenticationError: If API key is empty
        """
        if not api_key:
            raise AuthenticationError('API key cannot be empty')
        
        self.api_key = api_key
        self.session.headers['x-api-key'] = api_key

    def set_timeout(self, timeout: int) -> None:
        """
        Update the request timeout
        
        Args:
            timeout: Timeout in milliseconds
        """
        self.session.timeout = timeout

    def _generate_request_id(self) -> str:
        """
        Generate a unique request ID
        
        Returns:
            str: Request ID
        """
        return f"req_{int(time.time() * 1000)}_{uuid.uuid4().hex[:12]}"

    def _handle_request_error(self, error: Exception) -> CufinderError:
        """
        Handle request errors
        
        Args:
            error: Error object
            
        Returns:
            CufinderError: Formatted error
        """
        if isinstance(error, requests.exceptions.Timeout):
            return NetworkError('Request timeout', 408)
        elif isinstance(error, requests.exceptions.ConnectionError):
            return NetworkError('Unable to connect to API', 0)
        elif isinstance(error, requests.exceptions.RequestException):
            return NetworkError(f'Request failed: {str(error)}', 0)
        else:
            return CufinderError(
                str(error) if isinstance(error, Exception) else 'Unknown request error',
                'REQUEST_ERROR'
            )

    def _handle_response_error(self, response: requests.Response) -> CufinderError:
        """
        Handle response errors
        
        Args:
            response: Response object
            
        Returns:
            CufinderError: Formatted error
        """
        try:
            error_data = response.json()
            message = error_data.get('message', response.reason)
        except (ValueError, KeyError):
            message = response.reason or 'Unknown error'

        status_code = response.status_code

        if status_code == 400:
            # 400 => indicates not enough credit
            return CreditLimitError(message)
        elif status_code == 401:
            # 401 => indicates invalid api key
            return AuthenticationError(message)
        elif status_code == 404:
            # 404 => indicates not found result
            return NotFoundError(message)
        elif status_code == 422:
            # 422 => indicates an error in the payload
            return PayloadError(message, error_data if 'error_data' in locals() else None)
        elif status_code == 429:
            retry_after = response.headers.get('retry-after')
            retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
            return RateLimitError(message, retry_after_int)
        elif status_code in [500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511]:
            # 500, 501, ... => server errors
            return ServerError(message, status_code)
        else:
            return CufinderError(
                message,
                'API_ERROR',
                status_code,
                error_data if 'error_data' in locals() else None,
            )

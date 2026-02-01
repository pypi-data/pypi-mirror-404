"""Base service class for all Cufinder API services."""

from ..client import CufinderClient
from ..exceptions import CufinderError


class BaseService:
    """
    Base service class that provides common functionality for all services.
    
    Follows SOLID principles by providing a single responsibility base class.
    """

    def __init__(self, client: CufinderClient):
        """
        Initialize the base service.
        
        Args:
            client: The CufinderClient instance
        """
        self.client = client

    def parse_response_data(self, response_data: dict):
        """
        Parse API response data from the wrapped response format.
        
        Args:
            response_data: The raw API response
            
        Returns:
            Parsed response data
        """
        # Handle wrapped response format: { status: 1, data: {...} }
        if (
            response_data
            and isinstance(response_data, dict)
            and "status" in response_data
            and "data" in response_data
        ):
            return response_data["data"]
        
        # Handle direct response format
        return response_data


    def handle_error(self, error: Exception, service_name: str) -> CufinderError:
        """
        Handle service errors consistently.
        
        Args:
            error: The error to handle
            service_name: The name of the service for error context
            
        Returns:
            CufinderError: Formatted error
        """
        if isinstance(error, CufinderError):
            return error

        # Handle HTTP errors
        if hasattr(error, 'response') and error.response:
            status = getattr(error.response, 'status_code', 500)
            data = getattr(error.response, 'json', lambda: {})()
            message = data.get('message', str(error)) if isinstance(data, dict) else str(error)
            return CufinderError(f"{service_name}: {message}", "API_ERROR", status, data)

        # Handle network errors
        if hasattr(error, 'request'):
            return CufinderError(
                f"{service_name}: Network error - unable to reach API",
                "NETWORK_ERROR",
                0
            )

        # Handle other errors
        return CufinderError(
            f"{service_name}: {str(error)}",
            "UNKNOWN_ERROR",
            500,
        )


__all__ = ["BaseService"]
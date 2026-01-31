"""Base resource class."""
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ..utils.http import HTTPClient


class BaseResource:
    """
    Base class for all resource classes.
    """

    def __init__(self, http_client: "HTTPClient"):
        """
        Initialize resource.

        Args:
            http_client: HTTP client instance
        """
        self.http = http_client

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request via the HTTP client.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            headers: Additional headers
            files: Files for multipart upload

        Returns:
            Response data as dictionary
        """
        if files:
            # For file uploads, use multipart form data
            return self.http._request_multipart(method, endpoint, data=data, files=files, headers=headers)
        return self.http._request(method, endpoint, data=data, params=params, headers=headers)

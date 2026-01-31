"""
HTTP client with retry logic and error handling.
"""
import time
import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    raise ImportError(
        "requests library is required. Install it with: pip install requests"
    )

from ..config import Config
from ..exceptions import (
    AuthenticationError,
    ResourceNotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    NetworkError,
)

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles date, datetime, and Decimal objects.
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class HTTPClient:
    """
    HTTP client with automatic retries and error handling.
    """

    def __init__(self, config: Config):
        """
        Initialize HTTP client.

        Args:
            config: SDK configuration
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.api_token}",
                "Content-Type": "application/json",
                "User-Agent": "crexperium-python-sdk/1.0.0",
            }
        )
        self.session.verify = config.verify_ssl

    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint.

        Args:
            endpoint: API endpoint (e.g., '/api/v1/contacts/')

        Returns:
            Full URL
        """
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        return urljoin(self.config.base_url, endpoint)

    def _handle_error(self, response: requests.Response) -> None:
        """
        Handle HTTP error responses.

        Args:
            response: Response object

        Raises:
            Appropriate exception based on status code
        """
        try:
            error_data = response.json()
            error_message = error_data.get("error") or error_data.get("detail") or response.text
            errors = error_data if isinstance(error_data, dict) else {}
        except Exception:
            error_message = response.text or f"HTTP {response.status_code} error"
            errors = {}

        if response.status_code == 401:
            raise AuthenticationError(error_message, response=response)
        elif response.status_code == 404:
            raise ResourceNotFoundError(error_message, response=response)
        elif response.status_code == 400:
            raise ValidationError(error_message, errors=errors, response=response)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                error_message, retry_after=retry_after, response=response
            )
        elif response.status_code >= 500:
            raise ServerError(
                error_message, status_code=response.status_code, response=response
            )
        else:
            # Other client errors (4xx)
            raise ValidationError(error_message, errors=errors, response=response)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            headers: Additional headers to send
            retry_count: Current retry attempt

        Returns:
            Response data as dictionary

        Raises:
            Various CRM exceptions based on response
        """
        url = self._build_url(endpoint)

        try:
            logger.debug(f"{method} {url} (attempt {retry_count + 1})")

            # Merge custom headers with session headers
            request_headers = dict(self.session.headers)
            if headers:
                request_headers.update(headers)

            # Serialize data with custom encoder to handle date/datetime/Decimal
            json_data = None
            if data is not None:
                json_data = json.dumps(data, cls=DateTimeEncoder)

            response = self.session.request(
                method=method,
                url=url,
                data=json_data,
                params=params,
                headers=request_headers,
                timeout=self.config.timeout,
            )

            # Handle successful responses (2xx)
            if 200 <= response.status_code < 300:
                # Handle empty responses
                if response.status_code == 204 or not response.content:
                    return {}

                try:
                    return response.json()
                except ValueError:
                    # Response is not JSON
                    return {"data": response.text}

            # Handle error responses
            self._handle_error(response)

        except requests.exceptions.Timeout as e:
            logger.warning(f"Request timeout: {url}")
            if retry_count < self.config.max_retries:
                return self._retry_request(method, endpoint, data, params, headers, retry_count)
            raise NetworkError("Request timeout", original_error=e)

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error: {url}")
            if retry_count < self.config.max_retries:
                return self._retry_request(method, endpoint, data, params, headers, retry_count)
            raise NetworkError("Connection error", original_error=e)

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {url} - {str(e)}")
            raise NetworkError(f"Request failed: {str(e)}", original_error=e)

    def _retry_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
        retry_count: int,
    ) -> Dict[str, Any]:
        """
        Retry failed request with exponential backoff.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            headers: Additional headers
            retry_count: Current retry attempt

        Returns:
            Response data
        """
        # Exponential backoff: delay * 2^retry_count
        delay = self.config.retry_delay * (2**retry_count)
        logger.info(f"Retrying in {delay}s...")
        time.sleep(delay)

        return self._request(method, endpoint, data, params, headers, retry_count + 1)

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data
        """
        return self._request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make POST request.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data
        """
        return self._request("POST", endpoint, data=data, params=params, headers=headers)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make PUT request.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data
        """
        return self._request("PUT", endpoint, data=data, params=params, headers=headers)

    def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make PATCH request.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data
        """
        return self._request("PATCH", endpoint, data=data, params=params, headers=headers)

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make DELETE request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data
        """
        return self._request("DELETE", endpoint, params=params, headers=headers)

    def _request_multipart(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make multipart HTTP request for file uploads.

        Args:
            method: HTTP method (typically POST)
            endpoint: API endpoint
            data: Form data fields
            files: Files to upload (dict of field_name: file_object)
            headers: Additional headers
            retry_count: Current retry attempt

        Returns:
            Response data as dictionary
        """
        url = self._build_url(endpoint)

        try:
            logger.debug(f"{method} {url} (multipart, attempt {retry_count + 1})")

            # For multipart, we need to remove Content-Type header
            # requests will set it automatically with the boundary
            request_headers = {
                "Authorization": f"Bearer {self.config.api_token}",
                "User-Agent": "crexperium-python-sdk/1.0.0",
            }
            if headers:
                request_headers.update(headers)
            # Remove Content-Type if present (let requests set it)
            request_headers.pop("Content-Type", None)

            response = self.session.request(
                method=method,
                url=url,
                data=data,
                files=files,
                headers=request_headers,
                timeout=self.config.timeout,
            )

            # Handle successful responses (2xx)
            if 200 <= response.status_code < 300:
                if response.status_code == 204 or not response.content:
                    return {}
                try:
                    return response.json()
                except ValueError:
                    return {"data": response.text}

            # Handle error responses
            self._handle_error(response)

        except requests.exceptions.Timeout as e:
            logger.warning(f"Request timeout: {url}")
            if retry_count < self.config.max_retries:
                delay = self.config.retry_delay * (2**retry_count)
                time.sleep(delay)
                return self._request_multipart(method, endpoint, data, files, headers, retry_count + 1)
            raise NetworkError("Request timeout", original_error=e)

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error: {url}")
            if retry_count < self.config.max_retries:
                delay = self.config.retry_delay * (2**retry_count)
                time.sleep(delay)
                return self._request_multipart(method, endpoint, data, files, headers, retry_count + 1)
            raise NetworkError("Connection error", original_error=e)

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {url} - {str(e)}")
            raise NetworkError(f"Request failed: {str(e)}", original_error=e)

    def close(self):
        """Close the HTTP session."""
        self.session.close()

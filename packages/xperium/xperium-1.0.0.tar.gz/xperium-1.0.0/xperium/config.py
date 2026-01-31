"""
Configuration for Xperium SDK.
"""
import os
from dataclasses import dataclass
from typing import Optional


# Production API endpoint - fixed and not changeable by users
XPERIUM_API_URL = "https://api.xperium.xyz"

# Environment variable name for API token
XPERIUM_API_TOKEN_ENV = "XPERIUM_API_TOKEN"


@dataclass
class Config:
    """
    Configuration for CRM client.

    The API token is automatically read from the XPERIUM_API_TOKEN environment variable.
    The API endpoint is fixed to the production URL and cannot be changed.

    Args:
        api_token: API token for authentication (optional, reads from env var if not provided)
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retries for failed requests (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 1)
        verify_ssl: Whether to verify SSL certificates (default: True)
    """

    api_token: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True

    def __post_init__(self):
        """Validate configuration and read from environment if needed."""
        # Auto-load API token from environment variable
        if not self.api_token:
            self.api_token = os.getenv(XPERIUM_API_TOKEN_ENV)

        if not self.api_token:
            raise ValueError(
                f"API token is required. Either pass api_token parameter or set "
                f"{XPERIUM_API_TOKEN_ENV} environment variable."
            )

        # Validate timeout
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        # Validate max_retries
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        # Validate retry_delay
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")

    @property
    def base_url(self) -> str:
        """Get the fixed production API URL."""
        return XPERIUM_API_URL

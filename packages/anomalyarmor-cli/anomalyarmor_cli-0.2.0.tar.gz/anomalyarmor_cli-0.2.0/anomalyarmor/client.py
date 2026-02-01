"""Main client for the Armor SDK."""

from __future__ import annotations

from typing import Any

import httpx

from anomalyarmor._version import __version__
from anomalyarmor.config import load_config
from anomalyarmor.exceptions import (
    ArmorError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from anomalyarmor.resources.alerts import AlertsResource
from anomalyarmor.resources.api_keys import APIKeysResource
from anomalyarmor.resources.assets import AssetsResource
from anomalyarmor.resources.badges import BadgesResource
from anomalyarmor.resources.freshness import FreshnessResource
from anomalyarmor.resources.health import HealthResource
from anomalyarmor.resources.intelligence import IntelligenceResource
from anomalyarmor.resources.jobs import JobsResource
from anomalyarmor.resources.lineage import LineageResource
from anomalyarmor.resources.metrics import MetricsResource
from anomalyarmor.resources.recommendations import RecommendationsResource
from anomalyarmor.resources.referential import ReferentialResource
from anomalyarmor.resources.schema import SchemaResource
from anomalyarmor.resources.tags import TagsResource
from anomalyarmor.resources.validity import ValidityResource


class Client:
    """AnomalyArmor API client.

    The main entry point for interacting with the AnomalyArmor API.

    Example:
        >>> from anomalyarmor import Client
        >>>
        >>> # Using environment variable ARMOR_API_KEY
        >>> client = Client()
        >>>
        >>> # Or pass the API key directly
        >>> client = Client(api_key="aa_live_...")
        >>>
        >>> # List assets
        >>> assets = client.assets.list()
        >>> for asset in assets:
        ...     print(asset.qualified_name)
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            api_key: API key for authentication. If not provided, will load from
                     environment variable ARMOR_API_KEY or config file.
            api_url: Base URL for API requests. Defaults to production API.
            timeout: Request timeout in seconds. Defaults to 30.
        """
        # Load config (environment > file > defaults)
        config = load_config()

        # Override with explicit parameters
        self._api_key = api_key or config.api_key
        self._api_url = (api_url or config.api_url).rstrip("/")
        self._timeout = timeout or config.timeout

        if not self._api_key:
            raise AuthenticationError(
                "No API key provided. Set ARMOR_API_KEY environment variable, "
                "pass api_key parameter, or run 'anomalyarmor auth login'."
            )

        # Create HTTP client
        self._http = httpx.Client(
            base_url=self._api_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"anomalyarmor-cli/{__version__}",
            },
            timeout=self._timeout,
        )

        # Initialize resource namespaces
        self.assets = AssetsResource(self)
        self.freshness = FreshnessResource(self)
        self.schema = SchemaResource(self)
        self.lineage = LineageResource(self)
        self.alerts = AlertsResource(self)
        self.api_keys = APIKeysResource(self)
        self.intelligence = IntelligenceResource(self)
        self.jobs = JobsResource(self)
        self.tags = TagsResource(self)
        self.badges = BadgesResource(self)
        # TECH-712: Data quality resources
        self.metrics = MetricsResource(self)
        self.validity = ValidityResource(self)
        self.referential = ReferentialResource(self)
        # TECH-758: Health resource
        self.health = HealthResource(self)
        # TECH-772: Recommendations resource
        self.recommendations = RecommendationsResource(self)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: API path (relative to base URL)
            params: Query parameters
            json: JSON body for POST/PUT requests

        Returns:
            Response data

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            NotFoundError: If resource is not found
            ValidationError: If request validation fails
            ServerError: For other server errors
        """
        try:
            response = self._http.request(
                method=method,
                url=path,
                params=params,
                json=json,
            )
        except httpx.TimeoutException:
            raise ArmorError("Request timed out")
        except httpx.NetworkError as e:
            raise ArmorError(f"Network error: {e}")

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        # Parse response
        try:
            data = response.json()
        except Exception:
            data = {"message": response.text}

        # Success
        if response.status_code < 400:
            return data if isinstance(data, dict) else {}

        # Extract error info - handle both dict and string error formats
        error = data.get("error", {})
        if isinstance(error, dict):
            message = error.get("message") or data.get("message") or "Request failed"
            details = error.get("details", {})
            error_code = error.get("code")
        else:
            # Backend returned error as string
            message = data.get("message") or str(error) or "Request failed"
            details = {}
            error_code = None

        # Handle specific error codes from backend
        if error_code in ("INTELLIGENCE_NOT_GENERATED", "SCHEMA_NOT_DISCOVERED"):
            raise ArmorError(
                message=message,
                code=error_code,
                details=details,
            )

        # Handle HTTP status codes
        if response.status_code == 401:
            raise AuthenticationError(message, details)

        if response.status_code == 403:
            raise AuthenticationError(f"Forbidden: {message}", details)

        if response.status_code == 404:
            raise NotFoundError(message, details=details)

        if response.status_code == 400:
            raise ValidationError(message, details=details)

        if response.status_code == 422:
            raise ValidationError(message, details=details)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(message, retry_after=retry_after, details=details)

        # Generic server error
        raise ServerError(message, status_code=response.status_code, details=details)

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

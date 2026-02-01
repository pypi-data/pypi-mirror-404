"""Base client class for GitHub API interactions."""

from __future__ import annotations

import urllib.parse
from typing import Any


class Client:
    """Abstract base class for GitHub clients."""

    def __init__(self, token: str | None, base_url: str) -> None:
        """Construct the base client.

        Args:
            token: The API token for authentication.
            base_url: The base URL of the GitHub instance.

        """
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.headers: dict[str, Any] = {}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def __str__(self) -> str:
        """Return a string representation of the client.

        Returns:
            str: String representation.

        """
        return f"<Client base_url={self.base_url}>"

    @property
    def api_url(self) -> str:
        """Return the base API URL.

        Returns:
            str: The base API URL.

        """
        if urllib.parse.urlparse(self.base_url).netloc == "github.com":
            return "https://api.github.com"
        else:
            return f"{self.base_url}/api/v3"

    def _build_url(self, endpoint: str) -> str:
        """Construct the full URL for a given endpoint.

        Args:
            endpoint (str): The API endpoint.

        Returns:
            str: The full URL.

        """
        return f"{self.api_url}/{endpoint.lstrip('/')}"

    def _get_conditional_request_headers(
        self, etag: str | None = None, last_modified: str | None = None
    ) -> dict[str, str]:
        """Get headers for conditional requests.

        Args:
            etag: The ETag value for the resource.
            last_modified: The Last-Modified timestamp for the resource.

        Returns:
            A dictionary of headers for the conditional request.

        """
        headers: dict[str, str] = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        return headers

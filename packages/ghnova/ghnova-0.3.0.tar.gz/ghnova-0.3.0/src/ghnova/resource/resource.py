"""Base class for GitHub API resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from requests import Response

if TYPE_CHECKING:
    from ghnova.client.github import GitHub


class Resource:
    """Base class for GitHub API resources."""

    def __init__(self, client: GitHub) -> None:
        """Initialize the Resource with a GitHub client.

        Args:
            client: An instance of the GitHub client.

        """
        self.client = client

    def _get(self, endpoint: str, **kwargs: Any) -> Response:
        """Perform a GET request.

        Args:
            endpoint: The API endpoint.
            **kwargs: Additional arguments for the request.

        Returns:
            The response object.

        """
        return self.client._request(method="GET", endpoint=endpoint, **kwargs)

    def _post(self, endpoint: str, **kwargs: Any) -> Response:
        """Perform a POST request.

        Args:
            endpoint: The API endpoint.
            **kwargs: Additional arguments for the request.

        Returns:
            The response object.

        """
        return self.client._request(method="POST", endpoint=endpoint, **kwargs)

    def _put(self, endpoint: str, **kwargs: Any) -> Response:
        """Perform a PUT request.

        Args:
            endpoint: The API endpoint.
            **kwargs: Additional arguments for the request.

        Returns:
            The response object.

        """
        return self.client._request(method="PUT", endpoint=endpoint, **kwargs)

    def _delete(self, endpoint: str, **kwargs: Any) -> Response:
        """Perform a DELETE request.

        Args:
            endpoint: The API endpoint.
            **kwargs: Additional arguments for the request.

        Returns:
            The response object.

        """
        return self.client._request(method="DELETE", endpoint=endpoint, **kwargs)

    def _patch(self, endpoint: str, **kwargs: Any) -> Response:
        """Perform a PATCH request.

        Args:
            endpoint: The API endpoint.
            **kwargs: Additional arguments for the request.

        Returns:
            The response object.

        """
        return self.client._request(method="PATCH", endpoint=endpoint, **kwargs)

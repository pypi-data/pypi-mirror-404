"""Asynchronous GitHub API client implementation."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientResponse, ClientSession, ClientTimeout

from ghnova.client.base import Client
from ghnova.issue.async_issue import AsyncIssue
from ghnova.user.async_user import AsyncUser


class AsyncGitHub(Client):
    """Asynchronous GitHub API client."""

    def __init__(self, token: str | None = None, base_url: str = "https://github.com") -> None:
        """Initialize the asynchronous GitHub client.

        Args:
            token: The API token for authentication.
            base_url: The base URL of the GitHub instance.

        """
        super().__init__(token=token, base_url=base_url)
        self.session: ClientSession | None = None
        self.issue = AsyncIssue(client=self)
        self.user = AsyncUser(client=self)

    def __str__(self) -> str:
        """Return a string representation of the AsyncGitHub client.

        Returns:
            str: String representation.

        """
        return f"<AsyncGitHub base_url={self.base_url}>"

    async def __aenter__(self) -> AsyncGitHub:
        """Enter the asynchronous context manager.

        Returns:
            The AsyncGitHub client instance.

        """
        if self.session is not None and not self.session.closed:
            raise RuntimeError("AsyncGitHub session already open; do not re-enter context manager.")
        self.session = ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the asynchronous context manager.

        Args:
            exc_type: The exception type.
            exc_val: The exception value.
            exc_tb: The traceback.

        """
        if self.session:
            await self.session.close()
            self.session = None

    def _get_session(self, headers: dict | None = None, **kwargs: Any) -> ClientSession:
        """Get or create the aiohttp ClientSession.

        Args:
            headers: Optional headers to include in the session.
            **kwargs: Additional arguments for ClientSession.

        Returns:
            The aiohttp ClientSession instance.

        """
        return ClientSession(headers=headers, **kwargs)

    async def _request(  # noqa: PLR0913
        self,
        method: str,
        endpoint: str,
        etag: str | None = None,
        last_modified: str | None = None,
        headers: dict | None = None,
        timeout: int = 30,
        **kwargs: Any,
    ) -> ClientResponse:
        """Make an asynchronous HTTP request to the GitHub API.

        Args:
            method: The HTTP method (GET, POST, etc.).
            endpoint: The API endpoint.
            etag: str | None = None,
            last_modified: str | None = None,
            headers: Optional headers to include in the request.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments for the request.

        Returns:
            The HTTP response.

        """
        if self.session is None:
            raise RuntimeError(
                "AsyncGitHub must be used as an async context manager. "
                + "Use 'async with AsyncGitHub(...) as client:' to ensure proper resource cleanup."
            )

        url = self._build_url(endpoint=endpoint)
        conditional_headers = self._get_conditional_request_headers(etag=etag, last_modified=last_modified)
        request_headers = {**self.headers, **conditional_headers, **(headers or {})}
        timeout_obj = ClientTimeout(total=timeout)
        response = await self.session.request(
            method=method, url=url, headers=request_headers, timeout=timeout_obj, **kwargs
        )
        try:
            response.raise_for_status()
        except Exception:
            response.release()
            raise

        return response

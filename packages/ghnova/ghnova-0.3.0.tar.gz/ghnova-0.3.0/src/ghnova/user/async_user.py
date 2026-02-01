"""Asynchronous User Resource for GitHub API."""

from __future__ import annotations

from typing import Any, cast

from aiohttp import ClientResponse

from ghnova.resource.async_resource import AsyncResource
from ghnova.user.base import BaseUser
from ghnova.utils.response import process_async_response_with_last_modified


class AsyncUser(BaseUser, AsyncResource):
    """GitHub Asynchronous User resource."""

    async def _get_user(
        self,
        username: str | None = None,
        account_id: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """Asynchronously get user information.

        Args:
            username: The username of the user to retrieve. If None, retrieves the authenticated user.
            account_id: The account ID of the user to retrieve. If None, retrieves by username.
            etag: The ETag value for conditional requests.
            last_modified: The Last-Modified timestamp for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            The ClientResponse object.

        """
        endpoint, kwargs = self._get_user_helper(username=username, account_id=account_id, **kwargs)
        return await self._get(endpoint=endpoint, etag=etag, last_modified=last_modified, **kwargs)

    async def get_user(
        self,
        username: str | None = None,
        account_id: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], int, str | None, str | None]:
        """Asynchronously get user information.

        Args:
            username: The username of the user to retrieve. If None, retrieves the authenticated user.
            account_id: The account ID of the user to retrieve. If None, retrieves by username.
            etag: The ETag value for conditional requests.
            last_modified: The Last-Modified timestamp for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - A dictionary with user information (empty if 304 Not Modified).
                - The HTTP status code.
                - The ETag value from the response headers (if present).
                - The Last-Modified timestamp from the response headers (if present).

        """
        response = await self._get_user(
            username=username, account_id=account_id, etag=etag, last_modified=last_modified, **kwargs
        )
        data, status_code, etag_value, last_modified_value = await process_async_response_with_last_modified(response)
        data = cast(dict[str, Any], data)
        return data, status_code, etag_value, last_modified_value

    async def _update_user(  # noqa: PLR0913
        self,
        name: str | None = None,
        email: str | None = None,
        blog: str | None = None,
        twitter_username: str | None = None,
        company: str | None = None,
        location: str | None = None,
        hireable: bool | None = None,
        bio: str | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """Asynchronously update the authenticated user's information.

        Args:
            name: The user's name.
            email: The user's email.
            blog: The user's blog URL.
            twitter_username: The user's Twitter username.
            company: The user's company.
            location: The user's location.
            hireable: Whether the user is available for hire.
            bio: The user's bio.
            etag: The ETag value for conditional requests.
            last_modified: The Last-Modified timestamp for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            The ClientResponse object.

        """
        endpoint, payload, kwargs = self._update_user_helper(
            name=name,
            email=email,
            blog=blog,
            twitter_username=twitter_username,
            company=company,
            location=location,
            hireable=hireable,
            bio=bio,
            **kwargs,
        )
        return await self._patch(endpoint=endpoint, json=payload, etag=etag, last_modified=last_modified, **kwargs)

    async def update_user(  # noqa: PLR0913
        self,
        name: str | None = None,
        email: str | None = None,
        blog: str | None = None,
        twitter_username: str | None = None,
        company: str | None = None,
        location: str | None = None,
        hireable: bool | None = None,
        bio: str | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], int, str | None, str | None]:
        """Asynchronously update the authenticated user's information.

        Args:
            name: The user's name.
            email: The user's email.
            blog: The user's blog URL.
            twitter_username: The user's Twitter username.
            company: The user's company.
            location: The user's location.
            hireable: Whether the user is available for hire.
            bio: The user's bio.
            etag: The ETag value for conditional requests.
            last_modified: The Last-Modified timestamp for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - A dictionary with updated user information.
                - The HTTP status code.
                - The ETag value from the response headers (if present).
                - The Last-Modified timestamp from the response headers (if present).

        """
        response = await self._update_user(
            name=name,
            email=email,
            blog=blog,
            twitter_username=twitter_username,
            company=company,
            location=location,
            hireable=hireable,
            bio=bio,
            etag=etag,
            last_modified=last_modified,
            **kwargs,
        )
        data, status_code, etag, last_modified = await process_async_response_with_last_modified(response)
        data = cast(dict[str, Any], data)
        return data, status_code, etag, last_modified

    async def _list_users(
        self,
        since: int | None = None,
        per_page: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """Asynchronously list all users.

        Args:
            since: The integer ID of the last User that you've seen.
            per_page: The number of results per page (max 100).
            etag: The ETag value for conditional requests.
            last_modified: The Last-Modified timestamp for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            The ClientResponse object.

        """
        endpoint, params, kwargs = self._list_users_helper(since=since, per_page=per_page, **kwargs)
        return await self._get(endpoint=endpoint, params=params, etag=etag, last_modified=last_modified, **kwargs)

    async def list_users(
        self,
        since: int | None = None,
        per_page: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> tuple[list[dict[str, Any]], int, str | None, str | None]:
        """Asynchronously list all users.

        Args:
            since: The integer ID of the last User that you've seen.
            per_page: The number of results per page (max 100).
            etag: The ETag value for conditional requests.
            last_modified: The Last-Modified timestamp for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - A list of user dictionaries (empty if 304 Not Modified).
                - The HTTP status code.
                - The ETag value from the response headers (if present).
                - The Last-Modified timestamp from the response headers (if present).

        """
        response = await self._list_users(
            since=since, per_page=per_page, etag=etag, last_modified=last_modified, **kwargs
        )
        data, status_code, etag_value, last_modified_value = await process_async_response_with_last_modified(response)
        data = cast(list[dict[str, Any]], data)
        return data, status_code, etag_value, last_modified_value

    async def _get_contextual_information(
        self,
        username: str,
        subject_type: str | None = None,
        subject_id: str | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """Asynchronously get contextual information about a user.

        Args:
            username: The username of the user.
            subject_type: The type of subject for the hovercard.
            subject_id: The ID of the subject for the hovercard.
            **kwargs: Additional arguments for the request.

        Returns:
            The ClientResponse object.

        """
        endpoint, params, kwargs = self._get_contextual_information_helper(
            username=username, subject_type=subject_type, subject_id=subject_id, **kwargs
        )
        return await self._get(endpoint=endpoint, params=params, **kwargs)

    async def get_contextual_information(
        self,
        username: str,
        subject_type: str | None = None,
        subject_id: str | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], int, str | None, str | None]:
        """Asynchronously get contextual information about a user.

        Args:
            username: The username of the user.
            subject_type: The type of subject for the hovercard.
            subject_id: The ID of the subject for the hovercard.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - A dictionary with contextual information.
                - The HTTP status code.
                - The ETag value from the response headers (if present).
                - The Last-Modified timestamp from the response headers (if present).

        """
        response = await self._get_contextual_information(
            username=username, subject_type=subject_type, subject_id=subject_id, **kwargs
        )
        data, status_code, etag_value, last_modified_value = await process_async_response_with_last_modified(response)
        data = cast(dict[str, Any], data)
        return data, status_code, etag_value, last_modified_value

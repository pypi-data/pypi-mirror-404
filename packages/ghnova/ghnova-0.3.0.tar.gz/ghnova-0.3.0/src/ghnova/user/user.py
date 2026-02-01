"""GitHub User resource."""

from __future__ import annotations

from typing import Any, cast

from requests import Response

from ghnova.resource.resource import Resource
from ghnova.user.base import BaseUser
from ghnova.utils.response import process_response_with_last_modified


class User(BaseUser, Resource):
    """GitHub User resource."""

    def _get_user(
        self,
        username: str | None = None,
        account_id: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> Response:
        """Get user information.

        Args:
            username: The username of the user to retrieve. If None, retrieves the authenticated user.
            account_id: The account ID of the user to retrieve. If None, retrieves by username.
            etag: The ETag value for conditional requests.
            last_modified: The Last-Modified timestamp for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            The response object.

        """
        endpoint, kwargs = self._get_user_helper(username=username, account_id=account_id, **kwargs)
        return self._get(endpoint=endpoint, etag=etag, last_modified=last_modified, **kwargs)

    def get_user(
        self,
        username: str | None = None,
        account_id: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], int, str | None, str | None]:
        """Get user information.

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
        response = self._get_user(
            username=username, account_id=account_id, etag=etag, last_modified=last_modified, **kwargs
        )
        data, status_code, etag_value, last_modified_value = process_response_with_last_modified(response)
        data = cast(dict[str, Any], data)
        return data, status_code, etag_value, last_modified_value

    def _update_user(  # noqa: PLR0913
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
    ) -> Response:
        """Update the authenticated user's information.

        Args:
            name: The name of the user.
            email: The email of the user.
            blog: The blog URL of the user.
            twitter_username: The Twitter username of the user.
            company: The company of the user.
            location: The location of the user.
            hireable: The hireable status of the user.
            bio: The bio of the user.
            etag: The ETag value for conditional requests.
            last_modified: The Last-Modified timestamp for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            The response object.

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
        return self._patch(endpoint=endpoint, json=payload, etag=etag, last_modified=last_modified, **kwargs)

    def update_user(  # noqa: PLR0913
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
        """Update the authenticated user's information.

        Args:
            name: The name of the user.
            email: The email of the user.
            blog: The blog URL of the user.
            twitter_username: The Twitter username of the user.
            company: The company of the user.
            location: The location of the user.
            hireable: The hireable status of the user.
            bio: The bio of the user.
            etag: The ETag value for conditional requests.
            last_modified: The Last-Modified timestamp for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - A dictionary with updated user information (empty if 304 Not Modified).
                - The HTTP status code.
                - The ETag value from the response headers (if present).
                - The Last-Modified timestamp from the response headers (if present).

        """
        response = self._update_user(
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
        data, status_code, etag_value, last_modified_value = process_response_with_last_modified(response)
        data = cast(dict[str, Any], data)

        return data, status_code, etag_value, last_modified_value

    def _list_users(
        self,
        since: int | None = None,
        per_page: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> Response:
        """List all users.

        Args:
            since: The integer ID of the last User that you've seen.
            per_page: The number of results per page (max 100).
            etag: The ETag value for conditional requests.
            last_modified: The Last-Modified timestamp for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            A response object.

        """
        endpoint, params, kwargs = self._list_users_helper(since=since, per_page=per_page, **kwargs)
        return self._get(endpoint=endpoint, params=params, etag=etag, last_modified=last_modified, **kwargs)

    def list_users(
        self,
        since: int | None = None,
        per_page: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> tuple[list[dict[str, Any]], int, str | None, str | None]:
        """List all users.

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
        response = self._list_users(since=since, per_page=per_page, etag=etag, last_modified=last_modified, **kwargs)
        data, status_code, etag_value, last_modified_value = process_response_with_last_modified(response)
        if status_code == 304:  # noqa: PLR2004
            data = []
        return cast(list[dict[str, Any]], data), status_code, etag_value, last_modified_value

    def _get_contextual_information(
        self,
        username: str,
        subject_type: str | None = None,
        subject_id: str | None = None,
        **kwargs: Any,
    ) -> Response:
        """Get contextual information about a user.

        Args:
            username: The username of the user.
            subject_type: The type of subject for the hovercard.
            subject_id: The ID of the subject for the hovercard.
            **kwargs: Additional arguments for the request.

        Returns:
            The response object.

        """
        endpoint, params, kwargs = self._get_contextual_information_helper(
            username=username, subject_type=subject_type, subject_id=subject_id, **kwargs
        )
        return self._get(endpoint=endpoint, params=params, **kwargs)

    def get_contextual_information(
        self,
        username: str,
        subject_type: str | None = None,
        subject_id: str | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], int, str | None, str | None]:
        """Get contextual information about a user.

        Args:
            username: The username of the user.
            subject_type: The type of subject for the hovercard.
            subject_id: The ID of the subject for the hovercard.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - A dictionary with contextual information about the user.
                - The HTTP status code.
                - The ETag value from the response headers (if present).
                - The Last-Modified timestamp from the response headers (if present).

        """
        response = self._get_contextual_information(
            username=username, subject_type=subject_type, subject_id=subject_id, **kwargs
        )
        data, status_code, etag_value, last_modified_value = process_response_with_last_modified(response)
        data = cast(dict[str, Any], data)
        return data, status_code, etag_value, last_modified_value

"""Base class for GitHub User resource."""

from __future__ import annotations

from typing import Any


class BaseUser:
    """Base class for GitHub User resource."""

    def _get_user_endpoint(self, username: str | None, account_id: int | None) -> str:
        """Determine the user endpoint based on username or account ID.

        Args:
            username: The username of the user.
            account_id: The account ID of the user.

        Returns:
            The API endpoint for the user.

        """
        if username is None and account_id is None:
            return "/user"
        elif username is not None and account_id is None:
            return f"/users/{username}"
        elif username is None and account_id is not None:
            return f"/user/{account_id}"
        else:
            raise ValueError("Specify either username or account_id, not both.")

    def _get_user_helper(
        self, username: str | None = None, account_id: int | None = None, **kwargs: Any
    ) -> tuple[str, dict[str, Any]]:
        """Get user information.

        Args:
            username: The username of the user to retrieve. If None, retrieves the authenticated user.
            account_id: The account ID of the user to retrieve. If None, retrieves by username.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing the endpoint and the request arguments.
                - The API endpoint for the user.
                - A dictionary of request arguments.

        """
        endpoint = self._get_user_endpoint(username=username, account_id=account_id)
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers", {})
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        return endpoint, kwargs

    def _update_user_endpoint(self) -> str:
        """Get the endpoint for updating the authenticated user.

        Returns:
            The API endpoint for updating the authenticated user.

        """
        return "/user"

    def _update_user_helper(  # noqa: PLR0913
        self,
        name: str | None,
        email: str | None,
        blog: str | None,
        twitter_username: str | None,
        company: str | None,
        location: str | None,
        hireable: bool | None,
        bio: str | None,
        **kwargs: Any,
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """Get the endpoint and arguments for updating the authenticated user.

        Args:
            name: The name of the user.
            email: The email of the user.
            blog: The blog URL of the user.
            twitter_username: The Twitter username of the user.
            company: The company of the user.
            location: The location of the user.
            hireable: The hirable status of the user.
            bio: The bio of the user.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing the endpoint and the request arguments.
                - The API endpoint for updating the authenticated user.
                - A dictionary representing the JSON payload.
                - A dictionary of request arguments.

        """
        endpoint = self._update_user_endpoint()
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers", {})
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        payload = {}
        if name is not None:
            payload["name"] = name
        if email is not None:
            payload["email"] = email
        if blog is not None:
            payload["blog"] = blog
        if twitter_username is not None:
            payload["twitter_username"] = twitter_username
        if company is not None:
            payload["company"] = company
        if location is not None:
            payload["location"] = location

        if hireable is not None:
            payload["hireable"] = hireable
        if bio is not None:
            payload["bio"] = bio

        return endpoint, payload, kwargs

    def _list_users_endpoint(self) -> str:
        """Get the endpoint for listing all users.

        Returns:
            The API endpoint for listing all users.

        """
        return "/users"

    def _list_users_helper(
        self, since: int | None, per_page: int | None, **kwargs: Any
    ) -> tuple[str, dict[str, int], dict[str, Any]]:
        """Get the endpoint and arguments for listing all users.

        Args:
            since: The user ID to start from.
            per_page: The number of users per page.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing the endpoint and the request arguments.
                - The API endpoint for listing all users.
                - A dictionary of query parameters.
                - A dictionary of request arguments.

        """
        endpoint = self._list_users_endpoint()
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers", {})
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        params = {}
        if since is not None:
            params["since"] = since
        if per_page is not None:
            params["per_page"] = per_page

        return endpoint, params, kwargs

    def _get_contextual_information_endpoint(self) -> str:
        """Get the endpoint for retrieving contextual information about the authenticated user.

        Returns:
            The API endpoint for retrieving contextual information.

        """
        return "/users/{username}/hovercard"

    def _get_contextual_information_helper(
        self, username: str, subject_type: str | None = None, subject_id: str | None = None, **kwargs: Any
    ) -> tuple[str, dict[str, str], dict[str, Any]]:
        """Get the endpoint and arguments for retrieving contextual information about a user.

        Args:
            username: The username of the user.
            subject_type: The type of subject for the hovercard.
            subject_id: The ID of the subject for the hovercard.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing the endpoint and the request arguments.
                - The API endpoint for retrieving contextual information.
                - A dictionary of query parameters.
                - A dictionary of request arguments.

        """
        endpoint = self._get_contextual_information_endpoint().format(username=username)
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers", {})
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        params = {}
        if subject_type is not None:
            params["subject_type"] = subject_type
        if subject_id is not None:
            params["subject_id"] = subject_id

        return endpoint, params, kwargs

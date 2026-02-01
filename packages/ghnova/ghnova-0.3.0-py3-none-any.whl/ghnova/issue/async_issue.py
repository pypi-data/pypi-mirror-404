"""Asynchronous issue handling module."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, cast

from aiohttp import ClientResponse

from ghnova.issue.base import BaseIssue
from ghnova.resource.async_resource import AsyncResource
from ghnova.utils.response import process_async_response_with_last_modified


class AsyncIssue(BaseIssue, AsyncResource):
    """GitHub Asynchronous Issue resource class."""

    async def _list_issues(  # noqa: PLR0913
        self,
        owner: str | None = None,
        organization: str | None = None,
        repository: str | None = None,
        filter_by: Literal["assigned", "created", "mentioned", "subscribed", "all"] | None = None,
        state: Literal["open", "closed", "all"] | None = None,
        labels: list[str] | None = None,
        sort: Literal["created", "updated", "comments"] | None = None,
        direction: Literal["asc", "desc"] | None = None,
        since: datetime | None = None,
        collab: bool | None = None,
        orgs: bool | None = None,
        owned: bool | None = None,
        pulls: bool | None = None,
        issue_type: str | None = None,
        milestone: str | None = None,
        assignee: str | None = None,
        creator: str | None = None,
        mentioned: str | None = None,
        per_page: int = 30,
        page: int = 1,
        **kwargs: Any,
    ) -> ClientResponse:
        """List issues with various filtering and sorting options.

        Supported scenarios:

        - Authenticated user: Do not provide owner, organization, or repository.
        - Organization issues: Provide organization, but not owner or repository.
        - Repository issues: Provide owner or organization along with repository.

        Args:
            owner: The owner of the repository.
            organization: The organization name.
            repository: The repository name.
            filter_by: Filter issues by criteria.
            state: The state of the issues to return.
            labels: A list of labels to filter issues by.
            sort: The field to sort issues by.
            direction: The direction of the sort.
            since: Only issues updated at or after this time are returned.
            collab: Include issues from repositories the user collaborates on (for authenticated user issues).
            orgs: Include issues from organizations the user is a member of (for authenticated user issues).
            owned: Include issues from repositories owned by the user (for authenticated user issues).
            pulls: Include pull requests in the issues list (for authenticated user issues).
            issue_type: The type of issues to filter by (for organization issues).
            milestone: Filter issues by milestone (for repository issues).
            assignee: Filter issues by assignee (for repository issues).
            creator: Filter issues by creator (for repository issues).
            mentioned: Filter issues by mentioned user (for repository issues).
            per_page: The number of issues per page.
            page: The page number to retrieve.
            **kwargs: Additional arguments for the request.

        Returns:
            The ClientResponse object containing the list of issues.

        """
        endpoint, params, kwargs = self._list_issues_helper(
            owner=owner,
            organization=organization,
            repository=repository,
            filter_by=filter_by,
            state=state,
            labels=labels,
            sort=sort,
            direction=direction,
            since=since,
            collab=collab,
            orgs=orgs,
            owned=owned,
            pulls=pulls,
            issue_type=issue_type,
            milestone=milestone,
            assignee=assignee,
            creator=creator,
            mentioned=mentioned,
            per_page=per_page,
            page=page,
            **kwargs,
        )
        return await self._get(endpoint=endpoint, params=params, **kwargs)

    async def list_issues(  # noqa: PLR0913
        self,
        owner: str | None = None,
        organization: str | None = None,
        repository: str | None = None,
        filter_by: Literal["assigned", "created", "mentioned", "subscribed", "all"] | None = None,
        state: Literal["open", "closed", "all"] | None = None,
        labels: list[str] | None = None,
        sort: Literal["created", "updated", "comments"] | None = None,
        direction: Literal["asc", "desc"] | None = None,
        since: datetime | None = None,
        collab: bool | None = None,
        orgs: bool | None = None,
        owned: bool | None = None,
        pulls: bool | None = None,
        issue_type: str | None = None,
        milestone: str | None = None,
        assignee: str | None = None,
        creator: str | None = None,
        mentioned: str | None = None,
        per_page: int = 30,
        page: int = 1,
        **kwargs: Any,
    ) -> tuple[list[dict[str, Any]], int, str | None, str | None]:
        """List issues with various filtering and sorting options.

        Supported scenarios:

        - Authenticated user: Do not provide owner, organization, or repository.
        - Organization issues: Provide organization, but not owner or repository.
        - Repository issues: Provide owner or organization along with repository.

        Args:
            owner: The owner of the repository.
            organization: The organization name.
            repository: The repository name.
            filter_by: Filter issues by criteria.
            state: The state of the issues to return.
            labels: A list of labels to filter issues by.
            sort: The field to sort issues by.
            direction: The direction of the sort.
            since: Only issues updated at or after this time are returned.
            collab: Include issues from repositories the user collaborates on (for authenticated user issues).
            orgs: Include issues from organizations the user is a member of (for authenticated user issues).
            owned: Include issues from repositories owned by the user (for authenticated user issues).
            pulls: Include pull requests in the issues list (for authenticated user issues).
            issue_type: The type of issues to filter by (for organization issues).
            milestone: Filter issues by milestone (for repository issues).
            assignee: Filter issues by assignee (for repository issues).
            creator: Filter issues by creator (for repository issues).
            mentioned: Filter issues by mentioned user (for repository issues).
            per_page: The number of issues per page.
            page: The page number to retrieve.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - A list of issues as dictionaries.
                - The HTTP status code of the response.
                - The ETag value from the response headers (if present).
                - The Last-Modified value from the response headers (if present).

        """
        response = await self._list_issues(
            owner=owner,
            organization=organization,
            repository=repository,
            filter_by=filter_by,
            state=state,
            labels=labels,
            sort=sort,
            direction=direction,
            since=since,
            collab=collab,
            orgs=orgs,
            owned=owned,
            pulls=pulls,
            issue_type=issue_type,
            milestone=milestone,
            assignee=assignee,
            creator=creator,
            mentioned=mentioned,
            per_page=per_page,
            page=page,
            **kwargs,
        )
        data, status_code, etag_value, last_modified_value = await process_async_response_with_last_modified(response)
        return cast(list[dict[str, Any]], data), status_code, etag_value, last_modified_value

    async def _create_issue(  # noqa: PLR0913
        self,
        owner: str,
        repository: str,
        title: str,
        body: str | None = None,
        assignee: str | None = None,
        milestone: str | int | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        issue_type: str | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """Create a new issue in a repository.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            title: The title of the issue.
            body: The body content of the issue.
            assignee: The username of the assignee.
            milestone: The milestone number or title to associate with the issue.
            labels: A list of labels to assign to the issue.
            assignees: A list of usernames to assign to the issue.
            issue_type: The type of issue.
            **kwargs: Additional arguments for the request.

        Returns:
            The ClientResponse object containing the created issue.

        """
        endpoint, payload, kwargs = self._create_issue_helper(
            owner=owner,
            repository=repository,
            title=title,
            body=body,
            assignee=assignee,
            milestone=milestone,
            labels=labels,
            assignees=assignees,
            issue_type=issue_type,
            **kwargs,
        )
        return await self._post(endpoint=endpoint, json=payload, **kwargs)

    async def create_issue(  # noqa: PLR0913
        self,
        owner: str,
        repository: str,
        title: str,
        body: str | None = None,
        assignee: str | None = None,
        milestone: str | int | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        issue_type: str | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], int, str | None, str | None]:
        """Create a new issue in a repository.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            title: The title of the issue.
            body: The body content of the issue.
            assignee: The username of the assignee.
            milestone: The milestone number or title to associate with the issue.
            labels: A list of labels to assign to the issue.
            assignees: A list of usernames to assign to the issue.
            issue_type: The type of issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - The created issue as a dictionary.
                - The HTTP status code of the response.
                - The ETag value from the response headers (if present).
                - The Last-Modified value from the response headers (if present).

        """
        response = await self._create_issue(
            owner=owner,
            repository=repository,
            title=title,
            body=body,
            assignee=assignee,
            milestone=milestone,
            labels=labels,
            assignees=assignees,
            issue_type=issue_type,
            **kwargs,
        )
        data, status_code, etag_value, last_modified_value = await process_async_response_with_last_modified(response)
        return cast(dict[str, Any], data), status_code, etag_value, last_modified_value

    async def _get_issue(self, owner: str, repository: str, issue_number: int, **kwargs: Any) -> ClientResponse:
        """Get a specific issue by its number.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            The ClientResponse object containing the issue.

        """
        endpoint, kwargs = self._get_issue_helper(
            owner=owner,
            repository=repository,
            issue_number=issue_number,
            **kwargs,
        )
        return await self._get(endpoint=endpoint, **kwargs)

    async def get_issue(
        self, owner: str, repository: str, issue_number: int, **kwargs: Any
    ) -> tuple[dict[str, Any], int, str | None, str | None]:
        """Get a specific issue by its number.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - The issue as a dictionary.
                - The HTTP status code of the response.
                - The ETag value from the response headers (if present).
                - The Last-Modified value from the response headers (if present).

        """
        response = await self._get_issue(
            owner=owner,
            repository=repository,
            issue_number=issue_number,
            **kwargs,
        )
        data, status_code, etag_value, last_modified_value = await process_async_response_with_last_modified(response)
        return cast(dict[str, Any], data), status_code, etag_value, last_modified_value

    async def _update_issue(  # noqa: PLR0913
        self,
        owner: str,
        repository: str,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        assignee: str | None = None,
        milestone: str | int | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        state: Literal["open", "closed"] | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """Update an existing issue in a repository.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            title: The new title of the issue.
            body: The new body content of the issue.
            assignee: The username of the new assignee.
            milestone: The new milestone number or title to associate with the issue.
            labels: A new list of labels to assign to the issue.
            assignees: A new list of usernames to assign to the issue.
            state: The new state of the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A Response object from the API call.

        """
        endpoint, payload, kwargs = self._update_issue_helper(
            owner=owner,
            repository=repository,
            issue_number=issue_number,
            title=title,
            body=body,
            assignee=assignee,
            milestone=milestone,
            labels=labels,
            assignees=assignees,
            state=state,
            **kwargs,
        )
        return await self._patch(endpoint=endpoint, json=payload, **kwargs)

    async def update_issue(  # noqa: PLR0913
        self,
        owner: str,
        repository: str,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        assignee: str | None = None,
        milestone: str | int | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        state: Literal["open", "closed"] | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], int, str | None, str | None]:
        """Update an existing issue in a repository.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            title: The new title of the issue.
            body: The new body content of the issue.
            assignee: The username of the new assignee.
            milestone: The new milestone number or title to associate with the issue.
            labels: A new list of labels to assign to the issue.
            assignees: A new list of usernames to assign to the issue.
            state: The new state of the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - The updated issue as a dictionary.
                - The HTTP status code of the response.
                - The ETag value from the response headers (if present).
                - The Last-Modified value from the response headers (if present).

        """
        response = await self._update_issue(
            owner=owner,
            repository=repository,
            issue_number=issue_number,
            title=title,
            body=body,
            assignee=assignee,
            milestone=milestone,
            labels=labels,
            assignees=assignees,
            state=state,
            **kwargs,
        )
        data, status_code, etag_value, last_modified_value = await process_async_response_with_last_modified(response)
        return cast(dict[str, Any], data), status_code, etag_value, last_modified_value

    async def _lock_issue(
        self,
        owner: str,
        repository: str,
        issue_number: int,
        lock_reason: Literal["off-topic", "too heated", "resolved", "spam"] | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """Lock an issue to prevent further comments.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            lock_reason: The reason for locking the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A ClientResponse object from the API call.

        """
        endpoint, payload, kwargs = self._lock_issue_helper(
            owner=owner,
            repository=repository,
            issue_number=issue_number,
            lock_reason=lock_reason,
            **kwargs,
        )
        return await self._put(endpoint=endpoint, json=payload, **kwargs)

    async def lock_issue(
        self,
        owner: str,
        repository: str,
        issue_number: int,
        lock_reason: Literal["off-topic", "too heated", "resolved", "spam"] | None = None,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], int, str | None, str | None]:
        """Lock an issue to prevent further comments.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            lock_reason: The reason for locking the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - An empty dictionary for 204 No Content responses.
                - The HTTP status code of the response.
                - The ETag value from the response headers (if present).
                - The Last-Modified value from the response headers (if present).

        """
        response = await self._lock_issue(
            owner=owner,
            repository=repository,
            issue_number=issue_number,
            lock_reason=lock_reason,
            **kwargs,
        )
        data, status_code, etag_value, last_modified_value = await process_async_response_with_last_modified(response)
        return cast(dict[str, Any], data), status_code, etag_value, last_modified_value

    async def _unlock_issue(self, owner: str, repository: str, issue_number: int, **kwargs: Any) -> ClientResponse:
        """Unlock a previously locked issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A ClientResponse object from the API call.

        """
        endpoint, kwargs = self._unlock_issue_helper(
            owner=owner,
            repository=repository,
            issue_number=issue_number,
            **kwargs,
        )
        return await self._delete(endpoint=endpoint, **kwargs)

    async def unlock_issue(
        self, owner: str, repository: str, issue_number: int, **kwargs: Any
    ) -> tuple[dict[str, Any], int, str | None, str | None]:
        """Unlock a previously locked issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - An empty dictionary for 204 No Content responses.
                - The HTTP status code of the response.
                - The ETag value from the response headers (if present).
                - The Last-Modified value from the response headers (if present).

        """
        response = await self._unlock_issue(
            owner=owner,
            repository=repository,
            issue_number=issue_number,
            **kwargs,
        )
        data, status_code, etag_value, last_modified_value = await process_async_response_with_last_modified(response)
        return cast(dict[str, Any], data), status_code, etag_value, last_modified_value

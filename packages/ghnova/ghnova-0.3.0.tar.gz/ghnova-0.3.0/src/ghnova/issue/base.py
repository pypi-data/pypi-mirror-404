"""Base class for GitHub Issue resource."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Literal

logger = logging.getLogger("ghnova")


class BaseIssue:
    """Base class for GitHub Issue resource."""

    def _list_issues_endpoint(
        self, owner: str | None = None, organization: str | None = None, repository: str | None = None
    ) -> tuple[str, str]:
        """Determine the issues listing endpoint based on owner, organization, and repository.

        Args:
            owner: The owner of the repository.
            organization: The organization name.
            repository: The repository name.

        Returns:
            A tuple containing the API endpoint for listing issues and a description of the issue type.

        """
        if owner is None and organization is None and repository is None:
            return "/issues", "authenticated user issues"
        if owner is None and organization is not None and repository is None:
            return f"/orgs/{organization}/issues", "organization issues"
        if (owner is not None or organization is not None) and repository is not None:
            repo_owner = owner if owner is not None else organization
            return f"/repos/{repo_owner}/{repository}/issues", "repository issues"
        raise ValueError("Invalid combination of owner, organization, and repository parameters.")

    def _list_issues_helper(  # noqa: PLR0912, PLR0913, PLR0915
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
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
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

        """
        endpoint, endpoint_type = self._list_issues_endpoint(
            owner=owner, organization=organization, repository=repository
        )
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers", {})
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        params: dict[str, str | int | bool] = {}
        # Add the common query parameters
        if state is not None:
            params["state"] = state
        if labels is not None:
            params["labels"] = ",".join(labels)
        if sort is not None:
            params["sort"] = sort
        if direction is not None:
            params["direction"] = direction
        if since is not None:
            params["since"] = since.isoformat()
        if per_page is not None:
            params["per_page"] = per_page
        if page is not None:
            params["page"] = page

        # Add specific query parameters based on issue type
        if endpoint_type == "authenticated user issues":
            if filter_by is not None:
                params["filter"] = filter_by
            if collab is not None:
                params["collab"] = collab
            if orgs is not None:
                params["orgs"] = orgs
            if owned is not None:
                params["owned"] = owned
            if pulls is not None:
                params["pulls"] = pulls
            if issue_type is not None:
                logger.warning("The 'issue_type' parameter is ignored for authenticated user issues.")
            if milestone is not None:
                logger.warning("The 'milestone' parameter is ignored for authenticated user issues.")
            if assignee is not None:
                logger.warning("The 'assignee' parameter is ignored for authenticated user issues.")
            if creator is not None:
                logger.warning("The 'creator' parameter is ignored for authenticated user issues.")
            if mentioned is not None:
                logger.warning("The 'mentioned' parameter is ignored for authenticated user issues.")
        elif endpoint_type == "organization issues":
            if filter_by is not None:
                params["filter"] = filter_by
            if issue_type is not None:
                params["type"] = issue_type
            if collab is not None:
                logger.warning("The 'collab' parameter is ignored for organization issues.")
            if orgs is not None:
                logger.warning("The 'orgs' parameter is ignored for organization issues.")
            if owned is not None:
                logger.warning("The 'owned' parameter is ignored for organization issues.")
            if pulls is not None:
                logger.warning("The 'pulls' parameter is ignored for organization issues.")
            if milestone is not None:
                logger.warning("The 'milestone' parameter is ignored for organization issues.")
            if assignee is not None:
                logger.warning("The 'assignee' parameter is ignored for organization issues.")
            if creator is not None:
                logger.warning("The 'creator' parameter is ignored for organization issues.")
            if mentioned is not None:
                logger.warning("The 'mentioned' parameter is ignored for organization issues.")
        elif endpoint_type == "repository issues":
            if milestone is not None:
                params["milestone"] = milestone
            if assignee is not None:
                params["assignee"] = assignee
            if creator is not None:
                params["creator"] = creator
            if mentioned is not None:
                params["mentioned"] = mentioned
            if filter_by is not None:
                logger.warning("The 'filter_by' parameter is ignored for repository issues.")
            if collab is not None:
                logger.warning("The 'collab' parameter is ignored for repository issues.")
            if orgs is not None:
                logger.warning("The 'orgs' parameter is ignored for repository issues.")
            if owned is not None:
                logger.warning("The 'owned' parameter is ignored for repository issues.")
            if pulls is not None:
                logger.warning("The 'pulls' parameter is ignored for repository issues.")
            if issue_type is not None:
                logger.warning("The 'issue_type' parameter is ignored for repository issues.")
        else:
            raise ValueError(f"Invalid endpoint type determined: {endpoint_type}")

        return endpoint, params, kwargs

    def _create_issue_endpoint(self, owner: str, repository: str) -> str:
        """Get the endpoint for creating an issue in a repository.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.

        Returns:
            The API endpoint for creating an issue.

        """
        return f"/repos/{owner}/{repository}/issues"

    def _create_issue_helper(  # noqa: PLR0913
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
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """Prepare the endpoint and payload for creating a new issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            title: The title of the issue.
            body: The body content of the issue.
            assignee: The assignee of the issue.
            milestone: The milestone number or title for the issue.
            labels: A list of labels to assign to the issue.
            assignees: A list of assignees for the issue.
            issue_type: The type of the issue.
            **kwargs: Additional arguments for the request.

        """
        endpoint = self._create_issue_endpoint(owner=owner, repository=repository)
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers", {})
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        payload: dict[str, str | int | list[str]] = {"title": title}
        if body is not None:
            payload["body"] = body
        if assignee is not None:
            payload["assignee"] = assignee
        if milestone is not None:
            payload["milestone"] = milestone
        if labels is not None:
            payload["labels"] = labels
        if assignees is not None:
            payload["assignees"] = assignees
        if issue_type is not None:
            payload["type"] = issue_type

        return endpoint, payload, kwargs

    def _get_issue_endpoint(self, owner: str, repository: str, issue_number: int) -> str:
        """Get the endpoint for a specific issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.

        Returns:
            The API endpoint for the specific issue.

        """
        return f"/repos/{owner}/{repository}/issues/{issue_number}"

    def _get_issue_helper(
        self, owner: str, repository: str, issue_number: int, **kwargs: Any
    ) -> tuple[str, dict[str, Any]]:
        """Prepare the endpoint and arguments for retrieving a specific issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing the endpoint and request arguments.

        """
        endpoint = self._get_issue_endpoint(owner=owner, repository=repository, issue_number=issue_number)
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers", {})
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        return endpoint, kwargs

    def _update_issue_endpoint(self, owner: str, repository: str, issue_number: int) -> str:
        """Get the endpoint for updating a specific issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.

        Returns:
            The API endpoint for updating the specific issue.

        """
        return f"/repos/{owner}/{repository}/issues/{issue_number}"

    def _update_issue_helper(  # noqa: PLR0913
        self,
        owner: str,
        repository: str,
        issue_number: int,
        title: str | None = None,
        body: str | None = None,
        assignee: str | None = None,
        state: Literal["open", "closed"] | None = None,
        state_reason: Literal["completed", "not_planned", "duplicate", "reopened", "null"] | None = None,
        milestone: str | int | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
        issue_type: str | None = None,
        **kwargs: Any,
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """Prepare the endpoint and payload for updating a specific issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            title: The new title of the issue.
            body: The new body content of the issue.
            assignee: The new assignee of the issue.
            state: The new state of the issue.
            state_reason: The reason for the state change.
            milestone: The new milestone number or title for the issue.
            labels: A new list of labels to assign to the issue.
            assignees: A new list of assignees for the issue.
            issue_type: The new type of the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing the endpoint, payload, and request arguments.

        """
        endpoint = self._update_issue_endpoint(owner=owner, repository=repository, issue_number=issue_number)
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers", {})
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        if assignee is not None:
            payload["assignee"] = assignee
        if state is not None:
            payload["state"] = state
        if state_reason is not None:
            payload["state_reason"] = state_reason
        if milestone is not None:
            payload["milestone"] = milestone
        if labels is not None:
            payload["labels"] = labels
        if assignees is not None:
            payload["assignees"] = assignees
        if issue_type is not None:
            payload["type"] = issue_type

        return endpoint, payload, kwargs

    def _lock_issue_endpoint(self, owner: str, repository: str, issue_number: int) -> str:
        """Get the endpoint for locking a specific issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.

        Returns:
            The API endpoint for locking the specific issue.

        """
        return f"/repos/{owner}/{repository}/issues/{issue_number}/lock"

    def _lock_issue_helper(
        self,
        owner: str,
        repository: str,
        issue_number: int,
        lock_reason: Literal["off-topic", "too heated", "resolved", "spam"] | None = None,
        **kwargs: Any,
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """Prepare the endpoint and payload for locking a specific issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            lock_reason: The reason for locking the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing the endpoint, payload, and request arguments.

        """
        endpoint = self._lock_issue_endpoint(owner, repository, issue_number)
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers", {})
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        payload = {"lock_reason": lock_reason} if lock_reason is not None else {}

        return endpoint, payload, kwargs

    def _unlock_issue_endpoint(self, owner: str, repository: str, issue_number: int) -> str:
        """Get the endpoint for unlocking a specific issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.

        Returns:
            The API endpoint for unlocking the specific issue.

        """
        return f"/repos/{owner}/{repository}/issues/{issue_number}/lock"

    def _unlock_issue_helper(
        self,
        owner: str,
        repository: str,
        issue_number: int,
        **kwargs: Any,
    ) -> tuple[str, dict[str, Any]]:
        """Prepare the endpoint and arguments for unlocking a specific issue.

        Args:
            owner: The owner of the repository.
            repository: The name of the repository.
            issue_number: The number of the issue.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing the endpoint and request arguments.

        """
        endpoint = self._unlock_issue_endpoint(owner, repository, issue_number)
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers", {})
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        return endpoint, kwargs

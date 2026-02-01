"""Base class for GitHub Repository resource."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Literal

logger = logging.getLogger("ghnova")


class BaseRepository:
    """Base class for GitHub Repository resource."""

    def _list_repositories_endpoint(self, owner: str | None = None, organization: str | None = None) -> tuple[str, str]:
        """Determine the repositories endpoint based on owner or organization.

        If both owner and organization are None, returns the authenticated user's repositories.
        If owner is provided, returns that user's repositories.
        If organization is provided, returns that organization's repositories.

        Args:
            owner: The owner of the repositories.
            organization: The organization of the repositories.

        Returns:
            The API endpoint for the repositories and a description.

        """
        if owner is None and organization is None:
            return "/user/repos", "authenticated user's repositories"
        if owner is not None and organization is None:
            return f"/users/{owner}/repos", "user's repositories"
        if owner is None and organization is not None:
            return f"/orgs/{organization}/repos", "organization's repositories"
        raise ValueError("Specify either owner or organization, not both.")

    def _list_repositories_helper(  # noqa: PLR0912, PLR0913
        self,
        owner: str | None = None,
        organization: str | None = None,
        visibility: Literal["all", "public", "private"] | None = None,
        affiliation: list[Literal["owner", "collaborator", "organization_member"]] | None = None,
        repository_type: Literal["all", "owner", "public", "private", "member"] | None = None,
        sort: Literal["created", "updated", "pushed", "full_name"] | None = None,
        direction: Literal["asc", "desc"] | None = None,
        per_page: int = 30,
        page: int = 1,
        since: datetime | None = None,
        before: datetime | None = None,
        **kwargs: Any,
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """List repositories information.

        Args:
            owner: The owner of the repositories to retrieve. If None, retrieves the authenticated user's repositories.
            organization: The organization of the repositories to retrieve. If None, retrieves by owner.
            visibility: The visibility of the repositories. Can be one of "all", "public", or "private".
            affiliation: A list of affiliations for the repositories. Can include "owner", "collaborator", and/or "organization_member".
            repository_type: The type of repositories to retrieve. Can be one of "all", "owner", "public", "private", or "member".
            sort: The field to sort the repositories by. Can be one of "created", "updated", "pushed", or "full_name".
            direction: The direction to sort the repositories. Can be either "asc" or "desc".
            per_page: The number of repositories to return per page.
            page: The page number to retrieve.
            since: A datetime to filter repositories updated after this time.
            before: A datetime to filter repositories updated before this time.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing the endpoint and the request arguments.

                - The API endpoint for the repositories.
                - The query parameters for the request.
                - A dictionary of request arguments.

        """
        endpoint, description = self._list_repositories_endpoint(owner=owner, organization=organization)
        default_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        headers = kwargs.get("headers") or {}
        headers = {**default_headers, **headers}
        kwargs["headers"] = headers

        params = {}
        if visibility is not None:
            if description != "authenticated user's repositories":
                logger.warning(
                    "The 'visibility' parameter is not applicable when listing an organization's repositories."
                )
            else:
                params["visibility"] = visibility
        if affiliation is not None:
            if description != "authenticated user's repositories":
                logger.warning(
                    "The 'affiliation' parameter is only applicable when listing the authenticated user's repositories."
                )
            else:
                params["affiliation"] = ",".join(affiliation)
        if repository_type is not None:
            params["type"] = repository_type
        if sort is not None:
            params["sort"] = sort
        if direction is not None:
            params["direction"] = direction
        params["per_page"] = per_page
        params["page"] = page

        extra_params = kwargs.pop("params", {})
        params = {**params, **extra_params}

        if since is not None:
            if description != "authenticated user's repositories":
                logger.warning("The 'since' parameter is not applicable when listing an organization's repositories.")
            else:
                params["since"] = since.isoformat()
        if before is not None:
            if description != "authenticated user's repositories":
                logger.warning("The 'before' parameter is not applicable when listing an organization's repositories.")
            else:
                params["before"] = before.isoformat()

        return endpoint, params, kwargs

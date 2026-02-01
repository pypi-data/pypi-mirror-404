"""Asynchronous GitHub Repository resource."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, cast

from aiohttp import ClientResponse

from ghnova.repository.base import BaseRepository
from ghnova.resource.async_resource import AsyncResource
from ghnova.utils.response import process_async_response_with_last_modified


class AsyncRepository(BaseRepository, AsyncResource):
    """GitHub Repository resource."""

    async def _list_repositories(  # noqa: PLR0913
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
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """List repositories information.

        Args:
            owner: The owner of the repositories to retrieve. If None, retrieves the authenticated user's repositories.
            organization: The organization of the repositories to retrieve. If None, retrieves by owner.
            visibility: The visibility of the repositories. Can be one of "all", "public", or "private".
            affiliation: A list of affiliations for the repositories. Can include "owner", "collaborator", and/or "organization_member".
            repository_type: The type of repositories to retrieve. Can be one of "all", "owner", "public", "private", or "member".
            sort: The field to sort the repositories by. Can be one of "created", "updated", "pushed", or "full_name".
            direction: The direction to sort the repositories. Can be either "asc" or "desc".
            per_page: The number of results per page (max 100).
            page: The page number of the results to fetch.
            since: Only show repositories updated after this time.
            before: Only show repositories updated before this time.
            etag: The ETag header value for conditional requests.
            last_modified: The Last-Modified header value for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            The ClientResponse object containing the list of repositories.

        """
        endpoint, params, kwargs = self._list_repositories_helper(
            owner=owner,
            organization=organization,
            visibility=visibility,
            affiliation=affiliation,
            repository_type=repository_type,
            sort=sort,
            direction=direction,
            per_page=per_page,
            page=page,
            since=since,
            before=before,
            **kwargs,
        )
        return await self._get(endpoint, params=params, etag=etag, last_modified=last_modified, **kwargs)

    async def list_repositories(  # noqa: PLR0913
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
        etag: str | None = None,
        last_modified: str | None = None,
        **kwargs: Any,
    ) -> tuple[list[dict[str, Any]], int, str | None, str | None]:
        """List repositories information.

        Args:
            owner: The owner of the repositories to retrieve. If None, retrieves the authenticated user's repositories.
            organization: The organization of the repositories to retrieve. If None, retrieves by owner.
            visibility: The visibility of the repositories. Can be one of "all", "public", or "private".
            affiliation: A list of affiliations for the repositories. Can include "owner", "collaborator", and/or "organization_member".
            repository_type: The type of repositories to retrieve. Can be one of "all", "owner", "public", "private", or "member".
            sort: The field to sort the repositories by. Can be one of "created", "updated", "pushed", or "full_name".
            direction: The direction to sort the repositories. Can be either "asc" or "desc".
            per_page: The number of results per page (max 100).
            page: The page number of the results to fetch.
            since: Only show repositories updated after this time.
            before: Only show repositories updated before this time.
            etag: The ETag header value for conditional requests.
            last_modified: The Last-Modified header value for conditional requests.
            **kwargs: Additional arguments for the request.

        Returns:
            A tuple containing:

                - A list of dictionaries representing the repositories.
                - The HTTP status code of the response.
                - The ETag header value from the response, if available.
                - The Last-Modified header value from the response, if available.

        """
        response = await self._list_repositories(
            owner=owner,
            organization=organization,
            visibility=visibility,
            affiliation=affiliation,
            repository_type=repository_type,
            sort=sort,
            direction=direction,
            per_page=per_page,
            page=page,
            since=since,
            before=before,
            etag=etag,
            last_modified=last_modified,
            **kwargs,
        )
        data, status_code, etag_value, last_modified_value = await process_async_response_with_last_modified(response)
        return cast(list[dict[str, Any]], data), status_code, etag_value, last_modified_value

"""List command for repository CLI."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

import typer


def list_command(  # noqa: PLR0913
    ctx: typer.Context,
    owner: Annotated[
        str | None,
        typer.Option(
            "--owner",
            help="The owner of the repositories.",
        ),
    ] = None,
    organization: Annotated[
        str | None,
        typer.Option(
            "--organization",
            help="The organization name.",
        ),
    ] = None,
    visibility: Annotated[
        Literal["all", "public", "private"] | None,
        typer.Option(
            "--visibility",
            help="Filter by visibility: all, public, or private.",
        ),
    ] = None,
    affiliation: Annotated[
        list[str] | None,
        typer.Option(
            "--affiliation",
            help="Filter by affiliation: owner, collaborator, organization_member.",
        ),
    ] = None,
    repository_type: Annotated[
        Literal["all", "owner", "public", "private", "member"] | None,
        typer.Option(
            "--type",
            help="Filter by repository type: all, owner, public, private, or member.",
        ),
    ] = None,
    sort: Annotated[
        Literal["created", "updated", "pushed", "full_name"] | None,
        typer.Option(
            "--sort",
            help="Sort by: created, updated, pushed, or full_name.",
        ),
    ] = None,
    direction: Annotated[
        Literal["asc", "desc"] | None,
        typer.Option(
            "--direction",
            help="Sort direction: asc or desc.",
        ),
    ] = None,
    per_page: Annotated[
        int,
        typer.Option(
            "--per-page",
            help="Number of results per page.",
        ),
    ] = 30,
    page: Annotated[
        int,
        typer.Option(
            "--page",
            help="Page number for pagination.",
        ),
    ] = 1,
    since: Annotated[
        datetime | None,
        typer.Option(
            "--since",
            help="Only show repositories updated after this time (ISO 8601 format).",
        ),
    ] = None,
    before: Annotated[
        datetime | None,
        typer.Option(
            "--before",
            help="Only show repositories updated before this time (ISO 8601 format).",
        ),
    ] = None,
    etag: Annotated[
        str | None,
        typer.Option(
            "--etag",
            help="ETag header value for conditional requests.",
        ),
    ] = None,
    last_modified: Annotated[
        str | None,
        typer.Option(
            "--last-modified",
            help="Last-Modified header value for conditional requests.",
        ),
    ] = None,
    account_name: Annotated[
        str | None,
        typer.Option(
            "--account-name",
            help="Name of the account to use for authentication.",
        ),
    ] = None,
    token: Annotated[
        str | None,
        typer.Option(
            "--token",
            help="Token for authentication. If not provided, the token from the specified account will be used.",
        ),
    ] = None,
    base_url: Annotated[
        str | None,
        typer.Option(
            "--base-url",
            help="Base URL of the GitHub platform. If not provided, the base URL from the specified account will be used.",
        ),
    ] = None,
) -> None:
    """List repositories.

    Args:
        ctx: Typer context.
        owner: The owner of the repositories.
        organization: The organization name.
        visibility: Filter by visibility: all, public, or private.
        affiliation: Filter by affiliation: owner, collaborator, or organization_member.
        repository_type: Filter by repository type: all, owner, public, private, or member.
        sort: Sort by: created, updated, pushed, or full_name.
        direction: Sort direction: asc or desc.
        per_page: Number of results per page.
        page: Page number for pagination.
        since: Only show repositories updated after this time.
        before: Only show repositories updated before this time.
        etag: ETag header value for conditional requests.
        last_modified: Last-Modified header value for conditional requests.
        account_name: Name of the account to use for authentication.
        token: Token for authentication.
        base_url: Base URL of the GitHub platform.

    """
    import json  # noqa: PLC0415
    import logging  # noqa: PLC0415
    from typing import cast  # noqa: PLC0415

    from ghnova.cli.utils.auth import get_auth_params  # noqa: PLC0415
    from ghnova.client.github import GitHub  # noqa: PLC0415

    logger = logging.getLogger("ghnova")

    token, base_url = get_auth_params(
        config_path=ctx.obj["config_path"],
        account_name=account_name,
        token=token,
        base_url=base_url,
    )
    affiliation_list = None
    if affiliation:
        if not all(a in {"owner", "collaborator", "organization_member"} for a in affiliation):
            logger.error(
                "Invalid affiliation value. Must be a comma-separated list of: owner, collaborator, organization_member."
            )
            raise typer.Exit(code=1)
        affiliation_list = cast(list[Literal["owner", "collaborator", "organization_member"]], affiliation)

    try:
        with GitHub(token=token, base_url=base_url) as client:
            repository_client = client.repository
            data, status_code, etag_value, last_modified_value = repository_client.list_repositories(
                owner=owner,
                organization=organization,
                visibility=visibility,
                affiliation=affiliation_list,
                repository_type=repository_type,
                sort=sort,
                direction=direction,
                per_page=per_page,
                page=page,
                since=since,
                before=before,
                etag=etag,
                last_modified=last_modified,
            )
            result = {
                "data": data,
                "metadata": {
                    "status_code": status_code,
                    "etag": etag_value,
                    "last_modified": last_modified_value,
                },
            }
            print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        logger.exception("Error listing repositories: %s", e)
        raise typer.Exit(code=1) from e

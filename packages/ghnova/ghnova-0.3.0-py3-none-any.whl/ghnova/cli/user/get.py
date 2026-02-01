"""Get command for user CLI."""

from __future__ import annotations

from typing import Annotated

import typer


def get_command(  # noqa: PLR0913
    ctx: typer.Context,
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
    username: Annotated[
        str | None,
        typer.Option(
            "--username",
            help="Username of the user to retrieve. If not provided, the authenticated user's information will be retrieved.",
        ),
    ] = None,
    account_id: Annotated[
        int | None,
        typer.Option(
            "--account-id",
            help="Account ID of the user to retrieve.",
        ),
    ] = None,
    etag: Annotated[
        str | None,
        typer.Option("--etag", help="ETag from a previous request for caching purposes."),
    ] = None,
    last_modified: Annotated[
        str | None,
        typer.Option("--last-modified", help="Last-Modified header from a previous request for caching purposes."),
    ] = None,
):
    """Retrieve user information from GitHub.

    Args:
        ctx: Typer context.
        account_name: Name of the account to use for authentication.
        token: Token for authentication.
        base_url: Base URL of the GitHub platform.
        username: Username of the user to retrieve.
        account_id: Account ID of the user to retrieve.
        etag: ETag from a previous request for caching purposes.
        last_modified: Last-Modified header from a previous request for caching purposes.

    """
    import json  # noqa: PLC0415
    import logging  # noqa: PLC0415

    from ghnova.cli.utils.auth import get_auth_params  # noqa: PLC0415
    from ghnova.client.github import GitHub  # noqa: PLC0415

    logger = logging.getLogger("ghnova")

    token, base_url = get_auth_params(
        config_path=ctx.obj["config_path"], account_name=account_name, token=token, base_url=base_url
    )

    try:
        with GitHub(token=token, base_url=base_url) as client:
            user_client = client.user
            data, status_code, etag_value, last_modified_value = user_client.get_user(
                username=username, account_id=account_id, etag=etag, last_modified=last_modified
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
        logger.error("Error retrieving user information: %s", e)
        raise typer.Exit(code=1) from e

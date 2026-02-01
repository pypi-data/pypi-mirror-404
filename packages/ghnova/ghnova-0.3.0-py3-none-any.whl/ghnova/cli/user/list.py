"""CLI for listing users."""

from __future__ import annotations

from typing import Annotated

import typer


def list_command(  # noqa: D103, PLR0913
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
    since: Annotated[
        int | None,
        typer.Option(
            "--since",
            help="A user ID. Only return users with an ID greater than this ID.",
        ),
    ] = None,
    per_page: Annotated[int | None, typer.Option("--per-page", help="Number of results per page (max 100).")] = None,
    etag: Annotated[
        str | None, typer.Option("--etag", help="ETag from a previous request for caching purposes.")
    ] = None,
    last_modified: Annotated[
        str | None,
        typer.Option("--last-modified", help="Last-Modified header from a previous request for caching purposes."),
    ] = None,
):
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
            data, status_code, etag_value, last_modified_value = user_client.list_users(
                since=since, per_page=per_page, etag=etag, last_modified=last_modified
            )
            result = {
                "data": data,
                "metadata": {
                    "status_code": status_code,
                    "etag": etag_value,
                    "last_modified": last_modified_value,
                },
            }
            typer.echo(json.dumps(result, indent=2, default=str))
    except Exception as e:
        logger.error("Error listing users: %s", e)
        raise typer.Exit(code=1) from e

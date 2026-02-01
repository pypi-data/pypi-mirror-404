"""Update command for user CLI."""

from __future__ import annotations

from typing import Annotated

import typer


def update_command(  # noqa: PLR0913
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
    name: Annotated[
        str | None,
        typer.Option(
            "--name",
            help="The name of the user.",
        ),
    ] = None,
    email: Annotated[
        str | None,
        typer.Option(
            "--email",
            help="The email of the user.",
        ),
    ] = None,
    blog: Annotated[
        str | None,
        typer.Option(
            "--blog",
            help="The blog URL of the user.",
        ),
    ] = None,
    twitter_username: Annotated[
        str | None,
        typer.Option(
            "--twitter-username",
            help="The Twitter username of the user.",
        ),
    ] = None,
    company: Annotated[
        str | None,
        typer.Option(
            "--company",
            help="The company of the user.",
        ),
    ] = None,
    location: Annotated[
        str | None,
        typer.Option(
            "--location",
            help="The location of the user.",
        ),
    ] = None,
    hireable: Annotated[
        bool | None,
        typer.Option(
            "--hireable",
            help="The hireable status of the user.",
        ),
    ] = None,
    bio: Annotated[
        str | None,
        typer.Option(
            "--bio",
            help="The bio of the user.",
        ),
    ] = None,
    etag: Annotated[
        str | None,
        typer.Option(
            "--etag",
            help="ETag from a previous request for caching purposes.",
        ),
    ] = None,
    last_modified: Annotated[
        str | None,
        typer.Option(
            "--last-modified",
            help="Last-Modified header from a previous request for caching purposes.",
        ),
    ] = None,
) -> None:
    """Update the authenticated user's information on GitHub.

    Args:
        ctx: Typer context.
        account_name: Name of the account to use for authentication.
        token: Token for authentication.
        base_url: Base URL of the GitHub platform.
        name: The name of the user.
        email: The email of the user.
        blog: The blog URL of the user.
        twitter_username: The Twitter username of the user.
        company: The company of the user.
        location: The location of the user.
        hireable: The hireable status of the user.
        bio: The bio of the user.
        etag: ETag from a previous request for caching purposes.
        last_modified: Last-Modified header from a previous request for caching purposes.

    """
    import json  # noqa: PLC0415
    import logging  # noqa: PLC0415

    from ghnova.cli.utils.auth import get_auth_params  # noqa: PLC0415
    from ghnova.client.github import GitHub  # noqa: PLC0415

    logger = logging.getLogger("ghnova")

    token, base_url = get_auth_params(
        config_path=ctx.obj["config_path"],
        account_name=account_name,
        token=token,
        base_url=base_url,
    )

    try:
        with GitHub(token=token, base_url=base_url) as client:
            user_client = client.user
            data, status_code, etag_value, last_modified_value = user_client.update_user(
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
        logger.error("Error updating user information: %s", e)
        raise typer.Exit(code=1) from e

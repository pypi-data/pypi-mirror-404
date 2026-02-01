"""Get contextual information command for user CLI."""

from __future__ import annotations

from typing import Annotated

import typer


def contextual_information_command(  # noqa: PLR0913
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
            help="The username of the user to retrieve contextual information for.",
        ),
    ] = None,
    subject_type: Annotated[
        str | None,
        typer.Option(
            "--subject-type",
            help="The type of subject for the hovercard (e.g., 'organization', 'repository', 'issue', 'pull_request').",
        ),
    ] = None,
    subject_id: Annotated[
        str | None,
        typer.Option(
            "--subject-id",
            help="The ID of the subject for the hovercard.",
        ),
    ] = None,
) -> None:
    """Get contextual information about a user on GitHub.

    Args:
        ctx: Typer context.
        username: The username of the user to retrieve contextual information for.
        account_name: Name of the account to use for authentication.
        token: Token for authentication.
        base_url: Base URL of the GitHub platform.
        subject_type: The type of subject for the hovercard.
        subject_id: The ID of the subject for the hovercard.

    """
    import json  # noqa: PLC0415
    import logging  # noqa: PLC0415

    from ghnova.cli.utils.auth import get_auth_params  # noqa: PLC0415
    from ghnova.client.github import GitHub  # noqa: PLC0415

    logger = logging.getLogger("ghnova")

    if username is None:
        logger.error("Username must be provided to retrieve contextual information.")
        raise typer.Exit(code=1)

    token, base_url = get_auth_params(
        config_path=ctx.obj["config_path"],
        account_name=account_name,
        token=token,
        base_url=base_url,
    )

    try:
        with GitHub(token=token, base_url=base_url) as client:
            user_client = client.user
            data, status_code, etag_value, last_modified_value = user_client.get_contextual_information(
                username=username,
                subject_type=subject_type,
                subject_id=subject_id,
            )
            result = {
                "data": data,
                "metadata": {
                    "status_code": status_code,
                    "etag": etag_value,
                    "last_modified": last_modified_value,
                },
            }
            print(json.dumps(result, indent=4))
    except Exception as e:
        logger.error("Error retrieving contextual information: %s", e)
        raise typer.Exit(code=1) from e

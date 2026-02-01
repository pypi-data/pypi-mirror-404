"""Lock command for issue CLI."""

from __future__ import annotations

from typing import Annotated, Literal

import typer


def lock_command(  # noqa: PLR0913
    ctx: typer.Context,
    owner: Annotated[
        str,
        typer.Option(
            "--owner",
            help="The owner of the repository.",
        ),
    ],
    repository: Annotated[
        str,
        typer.Option(
            "--repository",
            help="The name of the repository.",
        ),
    ],
    issue_number: Annotated[
        int,
        typer.Option(
            "--issue-number",
            help="The issue number.",
        ),
    ],
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
    lock_reason: Annotated[
        Literal["off-topic", "too heated", "resolved", "spam"] | None,
        typer.Option(
            "--lock-reason",
            help="Reason for locking: off-topic, too heated, resolved, or spam.",
        ),
    ] = None,
) -> None:
    """Lock an issue to prevent further comments.

    Args:
        ctx: Typer context.
        owner: The owner of the repository.
        repository: The name of the repository.
        issue_number: The issue number.
        account_name: Name of the account to use for authentication.
        token: Token for authentication.
        base_url: Base URL of the GitHub platform.
        lock_reason: Reason for locking the issue.

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
            issue_client = client.issue
            data, status_code, etag_value, last_modified_value = issue_client.lock_issue(
                owner=owner,
                repository=repository,
                issue_number=issue_number,
                lock_reason=lock_reason,
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
        logger.error("Error locking issue: %s", e)
        raise typer.Exit(code=1) from e

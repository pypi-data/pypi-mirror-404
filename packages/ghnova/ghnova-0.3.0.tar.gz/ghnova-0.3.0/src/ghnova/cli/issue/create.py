"""Create command for issue CLI."""

from __future__ import annotations

from typing import Annotated

import typer


def create_command(  # noqa: PLR0913
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
    title: Annotated[
        str,
        typer.Option(
            "--title",
            help="The title of the issue.",
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
    body: Annotated[
        str | None,
        typer.Option(
            "--body",
            help="The body of the issue.",
        ),
    ] = None,
    assignee: Annotated[
        str | None,
        typer.Option(
            "--assignee",
            help="The assignee of the issue.",
        ),
    ] = None,
    milestone: Annotated[
        str | None,
        typer.Option(
            "--milestone",
            help="The milestone for the issue.",
        ),
    ] = None,
    labels: Annotated[
        list[str] | None,
        typer.Option(
            "--labels",
            help="A list of labels to assign to the issue.",
        ),
    ] = None,
    assignees: Annotated[
        list[str] | None,
        typer.Option(
            "--assignees",
            help="A list of assignees to assign to the issue.",
        ),
    ] = None,
    issue_type: Annotated[
        str | None,
        typer.Option(
            "--issue-type",
            help="The type of the issue (e.g., 'bug', 'feature').",
        ),
    ] = None,
) -> None:
    """Create a new issue in a repository.

    Args:
        ctx: Typer context.
        owner: The owner of the repository.
        repository: The name of the repository.
        title: The title of the issue.
        account_name: Name of the account to use for authentication.
        token: Token for authentication.
        base_url: Base URL of the GitHub platform.
        body: The body of the issue.
        assignee: The assignee of the issue.
        milestone: The milestone for the issue.
        labels: A list of labels to assign to the issue.
        assignees: A list of assignees to assign to the issue.
        issue_type: The type of the issue.

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
            data, status_code, etag_value, last_modified_value = issue_client.create_issue(
                owner=owner,
                repository=repository,
                title=title,
                body=body,
                assignee=assignee,
                milestone=milestone,
                labels=labels,
                assignees=assignees,
                issue_type=issue_type,
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
        logger.error("Error creating issue: %s", e)
        raise typer.Exit(code=1) from e

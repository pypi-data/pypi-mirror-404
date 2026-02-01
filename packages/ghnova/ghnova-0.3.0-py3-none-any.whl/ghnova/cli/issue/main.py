"""Issue CLI commands for ghnova."""

from __future__ import annotations

import typer

issue_app = typer.Typer(
    name="issue",
    help="Manage GitHub issues.",
    rich_markup_mode="rich",
)


def register_commands() -> None:
    """Register issue subcommands."""
    from ghnova.cli.issue.create import create_command  # noqa: PLC0415
    from ghnova.cli.issue.get import get_command  # noqa: PLC0415
    from ghnova.cli.issue.list import list_command  # noqa: PLC0415
    from ghnova.cli.issue.lock import lock_command  # noqa: PLC0415
    from ghnova.cli.issue.unlock import unlock_command  # noqa: PLC0415
    from ghnova.cli.issue.update import update_command  # noqa: PLC0415

    issue_app.command(name="create", help="Create a new issue.")(create_command)
    issue_app.command(name="get", help="Get a specific issue.")(get_command)
    issue_app.command(name="list", help="List issues.")(list_command)
    issue_app.command(name="lock", help="Lock an issue.")(lock_command)
    issue_app.command(name="unlock", help="Unlock an issue.")(unlock_command)
    issue_app.command(name="update", help="Update an issue.")(update_command)


register_commands()

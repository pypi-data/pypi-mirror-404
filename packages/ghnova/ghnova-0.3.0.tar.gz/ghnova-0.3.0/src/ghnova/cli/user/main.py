"""User CLI commands for ghnova."""

from __future__ import annotations

import typer

user_app = typer.Typer(
    name="user",
    help="Manage git users.",
    rich_markup_mode="rich",
)


def register_commands() -> None:
    """Register user subcommands."""
    from ghnova.cli.user.ctx_info import contextual_information_command  # noqa: PLC0415
    from ghnova.cli.user.get import get_command  # noqa: PLC0415
    from ghnova.cli.user.list import list_command  # noqa: PLC0415
    from ghnova.cli.user.update import update_command  # noqa: PLC0415

    user_app.command(name="get")(get_command)
    user_app.command(name="list")(list_command)
    user_app.command(name="update")(update_command)
    user_app.command(name="ctx-info")(contextual_information_command)


register_commands()

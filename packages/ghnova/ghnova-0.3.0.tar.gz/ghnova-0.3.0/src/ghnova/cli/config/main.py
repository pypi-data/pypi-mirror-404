"""Configuration CLI commands for ghnova."""

from __future__ import annotations

import typer

config_app = typer.Typer(
    name="config",
    help="Manage github configuration.",
    rich_markup_mode="rich",
)


def register_commands() -> None:
    """Register config subcommands."""
    from ghnova.cli.config.add import add_command  # noqa: PLC0415
    from ghnova.cli.config.delete import delete_command  # noqa: PLC0415
    from ghnova.cli.config.list import list_command  # noqa: PLC0415
    from ghnova.cli.config.update import update_command  # noqa: PLC0415

    config_app.command(name="add")(add_command)
    config_app.command(name="delete")(delete_command)
    config_app.command(name="list")(list_command)
    config_app.command(name="update")(update_command)


register_commands()

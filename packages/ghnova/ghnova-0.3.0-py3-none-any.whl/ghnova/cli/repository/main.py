"""Repository CLI commands for ghnova."""

from __future__ import annotations

import typer

repository_app = typer.Typer(
    name="repository",
    help="Manage git repositories.",
    rich_markup_mode="rich",
)


def register_commands() -> None:
    """Register repository subcommands."""
    from ghnova.cli.repository.list import list_command  # noqa: PLC0415

    repository_app.command(name="list", help="List repositories.")(list_command)


register_commands()

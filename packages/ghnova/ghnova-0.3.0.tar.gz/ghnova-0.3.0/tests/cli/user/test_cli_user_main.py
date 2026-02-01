"""Tests for the user CLI main module."""

from __future__ import annotations

from typer.testing import CliRunner

from ghnova.cli.user.main import user_app

runner = CliRunner()


class TestUserApp:
    """Tests for the user app."""

    def test_user_help(self) -> None:
        """Test that user help works."""
        result = runner.invoke(user_app, ["--help"])
        assert result.exit_code == 0
        assert "user" in result.stdout.lower()

    def test_user_get_command_exists(self) -> None:
        """Test that get command is available."""
        result = runner.invoke(user_app, ["get", "--help"])
        assert result.exit_code == 0

    def test_user_list_command_exists(self) -> None:
        """Test that list command is available."""
        result = runner.invoke(user_app, ["list", "--help"])
        assert result.exit_code == 0

    def test_user_update_command_exists(self) -> None:
        """Test that update command is available."""
        result = runner.invoke(user_app, ["update", "--help"])
        assert result.exit_code == 0

    def test_user_ctx_info_command_exists(self) -> None:
        """Test that ctx-info command is available."""
        result = runner.invoke(user_app, ["ctx-info", "--help"])
        assert result.exit_code == 0

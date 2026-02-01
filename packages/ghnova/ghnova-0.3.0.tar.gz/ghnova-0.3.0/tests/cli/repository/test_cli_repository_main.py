"""Tests for the repository CLI main module."""

from __future__ import annotations

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestRepositoryMain:
    """Tests for the repository CLI main module."""

    def test_repository_command_help(self) -> None:
        """Test repository command help."""
        result = runner.invoke(app, ["repository", "--help"])
        assert result.exit_code == 0
        assert "repository" in result.stdout.lower()

"""Tests for the issue CLI main module."""

from __future__ import annotations

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestIssueMain:
    """Tests for the issue CLI main module."""

    def test_issue_command_help(self) -> None:
        """Test issue command help."""
        result = runner.invoke(app, ["issue", "--help"])
        assert result.exit_code == 0
        assert "issue" in result.stdout.lower()

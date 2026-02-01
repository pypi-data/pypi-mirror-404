"""Tests for the issue create CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestCreateCommand:
    """Tests for the create issue command."""

    def test_create_command_help(self) -> None:
        """Test create command help."""
        result = runner.invoke(app, ["issue", "create", "--help"])
        assert result.exit_code == 0

    def test_create_issue(self, tmp_path) -> None:
        """Test creating a new issue."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.create_issue.return_value = (
                {"id": 1, "number": 1, "title": "New issue", "state": "open"},
                201,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "create",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--title",
                    "New issue",
                ],
            )

        assert result.exit_code == 0
        assert "New issue" in result.stdout
        assert "201" in result.stdout

    def test_create_issue_with_body(self, tmp_path) -> None:
        """Test creating an issue with body."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.create_issue.return_value = (
                {"id": 1, "number": 1, "title": "Bug", "body": "This is a bug", "state": "open"},
                201,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "create",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--title",
                    "Bug",
                    "--body",
                    "This is a bug",
                ],
            )

        assert result.exit_code == 0
        assert "Bug" in result.stdout

    def test_create_issue_with_labels(self, tmp_path) -> None:
        """Test creating an issue with labels."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.create_issue.return_value = (
                {
                    "id": 1,
                    "number": 1,
                    "title": "Issue",
                    "labels": [{"name": "bug"}, {"name": "critical"}],
                },
                201,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "create",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--title",
                    "Issue",
                    "--labels",
                    "bug",
                    "--labels",
                    "critical",
                ],
            )

        assert result.exit_code == 0

    def test_create_issue_error_handling(self, tmp_path) -> None:
        """Test error handling in create command."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.create_issue.side_effect = ValueError("Invalid input")

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "create",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--title",
                    "Issue",
                ],
            )

        assert result.exit_code == 1

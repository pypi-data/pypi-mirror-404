"""Tests for the issue update CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestUpdateCommand:
    """Tests for the update issue command."""

    def test_update_command_help(self) -> None:
        """Test update command help."""
        result = runner.invoke(app, ["issue", "update", "--help"])
        assert result.exit_code == 0

    def test_update_issue_title(self, tmp_path) -> None:
        """Test updating issue title."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.update_issue.return_value = (
                {"id": 1, "number": 42, "title": "Updated title", "state": "open"},
                200,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "update",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--issue-number",
                    "42",
                    "--title",
                    "Updated title",
                ],
            )

        assert result.exit_code == 0
        assert "Updated title" in result.stdout
        assert "200" in result.stdout

    def test_update_issue_state(self, tmp_path) -> None:
        """Test updating issue state."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.update_issue.return_value = (
                {"id": 1, "number": 42, "title": "Issue", "state": "closed"},
                200,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "update",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--issue-number",
                    "42",
                    "--state",
                    "closed",
                ],
            )

        assert result.exit_code == 0
        assert "closed" in result.stdout

    def test_update_issue_multiple_fields(self, tmp_path) -> None:
        """Test updating multiple issue fields."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.update_issue.return_value = (
                {
                    "id": 1,
                    "number": 42,
                    "title": "New title",
                    "body": "New body",
                    "state": "closed",
                },
                200,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "update",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--issue-number",
                    "42",
                    "--title",
                    "New title",
                    "--body",
                    "New body",
                    "--state",
                    "closed",
                ],
            )

        assert result.exit_code == 0
        assert "New title" in result.stdout

    def test_update_issue_with_labels(self, tmp_path) -> None:
        """Test updating issue with labels."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.update_issue.return_value = (
                {"id": 1, "number": 42, "title": "Issue", "labels": [{"name": "bug"}]},
                200,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "update",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--issue-number",
                    "42",
                    "--labels",
                    "bug",
                ],
            )

        assert result.exit_code == 0

    def test_update_issue_error_handling(self, tmp_path) -> None:
        """Test error handling in update command."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.update_issue.side_effect = ValueError("Issue not found")

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "update",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--issue-number",
                    "99999",
                    "--title",
                    "New title",
                ],
            )

        assert result.exit_code == 1

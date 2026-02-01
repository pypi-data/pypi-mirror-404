"""Tests for the issue get CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestGetCommand:
    """Tests for the get issue command."""

    def test_get_command_help(self) -> None:
        """Test get command help."""
        result = runner.invoke(app, ["issue", "get", "--help"])
        assert result.exit_code == 0

    def test_get_issue(self, tmp_path) -> None:
        """Test getting a specific issue."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.get_issue.return_value = (
                {"id": 1, "number": 42, "title": "Bug report", "state": "open"},
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
                    "get",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--issue-number",
                    "42",
                ],
            )

        assert result.exit_code == 0
        assert "Bug report" in result.stdout
        assert "200" in result.stdout

    def test_get_issue_with_caching_headers(self, tmp_path) -> None:
        """Test getting issue with ETag and Last-Modified headers."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.get_issue.return_value = (
                {"id": 1, "number": 42, "title": "Bug report"},
                304,
                "etag-value",
                "Last-Modified-value",
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "get",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--issue-number",
                    "42",
                    "--etag",
                    "etag-value",
                ],
            )

        assert result.exit_code == 0
        assert "304" in result.stdout

    def test_get_issue_error_handling(self, tmp_path) -> None:
        """Test error handling in get command."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.get_issue.side_effect = ValueError("Issue not found")

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "get",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--issue-number",
                    "99999",
                ],
            )

        assert result.exit_code == 1

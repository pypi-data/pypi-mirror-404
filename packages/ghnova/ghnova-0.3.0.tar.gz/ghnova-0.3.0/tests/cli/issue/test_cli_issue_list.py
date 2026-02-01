"""Tests for the issue list CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestListCommand:
    """Tests for the list issues command."""

    def test_list_command_help(self) -> None:
        """Test list command help."""
        result = runner.invoke(app, ["issue", "list", "--help"])
        assert result.exit_code == 0

    def test_list_issues(self, tmp_path) -> None:
        """Test listing issues from a repository."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.list_issues.return_value = (
                [
                    {"id": 1, "number": 1, "title": "First issue", "state": "open"},
                    {"id": 2, "number": 2, "title": "Second issue", "state": "closed"},
                ],
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
                    "list",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                ],
            )

        assert result.exit_code == 0
        assert "First issue" in result.stdout
        assert "Second issue" in result.stdout
        assert "200" in result.stdout

    def test_list_issues_with_state_filter(self, tmp_path) -> None:
        """Test listing issues with state filter."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.list_issues.return_value = (
                [
                    {"id": 1, "number": 1, "title": "Open issue", "state": "open"},
                ],
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
                    "list",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--state",
                    "open",
                ],
            )

        assert result.exit_code == 0
        assert "Open issue" in result.stdout

    def test_list_issues_with_pagination(self, tmp_path) -> None:
        """Test listing issues with pagination options."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.list_issues.return_value = (
                [{"id": 1, "number": 1, "title": "Issue"}],
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
                    "list",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--per-page",
                    "50",
                    "--page",
                    "2",
                ],
            )

        assert result.exit_code == 0
        mock_issue_client.list_issues.assert_called_once()
        call_kwargs = mock_issue_client.list_issues.call_args[1]
        assert call_kwargs["per_page"] == 50  # noqa: PLR2004
        assert call_kwargs["page"] == 2  # noqa: PLR2004

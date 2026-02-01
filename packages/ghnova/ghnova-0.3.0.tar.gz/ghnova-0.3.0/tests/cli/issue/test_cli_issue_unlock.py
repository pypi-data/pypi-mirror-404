"""Tests for the issue unlock CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestUnlockCommand:
    """Tests for the unlock issue command."""

    def test_unlock_command_help(self) -> None:
        """Test unlock command help."""
        result = runner.invoke(app, ["issue", "unlock", "--help"])
        assert result.exit_code == 0

    def test_unlock_issue(self, tmp_path) -> None:
        """Test unlocking an issue."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.unlock_issue.return_value = (
                {"id": 1, "number": 42, "locked": False},
                204,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "unlock",
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
        assert "204" in result.stdout

    def test_unlock_issue_account_overrides_custom_token(self, tmp_path) -> None:
        """Test that account token takes precedence over explicit token."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.unlock_issue.return_value = (
                {"id": 1, "number": 42, "locked": False},
                204,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "unlock",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--issue-number",
                    "42",
                    "--token",
                    "custom_token",
                ],
            )

        assert result.exit_code == 0
        mock_github.assert_called_once_with(token="test_token", base_url="https://github.com")

    def test_unlock_issue_error_handling(self, tmp_path) -> None:
        """Test error handling in unlock command."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.unlock_issue.side_effect = ValueError("Issue not found")

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "unlock",
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

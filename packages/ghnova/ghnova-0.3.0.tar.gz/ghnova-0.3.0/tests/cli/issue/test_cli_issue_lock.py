"""Tests for the issue lock CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestLockCommand:
    """Tests for the lock issue command."""

    def test_lock_command_help(self) -> None:
        """Test lock command help."""
        result = runner.invoke(app, ["issue", "lock", "--help"])
        assert result.exit_code == 0

    def test_lock_issue(self, tmp_path) -> None:
        """Test locking an issue."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.lock_issue.return_value = (
                {"id": 1, "number": 42, "locked": True},
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
                    "lock",
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

    def test_lock_issue_with_reason(self, tmp_path) -> None:
        """Test locking an issue with a reason."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.lock_issue.return_value = (
                {"id": 1, "number": 42, "locked": True},
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
                    "lock",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                    "--repository",
                    "Hello-World",
                    "--issue-number",
                    "42",
                    "--lock-reason",
                    "too heated",
                ],
            )

        assert result.exit_code == 0
        mock_issue_client.lock_issue.assert_called_once()
        call_kwargs = mock_issue_client.lock_issue.call_args[1]
        assert call_kwargs["lock_reason"] == "too heated"

    def test_lock_issue_error_handling(self, tmp_path) -> None:
        """Test error handling in lock command."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_issue_client = mock_client.issue
            mock_issue_client.lock_issue.side_effect = ValueError("Issue not found")

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "issue",
                    "lock",
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

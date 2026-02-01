"""Tests for the user list CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestListCommand:
    """Tests for the list users command."""

    def test_list_command_help(self) -> None:
        """Test list command help."""
        result = runner.invoke(app, ["user", "list", "--help"])
        assert result.exit_code == 0

    def test_list_users(self, tmp_path) -> None:
        """Test listing users."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with (
            patch("ghnova.cli.utils.auth.get_auth_params") as mock_auth,
            patch("ghnova.client.github.GitHub") as mock_github,
        ):
            mock_auth.return_value = ("test_token", "https://github.com")
            mock_client = mock_github.return_value.__enter__.return_value
            mock_user_client = mock_client.user
            mock_user_client.list_users.return_value = (
                [
                    {"login": "octocat", "id": 1},
                    {"login": "cat", "id": 2},
                ],
                200,
                None,
                None,
            )

            result = runner.invoke(
                app,
                ["--config-path", str(config_file), "user", "list"],
            )

        assert result.exit_code == 0
        assert "octocat" in result.stdout
        assert "cat" in result.stdout

    def test_list_users_with_since(self, tmp_path) -> None:
        """Test listing users with since parameter."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with (
            patch("ghnova.cli.utils.auth.get_auth_params") as mock_auth,
            patch("ghnova.client.github.GitHub") as mock_github,
        ):
            mock_auth.return_value = ("test_token", "https://github.com")
            mock_client = mock_github.return_value.__enter__.return_value
            mock_user_client = mock_client.user
            mock_user_client.list_users.return_value = (
                [{"login": "cat", "id": 2}],
                200,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "user",
                    "list",
                    "--since",
                    "1",
                ],
            )

        assert result.exit_code == 0
        assert "cat" in result.stdout

    def test_list_users_with_per_page(self, tmp_path) -> None:
        """Test listing users with per_page parameter."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with (
            patch("ghnova.cli.utils.auth.get_auth_params") as mock_auth,
            patch("ghnova.client.github.GitHub") as mock_github,
        ):
            mock_auth.return_value = ("test_token", "https://github.com")
            mock_client = mock_github.return_value.__enter__.return_value
            mock_user_client = mock_client.user
            mock_user_client.list_users.return_value = (
                [{"login": "octocat", "id": 1}],
                200,
                None,
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "user",
                    "list",
                    "--per-page",
                    "10",
                ],
            )

        assert result.exit_code == 0
        assert "octocat" in result.stdout

    def test_list_empty_response(self, tmp_path) -> None:
        """Test listing users with empty response."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with (
            patch("ghnova.cli.utils.auth.get_auth_params") as mock_auth,
            patch("ghnova.client.github.GitHub") as mock_github,
        ):
            mock_auth.return_value = ("test_token", "https://github.com")
            mock_client = mock_github.return_value.__enter__.return_value
            mock_user_client = mock_client.user
            mock_user_client.list_users.return_value = (
                [],
                200,
                None,
                None,
            )

            result = runner.invoke(
                app,
                ["--config-path", str(config_file), "user", "list"],
            )

        assert result.exit_code == 0
        assert "[]" in result.stdout

    def test_list_users_error_handling(self, tmp_path) -> None:
        """Test error handling in list command."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with (
            patch("ghnova.cli.utils.auth.get_auth_params") as mock_auth,
            patch("ghnova.client.github.GitHub") as mock_github,
        ):
            mock_auth.return_value = ("test_token", "https://github.com")
            mock_client = mock_github.return_value.__enter__.return_value
            mock_user_client = mock_client.user
            mock_user_client.list_users.side_effect = ValueError("API error")

            result = runner.invoke(
                app,
                ["--config-path", str(config_file), "user", "list"],
            )

        assert result.exit_code == 1

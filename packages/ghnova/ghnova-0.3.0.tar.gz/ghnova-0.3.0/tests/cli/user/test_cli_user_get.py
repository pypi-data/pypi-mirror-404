"""Tests for the user get CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestGetCommand:
    """Tests for the get user command."""

    def test_get_command_help(self) -> None:
        """Test get command help."""
        result = runner.invoke(app, ["user", "get", "--help"])
        assert result.exit_code == 0
        assert "retrieve user information" in result.stdout.lower()

    def test_get_authenticated_user(self, tmp_path) -> None:
        """Test getting authenticated user information."""
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
            mock_user_client.get_user.return_value = (
                {"login": "octocat", "id": 1, "name": "The Octocat"},
                200,
                None,
                None,
            )

            result = runner.invoke(
                app,
                ["--config-path", str(config_file), "user", "get"],
            )

        assert result.exit_code == 0
        assert "octocat" in result.stdout
        assert "200" in result.stdout

    def test_get_user_by_username(self, tmp_path) -> None:
        """Test getting user by username."""
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
            mock_user_client.get_user.return_value = (
                {"login": "octocat", "id": 1, "name": "The Octocat"},
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
                    "get",
                    "--username",
                    "octocat",
                ],
            )

        assert result.exit_code == 0
        assert "octocat" in result.stdout

    def test_get_user_by_account_id(self, tmp_path) -> None:
        """Test getting user by account ID."""
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
            mock_user_client.get_user.return_value = (
                {"login": "octocat", "id": 1, "name": "The Octocat"},
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
                    "get",
                    "--account-id",
                    "1",
                ],
            )

        assert result.exit_code == 0
        assert "octocat" in result.stdout

    def test_get_user_with_etag(self, tmp_path) -> None:
        """Test getting user with ETag for caching."""
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
            mock_user_client.get_user.return_value = (
                {},
                304,
                "etag123",
                None,
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "user",
                    "get",
                    "--etag",
                    "etag123",
                ],
            )

        assert result.exit_code == 0
        assert "304" in result.stdout

    def test_get_user_with_custom_token(self, tmp_path) -> None:
        """Test getting user with custom token."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with (
            patch("ghnova.cli.utils.auth.get_auth_params") as mock_auth,
            patch("ghnova.client.github.GitHub") as mock_github,
        ):
            mock_auth.return_value = ("custom_token", None)
            mock_client = mock_github.return_value.__enter__.return_value
            mock_user_client = mock_client.user
            mock_user_client.get_user.return_value = (
                {"login": "octocat", "id": 1},
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
                    "get",
                    "--token",
                    "custom_token",
                ],
            )

        assert result.exit_code == 0
        mock_github.assert_called_once_with(token="custom_token", base_url=None)

    def test_get_user_error_handling(self, tmp_path) -> None:
        """Test error handling in get command."""
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
            mock_user_client.get_user.side_effect = ValueError("Invalid user")

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "user",
                    "get",
                ],
            )

        assert result.exit_code == 1

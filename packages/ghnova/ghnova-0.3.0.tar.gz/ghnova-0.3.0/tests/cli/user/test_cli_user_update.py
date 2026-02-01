"""Tests for the user update CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestUpdateCommand:
    """Tests for the update user command."""

    def test_update_command_help(self) -> None:
        """Test update command help."""
        result = runner.invoke(app, ["user", "update", "--help"])
        assert result.exit_code == 0

    def test_update_user_name(self, tmp_path) -> None:
        """Test updating user name."""
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
            mock_user_client.update_user.return_value = (
                {"login": "octocat", "name": "New Name", "id": 1},
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
                    "update",
                    "--name",
                    "New Name",
                ],
            )

        assert result.exit_code == 0
        assert "New Name" in result.stdout

    def test_update_user_email(self, tmp_path) -> None:
        """Test updating user email."""
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
            mock_user_client.update_user.return_value = (
                {"login": "octocat", "email": "new@example.com", "id": 1},
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
                    "update",
                    "--email",
                    "new@example.com",
                ],
            )

        assert result.exit_code == 0
        assert "new@example.com" in result.stdout

    def test_update_user_multiple_fields(self, tmp_path) -> None:
        """Test updating multiple user fields."""
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
            mock_user_client.update_user.return_value = (
                {
                    "login": "octocat",
                    "name": "New Name",
                    "email": "new@example.com",
                    "location": "San Francisco",
                    "id": 1,
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
                    "user",
                    "update",
                    "--name",
                    "New Name",
                    "--email",
                    "new@example.com",
                    "--location",
                    "San Francisco",
                ],
            )

        assert result.exit_code == 0
        assert "New Name" in result.stdout
        assert "San Francisco" in result.stdout

    def test_update_user_with_bio(self, tmp_path) -> None:
        """Test updating user bio."""
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
            mock_user_client.update_user.return_value = (
                {"login": "octocat", "bio": "Developer", "id": 1},
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
                    "update",
                    "--bio",
                    "Developer",
                ],
            )

        assert result.exit_code == 0
        assert "Developer" in result.stdout

    def test_update_user_hireable(self, tmp_path) -> None:
        """Test updating user hireable status."""
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
            mock_user_client.update_user.return_value = (
                {"login": "octocat", "hireable": True, "id": 1},
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
                    "update",
                    "--hireable",
                ],
            )

        assert result.exit_code == 0

    def test_update_user_error_handling(self, tmp_path) -> None:
        """Test error handling in update command."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_user_client = mock_client.user
            mock_user_client.update_user.side_effect = ValueError("Update failed")

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "user",
                    "update",
                    "--name",
                    "New Name",
                ],
            )

        assert result.exit_code == 1

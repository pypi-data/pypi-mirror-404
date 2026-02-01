"""Tests for the user ctx-info CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestContextualInformationCommand:
    """Tests for the get contextual information command."""

    def test_ctx_info_command_help(self) -> None:
        """Test ctx-info command help."""
        result = runner.invoke(app, ["user", "ctx-info", "--help"])
        assert result.exit_code == 0

    def test_get_contextual_info(self, tmp_path) -> None:
        """Test getting contextual information for a user."""
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
            mock_user_client.get_contextual_information.return_value = (
                {
                    "hovercard": {
                        "contexts": [
                            {
                                "message": "Owns this repository",
                                "oct_icon": "repo",
                            }
                        ]
                    }
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
                    "ctx-info",
                    "--username",
                    "octocat",
                ],
            )

        assert result.exit_code == 0
        assert "hovercard" in result.stdout

    def test_get_contextual_info_with_subject_type(self, tmp_path) -> None:
        """Test getting contextual information with subject type."""
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
            mock_user_client.get_contextual_information.return_value = (
                {"hovercard": {"contexts": [{"message": "Org member", "oct_icon": "organization"}]}},
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
                    "ctx-info",
                    "--username",
                    "octocat",
                    "--subject-type",
                    "organization",
                ],
            )

        assert result.exit_code == 0
        assert "hovercard" in result.stdout

    def test_get_contextual_info_with_subject_id(self, tmp_path) -> None:
        """Test getting contextual information with subject ID."""
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
            mock_user_client.get_contextual_information.return_value = (
                {"hovercard": {"contexts": [{"message": "Mentioned in issue", "oct_icon": "issue"}]}},
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
                    "ctx-info",
                    "--username",
                    "octocat",
                    "--subject-type",
                    "issue",
                    "--subject-id",
                    "123",
                ],
            )

        assert result.exit_code == 0
        assert "hovercard" in result.stdout

    def test_ctx_info_missing_username(self, tmp_path) -> None:
        """Test ctx-info command with missing username."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        result = runner.invoke(
            app,
            [
                "--config-path",
                str(config_file),
                "user",
                "ctx-info",
            ],
        )

        assert result.exit_code == 1

    def test_ctx_info_with_custom_token(self, tmp_path) -> None:
        """Test ctx-info command with custom token."""
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
            mock_user_client.get_contextual_information.return_value = (
                {"hovercard": {}},
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
                    "ctx-info",
                    "--username",
                    "octocat",
                    "--token",
                    "custom_token",
                ],
            )

        assert result.exit_code == 0
        mock_github.assert_called_once_with(token="custom_token", base_url=None)

    def test_ctx_info_error_handling(self, tmp_path) -> None:
        """Test error handling in ctx-info command."""
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
            mock_user_client.get_contextual_information.side_effect = ValueError("API error")

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "user",
                    "ctx-info",
                    "--username",
                    "octocat",
                ],
            )

        assert result.exit_code == 1

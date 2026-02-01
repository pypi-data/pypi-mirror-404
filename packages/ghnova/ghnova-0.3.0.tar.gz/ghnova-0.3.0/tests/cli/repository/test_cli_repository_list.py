"""Tests for the repository list CLI command."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestListCommand:
    """Tests for the list repositories command."""

    def test_list_command_help(self) -> None:
        """Test list command help."""
        result = runner.invoke(app, ["repository", "list", "--help"])
        assert result.exit_code == 0

    def test_list_repositories(self, tmp_path) -> None:
        """Test listing repositories."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_repository_client = mock_client.repository
            mock_repository_client.list_repositories.return_value = (
                [
                    {"id": 1, "name": "Hello-World", "full_name": "octocat/Hello-World", "private": False},
                    {"id": 2, "name": "Spoon-Knife", "full_name": "octocat/Spoon-Knife", "private": False},
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
                    "repository",
                    "list",
                    "--account-name",
                    "test",
                ],
            )

        assert result.exit_code == 0
        assert "Hello-World" in result.stdout
        assert "Spoon-Knife" in result.stdout
        assert "200" in result.stdout

    def test_list_repositories_with_owner(self, tmp_path) -> None:
        """Test listing repositories for a specific owner."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_repository_client = mock_client.repository
            mock_repository_client.list_repositories.return_value = (
                [
                    {"id": 1, "name": "Hello-World", "full_name": "octocat/Hello-World", "private": False},
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
                    "repository",
                    "list",
                    "--account-name",
                    "test",
                    "--owner",
                    "octocat",
                ],
            )

        assert result.exit_code == 0
        mock_repository_client.list_repositories.assert_called_once()
        call_kwargs = mock_repository_client.list_repositories.call_args[1]
        assert call_kwargs["owner"] == "octocat"

    def test_list_repositories_with_visibility_filter(self, tmp_path) -> None:
        """Test listing repositories with visibility filter."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_repository_client = mock_client.repository
            mock_repository_client.list_repositories.return_value = (
                [
                    {"id": 1, "name": "Private-Repo", "full_name": "user/Private-Repo", "private": True},
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
                    "repository",
                    "list",
                    "--account-name",
                    "test",
                    "--visibility",
                    "private",
                ],
            )

        assert result.exit_code == 0
        mock_repository_client.list_repositories.assert_called_once()
        call_kwargs = mock_repository_client.list_repositories.call_args[1]
        assert call_kwargs["visibility"] == "private"

    def test_list_repositories_with_sorting(self, tmp_path) -> None:
        """Test listing repositories with sorting options."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_repository_client = mock_client.repository
            mock_repository_client.list_repositories.return_value = (
                [
                    {"id": 1, "name": "Repo1", "full_name": "user/Repo1", "updated_at": "2025-01-31T00:00:00Z"},
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
                    "repository",
                    "list",
                    "--account-name",
                    "test",
                    "--sort",
                    "updated",
                    "--direction",
                    "desc",
                ],
            )

        assert result.exit_code == 0
        mock_repository_client.list_repositories.assert_called_once()
        call_kwargs = mock_repository_client.list_repositories.call_args[1]
        assert call_kwargs["sort"] == "updated"
        assert call_kwargs["direction"] == "desc"

    def test_list_repositories_with_pagination(self, tmp_path) -> None:
        """Test listing repositories with pagination options."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_repository_client = mock_client.repository
            mock_repository_client.list_repositories.return_value = (
                [
                    {"id": 1, "name": "Repo1", "full_name": "user/Repo1", "private": False},
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
                    "repository",
                    "list",
                    "--account-name",
                    "test",
                    "--per-page",
                    "50",
                    "--page",
                    "2",
                ],
            )

        assert result.exit_code == 0
        mock_repository_client.list_repositories.assert_called_once()
        call_kwargs = mock_repository_client.list_repositories.call_args[1]
        assert call_kwargs["per_page"] == 50  # noqa: PLR2004
        assert call_kwargs["page"] == 2  # noqa: PLR2004

    def test_list_repositories_with_type_filter(self, tmp_path) -> None:
        """Test listing repositories with type filter."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_repository_client = mock_client.repository
            mock_repository_client.list_repositories.return_value = (
                [
                    {"id": 1, "name": "Repo1", "full_name": "user/Repo1", "private": False},
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
                    "repository",
                    "list",
                    "--account-name",
                    "test",
                    "--type",
                    "public",
                ],
            )

        assert result.exit_code == 0
        mock_repository_client.list_repositories.assert_called_once()
        call_kwargs = mock_repository_client.list_repositories.call_args[1]
        assert call_kwargs["repository_type"] == "public"

    def test_list_repositories_with_caching_headers(self, tmp_path) -> None:
        """Test listing repositories with ETag and Last-Modified headers."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_repository_client = mock_client.repository
            mock_repository_client.list_repositories.return_value = (
                [],
                304,
                "etag-value",
                "Last-Modified-value",
            )

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "repository",
                    "list",
                    "--account-name",
                    "test",
                    "--etag",
                    "etag-value",
                ],
            )

        assert result.exit_code == 0
        assert "304" in result.stdout

    def test_list_repositories_with_valid_affiliation(self, tmp_path) -> None:
        """Test listing repositories with valid affiliation values."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_repository_client = mock_client.repository
            mock_repository_client.list_repositories.return_value = (
                [
                    {"id": 1, "name": "Repo1", "full_name": "user/Repo1", "private": False},
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
                    "repository",
                    "list",
                    "--account-name",
                    "test",
                    "--affiliation",
                    "owner",
                    "--affiliation",
                    "collaborator",
                ],
            )

        assert result.exit_code == 0
        mock_repository_client.list_repositories.assert_called_once()
        call_kwargs = mock_repository_client.list_repositories.call_args[1]
        assert call_kwargs["affiliation"] == ["owner", "collaborator"]

    def test_list_repositories_with_invalid_affiliation(self, tmp_path) -> None:
        """Test listing repositories with invalid affiliation values."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as _mock_github:
            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "repository",
                    "list",
                    "--account-name",
                    "test",
                    "--affiliation",
                    "invalid_value",
                ],
            )

        assert result.exit_code == 1
        assert "Invalid affiliation value" in result.stderr

    def test_list_repositories_error_handling(self, tmp_path) -> None:
        """Test error handling in list command."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            "accounts:\n  test:\n    name: test\n    token: test_token\n"
            "    base_url: https://github.com\ndefault_account: test\n"
        )

        with patch("ghnova.client.github.GitHub") as mock_github:
            mock_client = mock_github.return_value.__enter__.return_value
            mock_repository_client = mock_client.repository
            mock_repository_client.list_repositories.side_effect = ValueError("API error")

            result = runner.invoke(
                app,
                [
                    "--config-path",
                    str(config_file),
                    "repository",
                    "list",
                    "--account-name",
                    "test",
                ],
            )

        assert result.exit_code == 1

"""Tests for the main CLI entry point."""

from __future__ import annotations

from typer.testing import CliRunner

from ghnova.cli.main import app

runner = CliRunner()


class TestMainCallback:
    """Tests for the main CLI callback."""

    def test_main_help(self) -> None:
        """Test that main help works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ghnova" in result.stdout

    def test_main_verbose_info(self) -> None:
        """Test verbose level option INFO."""
        result = runner.invoke(app, ["--verbose", "INFO", "config", "--help"])
        assert result.exit_code == 0

    def test_main_verbose_debug(self) -> None:
        """Test verbose level option DEBUG."""
        result = runner.invoke(app, ["--verbose", "DEBUG", "config", "--help"])
        assert result.exit_code == 0

    def test_main_config_path(self, tmp_path) -> None:
        """Test passing config path."""
        config_file = tmp_path / "config.yaml"
        result = runner.invoke(app, ["--config-path", str(config_file), "config", "--help"])
        assert result.exit_code == 0

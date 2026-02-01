"""CLI command tests."""

import subprocess
import sys
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from cluster_cli.main import app, get_latest_version_from_pypi, PYPI_PACKAGE_NAME
from cluster_cli.__version__ import __version__


runner = CliRunner()


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_shows_current_version(self):
        """Version command should display current version."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    @patch("cluster_cli.main.get_latest_version_from_pypi")
    def test_version_up_to_date(self, mock_get_latest):
        """Version command should show up-to-date message when current."""
        mock_get_latest.return_value = __version__
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "latest version" in result.stdout.lower()

    @patch("cluster_cli.main.get_latest_version_from_pypi")
    def test_version_update_available(self, mock_get_latest):
        """Version command should show update available when newer exists."""
        mock_get_latest.return_value = "99.99.99"
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "99.99.99" in result.stdout
        assert "cluster upgrade" in result.stdout.lower()

    @patch("cluster_cli.main.get_latest_version_from_pypi")
    def test_version_pypi_unreachable(self, mock_get_latest):
        """Version command should handle PyPI being unreachable."""
        mock_get_latest.return_value = None
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout


class TestUpgradeCommand:
    """Tests for the upgrade command."""

    @patch("cluster_cli.main.get_latest_version_from_pypi")
    def test_upgrade_already_latest(self, mock_get_latest):
        """Upgrade should report when already on latest version."""
        mock_get_latest.return_value = __version__
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 0
        assert "latest version" in result.stdout.lower()

    @patch("cluster_cli.main.get_latest_version_from_pypi")
    def test_upgrade_pypi_unreachable(self, mock_get_latest):
        """Upgrade should fail gracefully when PyPI is unreachable."""
        mock_get_latest.return_value = None
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 1
        assert "error" in result.stdout.lower()

    @patch("subprocess.run")
    @patch("cluster_cli.main.get_latest_version_from_pypi")
    def test_upgrade_runs_pip(self, mock_get_latest, mock_run):
        """Upgrade should run pip install --upgrade."""
        mock_get_latest.return_value = "99.99.99"
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = runner.invoke(app, ["upgrade"])

        assert result.exit_code == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "pip" in call_args
        assert "install" in call_args
        assert "--upgrade" in call_args
        assert PYPI_PACKAGE_NAME in call_args


class TestRebootCommand:
    """Tests for the reboot command."""

    @patch("subprocess.run")
    def test_reboot_shows_health_check(self, mock_run):
        """Reboot should show cluster health before prompting."""
        mock_run.return_value = MagicMock(returncode=0)

        # Simulate user declining reboot
        result = runner.invoke(app, ["reboot"], input="n\n")

        assert result.exit_code == 0
        # Should have called kubectl get nodes
        calls = [str(call) for call in mock_run.call_args_list]
        assert any("kubectl" in call and "nodes" in call for call in calls)

    @patch("subprocess.run")
    def test_reboot_aborted_by_user(self, mock_run):
        """Reboot should abort when user declines."""
        mock_run.return_value = MagicMock(returncode=0)

        result = runner.invoke(app, ["reboot"], input="n\n")

        # User declined, so no reboot should be called
        reboot_calls = [c for c in mock_run.call_args_list if "reboot" in str(c)]
        assert len(reboot_calls) == 0


class TestHealthCommand:
    """Tests for the health command."""

    @patch("subprocess.run")
    def test_health_calls_watch(self, mock_run):
        """Health should run watch command."""
        mock_run.return_value = MagicMock(returncode=0)

        result = runner.invoke(app, ["health"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "watch" in call_args


class TestGetLatestVersion:
    """Tests for PyPI version checking."""

    @patch("requests.get")
    def test_get_latest_version_success(self, mock_get):
        """Should return version from PyPI response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"info": {"version": "1.2.3"}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_latest_version_from_pypi()

        assert result == "1.2.3"
        mock_get.assert_called_once()
        assert PYPI_PACKAGE_NAME in mock_get.call_args[0][0]

    @patch("requests.get")
    def test_get_latest_version_timeout(self, mock_get):
        """Should return None on timeout."""
        mock_get.side_effect = Exception("Connection timeout")

        result = get_latest_version_from_pypi()

        assert result is None

    @patch("requests.get")
    def test_get_latest_version_bad_response(self, mock_get):
        """Should return None on bad response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        result = get_latest_version_from_pypi()

        assert result is None


class TestHelpOutput:
    """Tests for help output."""

    def test_help_flag(self):
        """--help should show usage information."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "version" in result.stdout.lower()
        assert "upgrade" in result.stdout.lower()
        assert "reboot" in result.stdout.lower()
        assert "health" in result.stdout.lower()

    def test_short_help_flag(self):
        """-h should show usage information."""
        result = runner.invoke(app, ["-h"])
        assert result.exit_code == 0

    def test_no_args_shows_help(self):
        """Running with no args should show help."""
        result = runner.invoke(app, [])
        # no_args_is_help=True shows help but exits with code 2
        assert result.exit_code == 2
        assert "Usage" in result.stdout or "usage" in result.stdout.lower()


class TestInvalidCommands:
    """Tests for invalid command handling."""

    def test_unknown_command(self):
        """Unknown commands should show error."""
        result = runner.invoke(app, ["notacommand"])
        assert result.exit_code != 0

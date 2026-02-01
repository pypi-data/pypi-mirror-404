from click.testing import CliRunner
from onako.cli import main


def test_status_reports_something():
    runner = CliRunner()
    result = runner.invoke(main, ["status"])
    assert result.exit_code == 0
    assert "Onako server:" in result.output


def test_stop_completes():
    runner = CliRunner()
    result = runner.invoke(main, ["stop"])
    assert result.exit_code == 0
    assert "not running" in result.output or "stopped" in result.output


def test_stop_handles_no_service():
    """Stop should handle the case where neither pid file nor service exists."""
    runner = CliRunner()
    result = runner.invoke(main, ["stop"])
    assert result.exit_code == 0

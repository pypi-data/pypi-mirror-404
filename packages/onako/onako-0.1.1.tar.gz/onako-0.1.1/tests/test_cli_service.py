from click.testing import CliRunner
from onako.cli import main


def test_status_reports_something():
    runner = CliRunner()
    result = runner.invoke(main, ["status"])
    assert result.exit_code == 0
    assert "Onako server:" in result.output


def test_uninstall_when_not_installed():
    runner = CliRunner()
    result = runner.invoke(main, ["uninstall"])
    assert result.exit_code == 0
    assert "not installed" in result.output

from click.testing import CliRunner
from onako.cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert "0.3.0" in result.output


def test_default_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "--session" in result.output
    assert "--host" in result.output
    assert "--port" in result.output


def test_serve_help():
    runner = CliRunner()
    result = runner.invoke(main, ["serve", "--help"])
    assert result.exit_code == 0
    assert "--host" in result.output
    assert "--port" in result.output
    assert "--session" in result.output
    assert "--background" in result.output
    assert "--dir" in result.output

import pytest
from click.testing import CliRunner
from dukpyra.cli import cli

def test_cli_version():
    """Test version command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert '0.1.0' in result.output

def test_cli_help():
    """Test help command"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Dukpyra' in result.output

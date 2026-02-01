"""CLI smoke tests."""

from __future__ import annotations

from click.testing import CliRunner

from sagellm_dev_tools.cli import main


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "sagellm-dev" in result.output


def test_cli_no_args_shows_quick_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code == 0
    assert "Quick commands" in result.output
    assert "sagellm-dev init" in result.output

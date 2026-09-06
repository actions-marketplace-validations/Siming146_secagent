"""Test CLI commands using Typer runner."""

from typer.testing import CliRunner
from secagent.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "SecAgent version" in result.stdout


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Autonomous AI Security Agent" in result.stdout


def test_cli_audit_mock():
    result = runner.invoke(app, ["audit", "benchmark/sample_vulnerable_repo", "--mock-llm"])
    assert result.exit_code == 0
    assert "SecAgent Audit Initializing" in result.stdout

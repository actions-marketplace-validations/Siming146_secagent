"""Test sandbox command runner and environment isolation."""

import os
import sys
from secagent.sandbox.runner import SandboxRunner
from secagent.sandbox.venv_manager import SandboxVenvManager


def test_sandbox_run_success():
    runner = SandboxRunner(default_timeout=5)
    result = runner.run(
        command=[sys.executable, "-c", "print('hello_sandbox')"],
        cwd=os.getcwd(),
    )
    assert result.is_success
    assert "hello_sandbox" in result.stdout
    assert not result.timed_out


def test_sandbox_timeout():
    runner = SandboxRunner(default_timeout=1)
    # Run a script that sleeps longer than timeout
    result = runner.run(
        command=[sys.executable, "-c", "import time; time.sleep(3)"],
        cwd=os.getcwd(),
        timeout=1,
    )
    assert result.timed_out
    assert not result.is_success


def test_sandbox_env_sanitization(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret_token_123")
    monkeypatch.setenv("GITHUB_TOKEN", "secret_gh_456")
    monkeypatch.setenv("SAFE_VAR", "visible_data")

    runner = SandboxRunner(default_timeout=5)
    script = (
        "import os; "
        "print('KEY=' + str(os.environ.get('DEEPSEEK_API_KEY'))); "
        "print('SAFE=' + str(os.environ.get('SAFE_VAR')))"
    )
    result = runner.run(
        command=[sys.executable, "-c", script],
        cwd=os.getcwd(),
    )
    assert result.is_success
    assert "KEY=None" in result.stdout
    assert "SAFE=visible_data" in result.stdout

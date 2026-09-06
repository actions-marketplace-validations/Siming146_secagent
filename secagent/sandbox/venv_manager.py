"""Virtual environment and test execution manager for sandbox verification."""

import logging
import os
import sys
import tempfile
from typing import List, Optional
from secagent.sandbox.runner import CommandResult, SandboxRunner

logger = logging.getLogger("secagent.sandbox.venv")


class SandboxVenvManager:
    """Manages test execution environments and reproduction script lifecycles."""

    def __init__(self, runner: Optional[SandboxRunner] = None):
        self.runner = runner or SandboxRunner()

    def run_pytest(
        self,
        repo_path: str,
        test_args: Optional[List[str]] = None,
        timeout: int = 60,
    ) -> CommandResult:
        """Run pytest in the target repository using the current python executable."""
        args = test_args or ["tests/"]
        cmd = [sys.executable, "-m", "pytest", "-q"] + args
        return self.runner.run(command=cmd, cwd=os.path.abspath(repo_path), timeout=timeout)

    def execute_reproduction_test(
        self,
        repo_path: str,
        test_code: str,
        test_filename: str = "test_secagent_repro.py",
        timeout: int = 30,
    ) -> CommandResult:
        """Write a temporary reproduction pytest file into repo_path, run it, and clean up."""
        repo_abs = os.path.abspath(repo_path)
        test_file_path = os.path.join(repo_abs, test_filename)

        try:
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            logger.info(f"Executing dynamic reproduction test: {test_file_path}")
            cmd = [sys.executable, "-m", "pytest", "-v", test_filename]
            result = self.runner.run(command=cmd, cwd=repo_abs, timeout=timeout)
            return result

        finally:
            if os.path.exists(test_file_path):
                try:
                    os.remove(test_file_path)
                except OSError as err:
                    logger.warning(f"Could not remove temporary test file {test_file_path}: {err}")

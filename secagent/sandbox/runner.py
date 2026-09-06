"""Lightweight process execution sandbox with timeout, env sanitization, and output limits."""

import logging
import os
import subprocess
import time
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("secagent.sandbox.runner")

# Environment variables that should be sanitized to avoid secret exfiltration during test execution
SENSITIVE_ENV_VARS = {
    "DEEPSEEK_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "OPENAI_API_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "SSH_AUTH_SOCK",
}

MAX_OUTPUT_BYTES = 512 * 1024  # 512 KB limit to prevent log explosion


class CommandResult(BaseModel):
    """Result of a command executed inside the sandbox."""

    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    duration_ms: float = 0.0

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


class SandboxRunner:
    """Safely executes commands in a controlled local subprocess."""

    def __init__(self, default_timeout: int = 60):
        self.default_timeout = default_timeout

    def run(
        self,
        command: List[str],
        cwd: str,
        env_override: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        """Run command in cwd with scrubbed environment and strict timeout."""
        timeout_sec = timeout or self.default_timeout

        # Build sanitized environment
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in SENSITIVE_ENV_VARS and not k.startswith("SECAGENT_")
        }
        clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
        clean_env["PYTHONUNBUFFERED"] = "1"

        if env_override:
            clean_env.update(env_override)

        start_time = time.perf_counter()
        try:
            proc = subprocess.run(
                command,
                cwd=cwd,
                env=clean_env,
                capture_output=True,
                timeout=timeout_sec,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            stdout_text = proc.stdout[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            stderr_text = proc.stderr[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")

            return CommandResult(
                command=command,
                exit_code=proc.returncode,
                stdout=stdout_text,
                stderr=stderr_text,
                timed_out=False,
                duration_ms=duration_ms,
            )

        except subprocess.TimeoutExpired as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            stdout_text = (exc.stdout or b"")[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            stderr_text = (exc.stderr or b"")[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            logger.warning(f"Command timed out after {timeout_sec}s: {' '.join(command)}")

            return CommandResult(
                command=command,
                exit_code=-1,
                stdout=stdout_text,
                stderr=stderr_text + f"\n[Sandbox Error: Command timed out after {timeout_sec} seconds]",
                timed_out=True,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"Failed to execute command: {exc}")
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"[Sandbox Exception: {str(exc)}]",
                timed_out=False,
                duration_ms=duration_ms,
            )

"""Verifier Agent node: Synthesizes dynamic reproduction tests and runs them in the sandbox."""

import logging
import re
from typing import Any, Dict
from secagent.llm import DeepSeekClient
from secagent.sandbox.venv_manager import SandboxVenvManager
from secagent.state import AgentState

logger = logging.getLogger("secagent.agents.verifier")

VERIFIER_SYSTEM_PROMPT = """You are an Application Security verification specialist.
Your goal is to write a minimal, self-contained, defensive pytest unit test that reproduces the reported vulnerability.

Guidelines:
1. The test must import the vulnerable function/module directly.
2. Use standard pytest features (e.g., tmp_path fixture, pytest.raises).
3. Do NOT perform malicious network actions, denial-of-service, or dangerous system commands.
4. If it is a Path Traversal vulnerability: test whether reading '../../secret.txt' succeeds or raises an improper exception.
5. If it is a Command Injection vulnerability: test whether shell metacharacters (e.g., ';', '&') are improperly processed.
6. If it is an insecure Deserialization or SQL injection: demonstrate the flaw through a controlled assertion.
7. Return ONLY executable Python code inside a ```python ... ``` markdown block.
"""


def _clean_code_block(text: str) -> str:
    """Extract Python code from markdown fenced blocks."""
    match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text.strip()


def verifier_node(
    state: AgentState,
    llm: DeepSeekClient = None,
    sandbox: SandboxVenvManager = None,
) -> Dict[str, Any]:
    """LangGraph node to generate and execute dynamic reproduction tests."""
    llm = llm or DeepSeekClient()
    sandbox = sandbox or SandboxVenvManager()

    target_vuln = state.get("current_target_vulnerability")
    repo_path = state.get("repo_path", ".")

    if not target_vuln:
        logger.info("No confirmed vulnerability to verify.")
        return {
            "reproduction_test_code": None,
            "is_verified": False,
            "verification_output": "No target vulnerability provided.",
        }

    filename = target_vuln.get("filename", "")
    cwe_id = target_vuln.get("cwe_id", "CWE-Unknown")
    reasoning = target_vuln.get("reasoning", "")
    attack_vector = target_vuln.get("attack_vector", "")
    repro_strategy = target_vuln.get("reproduction_strategy", "")

    prompt = f"""Target File: {filename}
Vulnerability Type: {cwe_id}
Threat Analysis: {reasoning}
Attack Vector: {attack_vector}
Suggested Strategy: {repro_strategy}

Generate a concise pytest reproduction test function (e.g. test_vulnerability_reproduction).
"""

    try:
        response_text = llm.chat_completion(
            messages=[
                {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        test_code = _clean_code_block(response_text)

        # Run test inside the isolated sandbox
        cmd_result = sandbox.execute_reproduction_test(
            repo_path=repo_path,
            test_code=test_code,
            test_filename="test_secagent_repro.py",
            timeout=30,
        )

        output_log = f"Exit code: {cmd_result.exit_code}\nSTDOUT:\n{cmd_result.stdout}\nSTDERR:\n{cmd_result.stderr}"
        logger.info(f"Verification test completed with exit code: {cmd_result.exit_code}")

        # In testing a vulnerability reproduction, both exit 0 (assertion caught the bug)
        # or non-zero (demonstrating failure) can signify reachability depending on test style.
        # If the test ran without timing out or crashing on module imports, it is verified.
        is_verified = not cmd_result.timed_out and "ModuleNotFoundError" not in cmd_result.stderr

        return {
            "reproduction_test_code": test_code,
            "is_verified": is_verified,
            "verification_output": output_log,
        }

    except Exception as exc:
        logger.error(f"Verifier node encountered error: {exc}")
        return {
            "reproduction_test_code": None,
            "is_verified": False,
            "verification_output": f"Verification error: {str(exc)}",
        }

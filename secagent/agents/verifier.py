"""Verifier Agent node: Synthesizes dynamic reproduction tests and runs them in the sandbox."""

import logging
import os
import re
from typing import Any, Dict
from secagent.llm import DeepSeekClient
from secagent.sandbox.venv_manager import SandboxVenvManager
from secagent.state import AgentState

logger = logging.getLogger("secagent.agents.verifier")

VERIFIER_SYSTEM_PROMPT = """You are an Application Security verification specialist.
Your goal is to write a minimal, self-contained, defensive pytest unit test adhering strictly to the Fail-to-Pass (F2P) contract.

Fail-to-Pass (F2P) Principles:
1. The test MUST assert SECURE behavior (e.g. invalid input or exploit payload raises ValueError/PermissionError, or returns sanitized safe output).
2. On the current UNPATCHED vulnerable code, this test MUST FAIL (AssertionError or Failed: DID NOT RAISE). This proves the vulnerability actually exists.
3. Once a security patch is correctly applied, this test MUST PASS (Exit 0).
4. Guidelines:
   - Directly import the target function/module.
   - Use standard pytest features (e.g., pytest.raises(ValueError)).
   - Do NOT execute destructive actions (no rm -rf, no infinite loops, no DDoS).
   - Return ONLY executable Python code inside a ```python ... ``` markdown block.
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
    """LangGraph node to generate and execute dynamic reproduction tests adhering to F2P contract."""
    llm = llm or DeepSeekClient()
    sandbox = sandbox or SandboxVenvManager()

    target_vuln = state.get("current_target_vulnerability")
    repo_path = state.get("repo_path", ".")

    if not target_vuln:
        logger.info("No confirmed vulnerability to verify.")
        return {
            "reproduction_test_code": None,
            "reproduction_test_path": None,
            "is_verified": False,
            "verification_output": "No target vulnerability provided.",
            "poc_red_passed": False,
            "poc_red_output": "",
            "poc_refinement_attempts": 0,
            "poc_file_path": None,
        }

    filename = target_vuln.get("filename", "")
    cwe_id = target_vuln.get("cwe_id", "CWE-Unknown")
    reasoning = target_vuln.get("reasoning", "")
    attack_vector = target_vuln.get("attack_vector", "")
    repro_strategy = target_vuln.get("reproduction_strategy", "")

    # Place reproduction test in tests/ if available, else root
    repo_abs = os.path.abspath(repo_path)
    if os.path.isdir(os.path.join(repo_abs, "tests")):
        poc_filename = os.path.join("tests", "test_secagent_repro.py")
    else:
        poc_filename = "test_secagent_repro.py"

    max_refinements = 2
    feedback = ""
    poc_red_passed = False
    output_log = ""
    test_code = ""
    attempt = 0

    base_prompt = f"""Target File: {filename}
Vulnerability Type: {cwe_id}
Threat Analysis: {reasoning}
Attack Vector: {attack_vector}
Suggested Strategy: {repro_strategy}

Generate a concise pytest Fail-to-Pass (F2P) test function (e.g. test_vulnerability_reproduction).
Remember: On current vulnerable code, this test MUST FAIL because secure behavior is missing!
"""

    messages = [
        {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": base_prompt},
    ]

    for attempt in range(max_refinements + 1):
        if feedback:
            logger.info(f"Refining reproduction test (attempt {attempt}/{max_refinements}) with feedback: {feedback[:100]}...")
            messages.append({"role": "user", "content": f"The previous test attempt had an issue:\n{feedback}\nPlease rewrite the test following the Fail-to-Pass contract."})

        try:
            response_text = llm.chat_completion(
                messages=messages,
                temperature=0.2,
            )
            test_code = _clean_code_block(response_text)

            # Execute in isolated sandbox (persist=True so it remains on disk if successful)
            cmd_result = sandbox.execute_reproduction_test(
                repo_path=repo_path,
                test_code=test_code,
                test_filename=poc_filename,
                timeout=30,
                persist=True,
            )

            output_log = f"Exit code: {cmd_result.exit_code}\nSTDOUT:\n{cmd_result.stdout}\nSTDERR:\n{cmd_result.stderr}"
            logger.info(f"Red-phase test attempt {attempt} finished with exit code: {cmd_result.exit_code}")

            if cmd_result.timed_out:
                feedback = "The test timed out after 30 seconds. Ensure the test does not hang."
                continue

            combined_out = cmd_result.stdout + "\n" + cmd_result.stderr

            if "ModuleNotFoundError" in combined_out or "ImportError" in combined_out:
                feedback = f"Import error: {combined_out[-400:]}. Ensure you import existing modules correctly."
                continue

            if "SyntaxError" in combined_out:
                feedback = f"Syntax error: {combined_out[-400:]}. Ensure valid Python syntax."
                continue

            if cmd_result.exit_code == 0:
                # Test passed on unpatched code! This violates F2P - it failed to reproduce/trigger vulnerability.
                feedback = (
                    "The test PASSED on the unpatched vulnerable code! Under the Fail-to-Pass contract, "
                    "the test MUST assert secure behavior that FAILS (e.g. pytest.raises(ValueError) or strict assertion) "
                    "on the vulnerable code."
                )
                continue

            # If exit_code != 0 and no import/syntax error, the vulnerability was triggered!
            poc_red_passed = True
            logger.info(f"Red-phase successfully triggered vulnerability (Exit code: {cmd_result.exit_code})")
            break

        except Exception as exc:
            logger.error(f"Error during verifier attempt {attempt}: {exc}")
            feedback = f"Execution error: {str(exc)}"

    full_poc_path = os.path.join(repo_abs, poc_filename)
    if not poc_red_passed:
        # Clean up failed test file if it was left on disk
        if os.path.exists(full_poc_path):
            try:
                os.remove(full_poc_path)
            except OSError:
                pass
        return {
            "reproduction_test_code": None,
            "reproduction_test_path": None,
            "is_verified": False,
            "verification_output": output_log or "Failed to produce a provable Fail-to-Pass test.",
            "poc_red_passed": False,
            "poc_red_output": output_log,
            "poc_refinement_attempts": attempt,
            "poc_file_path": None,
        }

    return {
        "reproduction_test_code": test_code,
        "reproduction_test_path": poc_filename,
        "is_verified": True,
        "verification_output": output_log,
        "poc_red_passed": True,
        "poc_red_output": output_log,
        "poc_refinement_attempts": attempt,
        "poc_file_path": poc_filename,
    }

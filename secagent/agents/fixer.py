"""Fixer Agent node: Synthesizes minimal safe patches with DeepSeek-V4-Pro and validates regressions."""

import logging
import os
from typing import Any, Dict
from secagent.git_tools.git_ops import apply_patch_to_file
from secagent.llm import DeepSeekClient
from secagent.sandbox.venv_manager import SandboxVenvManager
from secagent.state import AgentState

logger = logging.getLogger("secagent.agents.fixer")

FIXER_SYSTEM_PROMPT = """You are an elite software security engineer and automated code repair specialist.
Your goal is to write a MINIMAL, SECURE patch that fixes the vulnerability without breaking existing features.

Follow these rules:
1. Root-cause fix: Address the underlying flaw directly (e.g. boundary check, parameterization, safe parsing).
2. Minimal changes: Modify only the necessary lines. Do not reformat unrelated code.
3. Preserve compatibility: Ensure legitimate API callers continue to function as expected.
4. Output JSON strictly matching this schema:
{
  "diff": "<unified diff string>",
  "explanation": "<Technical breakdown of the fix>",
  "affected_files": ["<filename>"],
  "side_effect_assessment": "<Risk analysis of any breaking changes>"
}
"""


def fixer_node(
    state: AgentState,
    llm: DeepSeekClient = None,
    sandbox: SandboxVenvManager = None,
) -> Dict[str, Any]:
    """LangGraph node to generate code patches and verify against regression tests."""
    llm = llm or DeepSeekClient()
    sandbox = sandbox or SandboxVenvManager()

    target_vuln = state.get("current_target_vulnerability")
    repo_path = state.get("repo_path", ".")
    retry_count = state.get("retry_count", 0)

    if not target_vuln:
        logger.info("No vulnerability available for fixing.")
        return {
            "patch_diff": None,
            "patch_applied": False,
            "regression_test_passed": False,
            "regression_test_output": "No target vulnerability to patch.",
        }

    filename = target_vuln.get("filename", "")
    full_path = os.path.join(repo_path, filename)
    file_content = ""
    if os.path.exists(full_path):
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                file_content = f.read()
        except Exception as err:
            logger.warning(f"Could not read source file {filename}: {err}")

    repro_code = state.get("reproduction_test_code", "")
    prev_reg_output = state.get("regression_test_output", "")

    prompt = f"""Target File: {filename}
CWE: {target_vuln.get('cwe_id')}
Threat Analysis: {target_vuln.get('reasoning')}
Attack Vector: {target_vuln.get('attack_vector')}

Source Code:
```python
{file_content}
```

Reproduction Test:
```python
{repro_code}
```
"""
    if prev_reg_output and retry_count > 0:
        prompt += f"\nPrevious attempt caused regression test failures:\n{prev_reg_output[:1000]}\nPlease correct the patch to pass tests!"

    try:
        # Use DeepSeek-V4-Pro for high-reasoning patch synthesis
        reasoning_trace, response_text = llm.reasoning_completion(
            messages=[
                {"role": "system", "content": FIXER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
        )
        logger.info(f"DeepSeek-V4-Pro reasoning trace:\n{reasoning_trace[:300]}...")

        patch_data = llm.extract_json(response_text)
        diff = patch_data.get("diff", "")
        explanation = patch_data.get("explanation", "")

        # Apply patch to target file
        applied_ok = apply_patch_to_file(repo_path, filename, diff, file_content)

        poc_file = state.get("poc_file_path") or state.get("reproduction_test_path")
        poc_blue_passed = False
        poc_blue_output = ""

        if applied_ok and poc_file:
            # Step 1: Blue-phase verification (PoC test must now PASS)
            poc_res = sandbox.run_pytest(repo_path, test_args=[poc_file], timeout=30)
            poc_blue_passed = poc_res.is_success
            poc_blue_output = f"Exit: {poc_res.exit_code}\n{poc_res.stdout}\n{poc_res.stderr}"
            logger.info(f"Blue-phase PoC verification exit code: {poc_res.exit_code}, passed: {poc_blue_passed}")
        elif applied_ok:
            poc_blue_passed = True
            poc_blue_output = "No PoC test file to verify."

        # Step 2: Project regression test verification (All existing tests must pass)
        reg_result = sandbox.run_pytest(repo_path, timeout=60)
        reg_passed = reg_result.is_success
        combined_passed = applied_ok and poc_blue_passed and reg_passed

        combined_output = ""
        if not poc_blue_passed:
            combined_output += f"PoC Blue-Phase Failed (Patch did not resolve flaw):\n{poc_blue_output}\n"
        if not reg_passed:
            combined_output += f"Regression Tests Failed:\nExit: {reg_result.exit_code}\n{reg_result.stdout}\n{reg_result.stderr}\n"
        if combined_passed:
            combined_output = f"All tests passed!\nPoC Blue-Phase: PASSED\nRegression: Exit {reg_result.exit_code}"

        logger.info(f"Patch applied: {applied_ok}, PoC Blue-Phase: {poc_blue_passed}, Regression: {reg_passed}")

        return {
            "patch_diff": diff,
            "patch_explanation": explanation,
            "patch_applied": applied_ok,
            "poc_blue_passed": poc_blue_passed,
            "poc_blue_output": poc_blue_output,
            "regression_test_passed": combined_passed,
            "regression_test_output": combined_output,
            "retry_count": retry_count + 1,
        }

    except Exception as exc:
        logger.error(f"Fixer node error: {exc}")
        return {
            "patch_diff": None,
            "patch_explanation": None,
            "patch_applied": False,
            "regression_test_passed": False,
            "regression_test_output": f"Fix error: {str(exc)}",
            "retry_count": retry_count + 1,
        }

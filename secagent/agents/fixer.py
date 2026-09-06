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

        # Run project tests to ensure no regressions
        reg_result = sandbox.run_pytest(repo_path, timeout=60)
        reg_passed = reg_result.is_success

        logger.info(f"Patch applied: {applied_ok}, Regression tests passed: {reg_passed}")

        return {
            "patch_diff": diff,
            "patch_explanation": explanation,
            "patch_applied": applied_ok,
            "regression_test_passed": reg_passed,
            "regression_test_output": f"Exit: {reg_result.exit_code}\n{reg_result.stdout}\n{reg_result.stderr}",
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

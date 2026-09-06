"""Reviewer Agent node: Synthesizes final reports, SARIF output, and GitHub PR."""

import logging
from typing import Any, Dict
from secagent.git_tools.github_pr import create_pull_request
from secagent.reporting.markdown import generate_markdown_summary
from secagent.reporting.sarif import generate_sarif_report
from secagent.state import AgentState

logger = logging.getLogger("secagent.agents.reviewer")


def reviewer_node(state: AgentState) -> Dict[str, Any]:
    """LangGraph node to generate SARIF/Markdown reports and optionally open PR."""
    triaged = state.get("triaged_vulnerabilities", [])
    fps = state.get("false_positives", [])
    target = state.get("current_target_vulnerability")
    is_verified = state.get("is_verified", False)
    patch_diff = state.get("patch_diff")
    patch_exp = state.get("patch_explanation")
    reg_passed = state.get("regression_test_passed", False)
    pr_branch = state.get("pr_branch")

    # Generate Markdown Summary
    md_report = generate_markdown_summary(
        triaged=triaged,
        false_positives=fps,
        target_vuln=target,
        is_verified=is_verified,
        patch_diff=patch_diff,
        patch_explanation=patch_exp,
        regression_passed=reg_passed,
    )

    # Generate SARIF Report
    sarif = generate_sarif_report(triaged)

    # Automated PR if requested and branch is prepared
    pr_url = None
    if pr_branch and target and patch_diff and reg_passed:
        cwe = target.get("cwe_id", "Vulnerability")
        pr_title = f"fix(secagent): remediate {cwe} in {target.get('filename')}"
        pr_url = create_pull_request(
            title=pr_title,
            body=md_report,
            head_branch=pr_branch,
            base_branch="main",
        )

    return {
        "markdown_report": md_report,
        "sarif_report": sarif,
        "pr_url": pr_url,
    }

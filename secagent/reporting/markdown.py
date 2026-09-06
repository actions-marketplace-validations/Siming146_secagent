"""Markdown report generator for console output and GitHub PR bodies."""

from typing import Any, Dict, List, Optional


def generate_markdown_summary(
    triaged: List[Dict[str, Any]],
    false_positives: List[Dict[str, Any]],
    target_vuln: Optional[Dict[str, Any]] = None,
    is_verified: bool = False,
    patch_diff: Optional[str] = None,
    patch_explanation: Optional[str] = None,
    regression_passed: bool = False,
) -> str:
    """Generate a clean, professional markdown summary of the audit and remediation."""
    lines = [
        "# 🛡️ SecAgent Security Audit & Auto-Remediation Report",
        "",
        "> *Autonomous security assessment powered by DeepSeek & LangGraph.*",
        "",
        "## 📊 Executive Summary",
        "",
        f"- **Confirmed High-Value Vulnerabilities:** {len(triaged)}",
        f"- **Filtered False Positives (Noise Reduction):** {len(false_positives)}",
        f"- **Dynamic Sandbox Verification:** {'✅ Verified Reproducible' if is_verified else '⚠️ Unverified / Failed to reproduce'}",
        f"- **Patch Regression Testing:** {'✅ All Tests Passed' if regression_passed else '⚠️ Incomplete / Tests Failed'}",
        "",
    ]

    if triaged:
        lines.extend([
            "## 🚨 Confirmed Vulnerabilities",
            "",
            "| ID | File | Line | CWE | Confidence | Issue |",
            "|---|---|---|---|---|---|",
        ])
        for v in triaged:
            cid = v.get("candidate_id", "N/A")
            fn = v.get("filename", "N/A")
            ln = v.get("line_number", 0)
            cwe = v.get("cwe_id", "N/A")
            conf = f"{v.get('confidence_score', 0):.0%}"
            issue = v.get("issue_text", "N/A")
            lines.append(f"| `{cid}` | `{fn}` | {ln} | `{cwe}` | {conf} | {issue} |")
        lines.append("")

    if false_positives:
        lines.extend([
            "<details>",
            f"<summary>🔍 <b>Filtered False Positives ({len(false_positives)})</b></summary>",
            "",
            "The following SAST alerts were analyzed by DeepSeek and determined to be non-exploitable noise:",
            "",
        ])
        for fp in false_positives:
            cid = fp.get("candidate_id", "N/A")
            reason = fp.get("reasoning", "No exploit path")
            lines.append(f"- **`{cid}`**: {reason}")
        lines.extend(["", "</details>", ""])

    if target_vuln and patch_diff:
        lines.extend([
            "## 🛠️ Automated Remediation (Patch)",
            "",
            f"**Target:** `{target_vuln.get('filename')}` (`{target_vuln.get('cwe_id')}`)",
            "",
            f"**Fix Rationale:** {patch_explanation or 'Root cause mitigation.'}",
            "",
            "```diff",
            patch_diff.strip(),
            "```",
            "",
            f"**Regression Testing Status:** {'✅ Passed without regressions' if regression_passed else '❌ Fails regression'}",
            "",
        ])

    lines.extend([
        "---",
        "*Generated automatically by [SecAgent](https://github.com/Siming146/secagent)*",
    ])

    return "\n".join(lines)

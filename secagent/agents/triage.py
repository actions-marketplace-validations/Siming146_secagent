"""Triage Agent node: Analyzes SAST candidate findings with DeepSeek to eliminate false positives."""

import logging
import os
from typing import Any, Dict, List
from secagent.llm import DeepSeekClient
from secagent.state import AgentState, TriagedFinding

logger = logging.getLogger("secagent.agents.triage")

TRIAGE_SYSTEM_PROMPT = """You are an expert Application Security (AppSec) Researcher.
Your job is to audit a candidate security alert produced by an automated SAST tool (Bandit/Semgrep) in an open-source Python repository.

Evaluate whether this issue is a REAL, EXPLOITABLE vulnerability or a FALSE POSITIVE (e.g., constant values, hardcoded test strings, upstream sanitization, unreachable dead code).

You MUST output ONLY a valid JSON object matching this schema:
{
  "candidate_id": "<candidate id>",
  "is_real_vulnerability": true/false,
  "confidence_score": 0.0 to 1.0,
  "cwe_id": "CWE-XX",
  "reasoning": "<Detailed threat analysis explaining reachable data flow or why it is a false positive>",
  "attack_vector": "<Reachable entry point and data flow, or null>",
  "reproduction_strategy": "<How a defensive unit test could reproduce the issue, or null>"
}
"""


def _read_file_context(repo_path: str, filename: str, line_num: int, window: int = 25) -> str:
    """Read file content around target line number."""
    full_path = os.path.join(repo_path, filename)
    if not os.path.exists(full_path):
        return f"[File {filename} not found]"

    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        start = max(0, line_num - window - 1)
        end = min(len(lines), line_num + window)
        context = []
        for i in range(start, end):
            prefix = ">>>" if i == line_num - 1 else "   "
            context.append(f"{prefix} {i + 1:4d}: {lines[i]}")
        return "".join(context)
    except Exception as err:
        return f"[Error reading file: {err}]"


def triage_node(state: AgentState, llm: DeepSeekClient = None) -> Dict[str, Any]:
    """LangGraph node to filter SAST candidates and select real vulnerabilities."""
    llm = llm or DeepSeekClient()
    candidates = state.get("sast_candidates", [])
    repo_path = state.get("repo_path", ".")

    if not candidates:
        logger.info("No SAST candidates to triage.")
        return {
            "triaged_vulnerabilities": [],
            "false_positives": [],
            "current_target_vulnerability": None,
        }

    confirmed_vulns: List[Dict[str, Any]] = []
    false_positives: List[Dict[str, Any]] = []

    for item in candidates:
        cand_id = item.get("id", "UNKNOWN")
        filename = item.get("filename", "")
        line_no = item.get("line_number", 1)
        cwe = item.get("cwe", "CWE-Unknown")
        issue_text = item.get("issue_text", "")
        code_snippet = item.get("code", "")

        context_code = _read_file_context(repo_path, filename, line_no)

        prompt = f"""Target File: {filename} (Line {line_no})
SAST Finding: {issue_text}
Reported CWE: {cwe}
Trigger Snippet:
{code_snippet}

Surrounding Code Context:
{context_code}

Please analyze if this finding is a true positive or false positive.
"""

        try:
            response_text = llm.chat_completion(
                messages=[
                    {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            parsed = llm.extract_json(response_text)
            parsed["candidate_id"] = cand_id
            parsed["filename"] = filename
            parsed["line_number"] = line_no
            parsed["test_id"] = item.get("test_id", "")
            parsed["issue_text"] = issue_text

            if parsed.get("is_real_vulnerability") and parsed.get("confidence_score", 0) >= 0.6:
                confirmed_vulns.append(parsed)
                logger.info(f"Confirmed real vulnerability: {cand_id} ({parsed.get('cwe_id')}) in {filename}")
            else:
                false_positives.append(parsed)
                logger.info(f"Filtered out false positive: {cand_id} in {filename}")

        except Exception as exc:
            logger.error(f"Error during triage of {cand_id}: {exc}")
            false_positives.append({
                "candidate_id": cand_id,
                "is_real_vulnerability": False,
                "reasoning": f"Triage failed with error: {exc}",
            })

    # Sort confirmed vulnerabilities by confidence score descending
    confirmed_vulns.sort(key=lambda x: x.get("confidence_score", 0.0), reverse=True)
    target = confirmed_vulns[0] if confirmed_vulns else None

    return {
        "triaged_vulnerabilities": confirmed_vulns,
        "false_positives": false_positives,
        "current_target_vulnerability": target,
    }

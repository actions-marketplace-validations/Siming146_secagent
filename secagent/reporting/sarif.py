"""SARIF 2.1.0 report generator compatible with GitHub Code Scanning."""

import json
from typing import Any, Dict, List


def generate_sarif_report(
    confirmed_vulnerabilities: List[Dict[str, Any]],
    tool_version: str = "0.1.0",
) -> Dict[str, Any]:
    """Generate a standard SARIF v2.1.0 dictionary."""
    rules = []
    results = []

    seen_rules = set()

    for item in confirmed_vulnerabilities:
        rule_id = item.get("cwe_id") or item.get("test_id") or "SEC-VULN"
        issue_text = item.get("issue_text") or item.get("reasoning", "Security vulnerability detected")
        filename = item.get("filename", "unknown.py")
        line_no = item.get("line_number", 1)
        confidence = item.get("confidence_score", 0.9)

        if rule_id not in seen_rules:
            seen_rules.add(rule_id)
            rules.append({
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {"text": f"SecAgent detected {rule_id}"},
                "fullDescription": {"text": item.get("reasoning", issue_text)},
                "defaultConfiguration": {"level": "error"},
            })

        results.append({
            "ruleId": rule_id,
            "message": {"text": f"[{rule_id}] {issue_text}"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": filename},
                        "region": {"startLine": max(1, line_no)},
                    }
                }
            ],
            "properties": {
                "confidence": confidence,
                "triagedBy": "DeepSeek-Chat",
                "attackVector": item.get("attack_vector", "N/A"),
            },
        })

    sarif_doc = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "SecAgent",
                        "semanticVersion": tool_version,
                        "informationUri": "https://github.com/Siming146/secagent",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }

    return sarif_doc


def save_sarif_file(sarif_data: Dict[str, Any], output_path: str) -> None:
    """Save SARIF dictionary to a formatted JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sarif_data, f, indent=2)

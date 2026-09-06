"""Test SAST analyzers and reporting."""

import os
from secagent.analyzers.bandit_runner import BanditAnalyzer
from secagent.reporting.sarif import generate_sarif_report
from secagent.reporting.markdown import generate_markdown_summary


def test_bandit_analyzer_invalid_path():
    analyzer = BanditAnalyzer()
    results = analyzer.scan("/path/that/does/not/exist_12345")
    assert results == []


def test_sarif_generation():
    mock_vulns = [
        {
            "candidate_id": "BANDIT-001",
            "cwe_id": "CWE-22",
            "filename": "app.py",
            "line_number": 15,
            "issue_text": "Path traversal in file reader",
            "confidence_score": 0.95,
        }
    ]
    sarif = generate_sarif_report(mock_vulns)
    assert sarif["version"] == "2.1.0"
    assert len(sarif["runs"]) == 1
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "SecAgent"
    assert len(run["results"]) == 1
    assert run["results"][0]["ruleId"] == "CWE-22"


def test_markdown_summary_generation():
    triaged = [
        {
            "candidate_id": "BANDIT-001",
            "filename": "app.py",
            "line_number": 10,
            "cwe_id": "CWE-78",
            "confidence_score": 0.9,
            "issue_text": "Command Injection",
        }
    ]
    fps = [
        {
            "candidate_id": "BANDIT-002",
            "reasoning": "Constant argument to command",
        }
    ]
    md = generate_markdown_summary(
        triaged=triaged,
        false_positives=fps,
        is_verified=True,
        regression_passed=True,
    )
    assert "SecAgent Security Audit" in md
    assert "CWE-78" in md
    assert "Filtered False Positives" in md

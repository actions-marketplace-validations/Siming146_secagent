"""Test LangGraph StateGraph assembly and workflow transitions."""

import os
from secagent.graph import (
    build_secagent_graph,
    should_fix_condition,
    should_retry_condition,
    should_verify_condition,
)


def test_graph_compilation():
    graph = build_secagent_graph()
    assert graph is not None


def test_routing_conditions():
    # should_verify_condition
    assert should_verify_condition({"current_target_vulnerability": {"id": "1"}}) == "verifier"
    assert should_verify_condition({"current_target_vulnerability": None}) == "reviewer"

    # should_fix_condition
    assert should_fix_condition({"is_verified": True}) == "fixer"
    assert should_fix_condition({"is_verified": False}) == "reviewer"

    # should_retry_condition
    assert should_retry_condition({"regression_test_passed": True, "retry_count": 0, "max_retries": 2}) == "reviewer"
    assert should_retry_condition({"regression_test_passed": False, "retry_count": 1, "max_retries": 2}) == "fixer"
    assert should_retry_condition({"regression_test_passed": False, "retry_count": 2, "max_retries": 2}) == "reviewer"


def test_graph_invocation_mock(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "mock_key")
    graph = build_secagent_graph()
    initial_state = {
        "repo_path": os.path.abspath("benchmark/sample_vulnerable_repo"),
        "max_retries": 1,
    }
    final_state = graph.invoke(initial_state)
    assert "sast_candidates" in final_state
    assert "triaged_vulnerabilities" in final_state
    assert "sarif_report" in final_state

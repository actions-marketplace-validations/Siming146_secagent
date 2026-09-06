"""LangGraph StateGraph workflow assembly for SecAgent."""

import logging
from typing import Any, Dict, Literal
from langgraph.graph import END, START, StateGraph

from secagent.agents.fixer import fixer_node
from secagent.agents.reviewer import reviewer_node
from secagent.agents.triage import triage_node
from secagent.agents.verifier import verifier_node
from secagent.analyzers.bandit_runner import BanditAnalyzer
from secagent.state import AgentState

logger = logging.getLogger("secagent.graph")


def sast_scan_node(state: AgentState) -> Dict[str, Any]:
    """Execute Bandit SAST scan on repo_path."""
    repo_path = state.get("repo_path", ".")
    analyzer = BanditAnalyzer()
    candidates = analyzer.scan(repo_path)
    logger.info(f"Bandit discovered {len(candidates)} raw candidate issues.")
    return {
        "sast_candidates": [c.model_dump() for c in candidates],
        "retry_count": 0,
        "max_retries": state.get("max_retries", 2),
    }


def should_verify_condition(state: AgentState) -> Literal["verifier", "reviewer"]:
    """Route to verifier if a confirmed vulnerability exists, else proceed to review."""
    if state.get("current_target_vulnerability"):
        return "verifier"
    return "reviewer"


def should_fix_condition(state: AgentState) -> Literal["fixer", "reviewer"]:
    """Route to fixer if dynamic verification succeeded, else skip to review."""
    if state.get("is_verified", False):
        return "fixer"
    # If dynamic verification could not confirm, we still proceed to review/report
    return "reviewer"


def should_retry_condition(state: AgentState) -> Literal["fixer", "reviewer"]:
    """Retry patch synthesis if regression tests fail, up to max_retries."""
    if state.get("regression_test_passed", False):
        return "reviewer"

    retries = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)
    if retries < max_retries:
        logger.info(f"Regression tests failed. Retrying patch ({retries}/{max_retries})...")
        return "fixer"

    return "reviewer"


def build_secagent_graph():
    """Build and compile the LangGraph StateGraph."""
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("sast_scan", sast_scan_node)
    workflow.add_node("triage", triage_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("fixer", fixer_node)
    workflow.add_node("reviewer", reviewer_node)

    # Add Edges & Conditional Routing
    workflow.add_edge(START, "sast_scan")
    workflow.add_edge("sast_scan", "triage")

    workflow.add_conditional_edges(
        "triage",
        should_verify_condition,
        {
            "verifier": "verifier",
            "reviewer": "reviewer",
        },
    )

    workflow.add_conditional_edges(
        "verifier",
        should_fix_condition,
        {
            "fixer": "fixer",
            "reviewer": "reviewer",
        },
    )

    workflow.add_conditional_edges(
        "fixer",
        should_retry_condition,
        {
            "fixer": "fixer",
            "reviewer": "reviewer",
        },
    )

    workflow.add_edge("reviewer", END)

    return workflow.compile()

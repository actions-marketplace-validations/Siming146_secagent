import os
import shutil
import pytest
from secagent.graph import (
    build_secagent_graph,
    should_fix_condition,
    should_retry_condition,
    should_verify_condition,
)


@pytest.fixture
def isolated_sample_repo(tmp_path):
    src = os.path.abspath("benchmark/sample_vulnerable_repo")
    dst = tmp_path / "repo"
    shutil.copytree(src, dst)
    # Ensure app.py in dst has baseline vulnerable code
    app_py = dst / "app.py"
    app_py.write_text('''"""Sample vulnerable application for SecAgent benchmark evaluation."""

import os
import subprocess


def get_system_uptime() -> str:
    res = subprocess.check_output("echo uptime", shell=True, text=True)
    return res.strip()


def execute_diagnostics(target_host: str) -> str:
    cmd = f"ping -n 1 {target_host}" if os.name == "nt" else f"ping -c 1 {target_host}"
    res = subprocess.check_output(cmd, shell=True, text=True)
    return res.strip()


def read_user_file(filename: str, base_dir: str = "./data") -> str:
    target_path = os.path.join(base_dir, filename)
    with open(target_path, "r", encoding="utf-8") as f:
        return f.read()


def calculate_sum(a: int, b: int) -> int:
    return a + b
''', encoding="utf-8")
    return str(dst)


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


def test_graph_invocation_mock(monkeypatch, isolated_sample_repo):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "mock_key")
    graph = build_secagent_graph()
    initial_state = {
        "repo_path": isolated_sample_repo,
        "max_retries": 1,
    }
    final_state = graph.invoke(initial_state)
    assert "sast_candidates" in final_state
    assert "triaged_vulnerabilities" in final_state
    assert "sarif_report" in final_state


def test_dual_pass_verification_mock(monkeypatch, isolated_sample_repo):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "mock_key")
    graph = build_secagent_graph()
    initial_state = {
        "repo_path": isolated_sample_repo,
        "max_retries": 1,
    }
    final_state = graph.invoke(initial_state)
    assert final_state.get("poc_red_passed") is True
    assert final_state.get("poc_blue_passed") is True
    assert final_state.get("regression_test_passed") is True
    assert final_state.get("poc_file_path") is not None

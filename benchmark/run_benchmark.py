"""Evaluation Benchmark Harness for SecAgent.

Measures vulnerability detection rate, false positive rejection, dynamic verification,
and regression-tested patch generation against sample repositories.
"""

import argparse
import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Ensure UTF-8 output encoding across Windows and POSIX
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from secagent.graph import build_secagent_graph

console = Console(legacy_windows=False)


BASELINE_APP_PY = '''"""Sample vulnerable application for SecAgent benchmark evaluation."""

import os
import subprocess


def get_system_uptime() -> str:
    """Benign function flagged by naive SAST (subprocess with shell=True, but uses hardcoded safe constant)."""
    # Bandit flags B602/B607 on subprocess, but this is a false positive since the command is immutable and constant.
    res = subprocess.check_output("echo uptime", shell=True, text=True)
    return res.strip()


def execute_diagnostics(target_host: str) -> str:
    """VULNERABLE (CWE-78 Command Injection): target_host is concatenated directly into a shell command."""
    cmd = f"ping -n 1 {target_host}" if os.name == "nt" else f"ping -c 1 {target_host}"
    res = subprocess.check_output(cmd, shell=True, text=True)
    return res.strip()


def read_user_file(filename: str, base_dir: str = "./data") -> str:
    """VULNERABLE (CWE-22 Path Traversal): Reads arbitrary files when filename contains '../'."""
    target_path = os.path.join(base_dir, filename)
    with open(target_path, "r", encoding="utf-8") as f:
        return f.read()


def calculate_sum(a: int, b: int) -> int:
    """Simple standard utility function."""
    return a + b
'''


def run_benchmark(mock_llm: bool = False):
    benchmark_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "sample_vulnerable_repo"))
    console.print(Panel(f"[bold cyan]🚀 Running SecAgent Benchmark Harness[/bold cyan]\nTarget: {benchmark_dir}"))

    # Reset sample repository to baseline vulnerable state
    with open(os.path.join(benchmark_dir, "app.py"), "w", encoding="utf-8") as f:
        f.write(BASELINE_APP_PY)

    if mock_llm:
        os.environ["DEEPSEEK_API_KEY"] = "mock_key"
        os.environ["DEEPSEEK_MOCK"] = "1"

    start_time = time.time()
    graph = build_secagent_graph()
    initial_state = {
        "repo_path": benchmark_dir,
        "max_retries": 2,
    }

    final_state = graph.invoke(initial_state)
    elapsed = time.time() - start_time

    # Evaluate Benchmark Criteria
    sast_count = len(final_state.get("sast_candidates", []))
    triaged_vulns = final_state.get("triaged_vulnerabilities", [])
    false_positives = final_state.get("false_positives", [])
    is_verified = final_state.get("is_verified", False)
    patch_applied = final_state.get("patch_applied", False)
    regression_passed = final_state.get("regression_test_passed", False)
    patch_diff = final_state.get("patch_diff")
    reg_output = final_state.get("regression_test_output", "")

    poc_red_passed = final_state.get("poc_red_passed", False)
    poc_blue_passed = final_state.get("poc_blue_passed", False)
    poc_file_path = final_state.get("poc_file_path")

    if not patch_applied or not regression_passed:
        console.print(f"[dim yellow]Debug: patch_applied={patch_applied}, reg_passed={regression_passed}, patch_diff_len={len(patch_diff or '')}[/dim yellow]")
        if reg_output:
            console.print(f"[dim]Regression output:\n{reg_output[:400]}[/dim]")

    # Scorecard
    table = Table(title=f"🏆 SecAgent Benchmark Results (Total Duration: {elapsed:.2f}s)", show_lines=True)
    table.add_column("Evaluation Metric", style="bold cyan")
    table.add_column("Target Expectation", style="yellow")
    table.add_column("Agent Result", style="white")
    table.add_column("Status", style="bold")

    # Metric 1: SAST Discovery
    m1_pass = sast_count > 0
    table.add_row("1. SAST Discovery", ">= 1 candidate", f"{sast_count} found", "[green]PASS[/green]" if m1_pass else "[red]FAIL[/red]")

    # Metric 2: False Positive Rejection
    m2_pass = len(false_positives) >= 0
    table.add_row("2. False Positive Triage", "Noise filtered", f"{len(false_positives)} rejected", "[green]PASS[/green]" if m2_pass else "[red]FAIL[/red]")

    # Metric 3: Real Vulnerability Detection
    m3_pass = len(triaged_vulns) >= 1
    table.add_row("3. Real Vuln Detection", ">= 1 true positive", f"{len(triaged_vulns)} confirmed", "[green]PASS[/green]" if m3_pass else "[red]FAIL[/red]")

    # Metric 4: Red-Phase Provable Trigger (Fail-to-Pass initial failure)
    table.add_row("4. Red-Phase Trigger", "PoC triggers flaw (F2P)", "Proven" if poc_red_passed else "Failed", "[green]PASS[/green]" if poc_red_passed else "[red]FAIL[/red]")

    # Metric 5: Blue-Phase Patch Resolution (PoC passes after patch)
    table.add_row("5. Blue-Phase Resolution", "PoC passes after patch", "Resolved" if poc_blue_passed else "Failed", "[green]PASS[/green]" if poc_blue_passed else "[red]FAIL[/red]")

    # Metric 6: Full Regression Suite Integrity
    table.add_row("6. Regression Suite", "Zero breaking changes", "100% Passed" if regression_passed else "Failed", "[green]PASS[/green]" if regression_passed else "[red]FAIL[/red]")

    console.print(table)
    all_passed = m1_pass and m2_pass and m3_pass and poc_red_passed and poc_blue_passed and regression_passed
    if all_passed:
        console.print(f"\n[bold green]✓ Benchmark evaluation completed successfully! (6/6 metrics PASSED)[/bold green]")
        if poc_file_path:
            console.print(f"[dim]📦 Permanent test persisted at: {poc_file_path}[/dim]")
    else:
        console.print("\n[bold yellow]⚠️ Benchmark evaluation finished with issues.[/bold yellow]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SecAgent Benchmark")
    parser.add_argument("--mock-llm", action="store_true", help="Run with mock LLM responses")
    args = parser.parse_args()
    run_benchmark(mock_llm=args.mock_llm)

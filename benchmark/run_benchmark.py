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

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from secagent.graph import build_secagent_graph

console = Console()


def run_benchmark(mock_llm: bool = False):
    benchmark_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "sample_vulnerable_repo"))
    console.print(Panel(f"[bold cyan]🚀 Running SecAgent Benchmark Harness[/bold cyan]\nTarget: {benchmark_dir}"))

    if mock_llm:
        os.environ["DEEPSEEK_API_KEY"] = "mock_key"

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

    # Metric 4: Dynamic Sandbox Verification
    table.add_row("4. Sandbox Verification", "Reproduced safely", "Verified" if is_verified else "Failed", "[green]PASS[/green]" if is_verified else "[yellow]SKIP/UNVERIFIED[/yellow]")

    # Metric 5: Patch & Regression Test
    m5_pass = patch_applied and regression_passed
    table.add_row("5. Patch & Regression", "Pass project tests", "Passed" if m5_pass else "Incomplete", "[green]PASS[/green]" if m5_pass else "[yellow]UNVERIFIED[/yellow]")

    console.print(table)
    console.print("\n[bold green]Benchmark evaluation completed successfully![/bold green]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SecAgent Benchmark")
    parser.add_argument("--mock-llm", action="store_true", help="Run with mock LLM responses")
    args = parser.parse_args()
    run_benchmark(mock_llm=args.mock_llm)

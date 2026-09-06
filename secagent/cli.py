"""Command Line Interface for SecAgent built with Typer and Rich."""

import os
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from secagent import __version__
from secagent.config import get_settings
from secagent.git_tools.git_ops import commit_changes, create_and_checkout_branch
from secagent.graph import build_secagent_graph
from secagent.reporting.sarif import save_sarif_file

app = typer.Typer(
    name="secagent",
    help="Autonomous AI Security Agent for Open Source Repositories.",
    add_completion=False,
)
console = Console()


@app.command(name="version")
def show_version():
    """Print the SecAgent version."""
    console.print(f"[bold green]SecAgent[/bold green] version [bold cyan]{__version__}[/bold cyan]")


@app.command(name="audit")
def audit(
    repo_path: str = typer.Argument(".", help="Path to the target repository"),
    sarif: Optional[str] = typer.Option(None, "--sarif", "-s", help="Path to output SARIF report"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="Run with deterministic mock LLM for testing"),
):
    """Scan a repository, triage findings with DeepSeek, and output an audit report."""
    console.print(Panel(f"[bold blue]🛡️ SecAgent Audit Initializing[/bold blue]\nTarget: [cyan]{repo_path}[/cyan]"))

    if mock_llm:
        os.environ["DEEPSEEK_API_KEY"] = "mock_key"

    graph = build_secagent_graph()
    initial_state = {
        "repo_path": repo_path,
        "max_retries": 1,
    }

    with console.status("[bold green]Executing security workflow (SAST ➔ DeepSeek Triage)..."):
        final_state = graph.invoke(initial_state)

    triaged = final_state.get("triaged_vulnerabilities", [])
    fps = final_state.get("false_positives", [])

    # Display Results Table
    table = Table(title="🛡️ Confirmed Real Vulnerabilities", show_lines=True)
    table.add_column("ID", style="bold cyan")
    table.add_column("File", style="green")
    table.add_column("Line", style="yellow")
    table.add_column("CWE", style="magenta")
    table.add_column("Confidence", style="bold red")
    table.add_column("Summary", style="white")

    for v in triaged:
        table.add_row(
            v.get("candidate_id", "N/A"),
            v.get("filename", "N/A"),
            str(v.get("line_number", 0)),
            v.get("cwe_id", "N/A"),
            f"{v.get('confidence_score', 0):.0%}",
            v.get("issue_text", "N/A")[:50] + "...",
        )

    console.print(table)
    console.print(f"\n[bold green]✓[/bold green] Filtered [bold cyan]{len(fps)}[/bold cyan] false positive alerts.")

    # Save SARIF if requested
    sarif_path = sarif or get_settings().secagent_sarif_output
    if sarif_path and final_state.get("sarif_report"):
        save_sarif_file(final_state["sarif_report"], sarif_path)
        console.print(f"[bold green]✓[/bold green] Saved SARIF report to [cyan]{sarif_path}[/cyan]")


@app.command(name="fix")
def fix(
    repo_path: str = typer.Argument(".", help="Path to target repository"),
    create_pr: bool = typer.Option(False, "--create-pr", help="Automatically push and open a GitHub PR"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch name for the fix"),
    sarif: Optional[str] = typer.Option(None, "--sarif", "-s", help="Path to output SARIF report"),
    mock_llm: bool = typer.Option(False, "--mock-llm", help="Run with deterministic mock LLM for testing"),
):
    """Run full autonomous loop: scan, triage, sandbox verify, synthesize patch, test, and PR."""
    console.print(Panel(f"[bold magenta]🚀 SecAgent Autonomous Fix Loop[/bold magenta]\nTarget: [cyan]{repo_path}[/cyan]"))

    if mock_llm:
        os.environ["DEEPSEEK_API_KEY"] = "mock_key"

    target_branch = branch or "secagent/security-patch"
    if create_pr:
        console.print(f"[dim]Checking out fix branch: {target_branch}...[/dim]")
        create_and_checkout_branch(repo_path, target_branch)

    graph = build_secagent_graph()
    initial_state = {
        "repo_path": repo_path,
        "pr_branch": target_branch if create_pr else None,
        "max_retries": 2,
    }

    with console.status("[bold green]Executing full remediation pipeline..."):
        final_state = graph.invoke(initial_state)

    if final_state.get("patch_applied"):
        console.print("[bold green]✓ Patch successfully applied to codebase![/bold green]")
        if final_state.get("regression_test_passed"):
            console.print("[bold green]✓ Regression test suite PASSED.[/bold green]")
            if create_pr:
                commit_changes(repo_path, "fix(secagent): remediate verified security vulnerability")
                if final_state.get("pr_url"):
                    console.print(f"[bold green]🎉 Pull Request Opened:[/bold green] [link={final_state['pr_url']}]{final_state['pr_url']}[/link]")
        else:
            console.print("[bold yellow]⚠️ Patch applied but regression tests failed. Manual review advised.[/bold yellow]")
    else:
        console.print("[bold yellow]ℹ No patch was applied (either no exploitable issues or verification did not confirm).[/bold yellow]")

    # Print summary
    if final_state.get("markdown_report"):
        console.print("\n" + final_state["markdown_report"])


def main():
    app()


if __name__ == "__main__":
    main()

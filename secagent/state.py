"""State schemas and data models for SecAgent LangGraph workflow."""

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class VulnerabilityCandidate(BaseModel):
    """Raw candidate issue produced by SAST scanner (e.g. Bandit, Semgrep)."""

    id: str = Field(description="Unique candidate identifier")
    tool: str = Field(default="bandit", description="Scanner that discovered this issue")
    test_id: str = Field(description="Scanner test ID (e.g., B602, B105)")
    cwe: Optional[str] = Field(default=None, description="CWE number (e.g., CWE-78, CWE-89)")
    severity: str = Field(default="MEDIUM", description="Severity level: LOW, MEDIUM, HIGH")
    confidence: str = Field(default="MEDIUM", description="Confidence level: LOW, MEDIUM, HIGH")
    filename: str = Field(description="Relative path to affected file")
    line_number: int = Field(description="Line number where finding was flagged")
    line_range: List[int] = Field(default_factory=list)
    code: str = Field(description="Source code snippet surrounding the finding")
    issue_text: str = Field(description="Description of the security finding")


class TriagedFinding(BaseModel):
    """DeepSeek analysis result for a candidate issue."""

    candidate_id: str
    is_real_vulnerability: bool = Field(
        description="True if the finding represents a real, reachable security issue, False if false positive"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0"
    )
    reasoning: str = Field(description="Detailed threat analysis and justification")
    cwe_id: str = Field(default="CWE-Unknown")
    attack_vector: Optional[str] = Field(default=None, description="Reachable entry point and data flow")
    reproduction_strategy: Optional[str] = Field(
        default=None, description="Suggested test input or setup to reproduce the issue defensively"
    )


class VerifiedVulnerability(BaseModel):
    """Vulnerability confirmed via isolated dynamic sandbox execution."""

    triage_info: TriagedFinding
    reproduction_code: str
    sandbox_output: str
    verified_at: str


class PatchSolution(BaseModel):
    """Synthesized code patch and rationale from DeepSeek-R1."""

    diff: str = Field(description="Unified diff format patch")
    explanation: str = Field(description="Technical explanation of the fix")
    affected_files: List[str] = Field(default_factory=list)
    side_effect_assessment: str = Field(
        description="Evaluation of potential breaking changes or regressions"
    )


class AgentState(TypedDict, total=False):
    """Global execution state carried across LangGraph nodes."""

    # Target Repository Context
    repo_path: str
    relative_target_dir: Optional[str]

    # SAST & Discovery Phase
    sast_candidates: List[Dict[str, Any]]

    # Triage & DeepSeek Threat Modeling Phase
    triaged_vulnerabilities: List[Dict[str, Any]]
    false_positives: List[Dict[str, Any]]
    current_target_vulnerability: Optional[Dict[str, Any]]

    # Verification & Sandbox Phase
    reproduction_test_code: Optional[str]
    reproduction_test_path: Optional[str]
    is_verified: bool
    verification_output: str

    # Remediation Phase
    patch_diff: Optional[str]
    patch_explanation: Optional[str]
    patch_applied: bool
    regression_test_passed: bool
    regression_test_output: str
    retry_count: int
    max_retries: int

    # Review & Delivery Phase
    pr_branch: Optional[str]
    pr_url: Optional[str]
    pr_body: Optional[str]
    sarif_report: Optional[Dict[str, Any]]
    markdown_report: Optional[str]

    # Error Tracking
    errors: List[str]

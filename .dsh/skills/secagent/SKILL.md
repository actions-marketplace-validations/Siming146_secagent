---
name: secagent
description: Autonomous security research and auto-patching agent for open-source repositories. Audits codebase, reduces false positives, executes dynamic sandbox verification, and generates minimal regression-tested fixes using DeepSeek-V3/R1.
---

# SecAgent Skill for DeepSeek Harness (dsh)

This skill equips DeepSeek Harness agents with professional Application Security (AppSec) research and automated vulnerability remediation capabilities.

## When to Use This Skill

Activate or run SecAgent when:
- The user asks to audit the security of the current project or a specified folder/repository.
- The user wants to find real, exploitable security vulnerabilities (SQLi, Command Injection, Path Traversal, SSRF, Deserialization, Hardcoded Secrets) without being overwhelmed by noisy SAST warnings.
- The user wants to dynamically verify whether an alleged vulnerability can be reproduced in a safe sandbox.
- The user wants an automated, regression-tested patch and Pull Request generated for a confirmed vulnerability.

## Core Commands

SecAgent provides convenient CLI commands that can be invoked via terminal or script within the harness:

### 1. Audit & Noise Reduction (SAST + DeepSeek Triage)
Scan the repository, filter out false positives with DeepSeek, and output a detailed Markdown/SARIF report:
```bash
secagent audit <repo_path> [--sarif <output.sarif>]
```

### 2. Full Autonomous Remediation Loop
Scan, triage, generate dynamic verification test, execute in isolated sandbox, synthesize minimal patch with DeepSeek-R1, and run regression tests:
```bash
secagent fix <repo_path> [--dry-run]
```

### 3. Automated Pull Request Creation
Execute the full loop and automatically commit to a fix branch and open a GitHub PR:
```bash
secagent fix <repo_path> --create-pr --branch secagent/patch-cwe-fixes
```

## Security Best Practices for the Agent

1. **Sandbox Safety**: All dynamic verifications are run in a controlled subprocess sandbox with strict timeout and environment sanitization. Never run unverified exploit payloads directly on host production environments.
2. **Minimal Patches**: The generated fix must address the root cause while preserving existing behavior and passing all existing project test suites.
3. **Traceability**: All reasoning traces, triage decisions, test outputs, and diffs are logged in the state for user review.

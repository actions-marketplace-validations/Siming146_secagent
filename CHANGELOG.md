# Changelog

All notable changes to **SecAgent** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2026-09-11

### Added
- **Dual-Pass Exploit Verification (F2P Red/Blue Protocol)**: Implemented strict Fail-to-Pass contract verification ensuring PoC tests must fail on unpatched code to prove vulnerability reachability (Red Phase), and must pass on patched code to confirm resolution (Blue Phase).
- **PoC Refinement Loop**: Introduced self-reflection and iterative correction in `verifier_node` (up to 2 refinement attempts) if tests unexpectedly pass on vulnerable code or encounter syntax/import errors.
- **Permanent Regression Test Persistence**: Validated PoC reproduction test suites (e.g., `tests/test_secagent_repro.py`) are now persisted to the codebase and automatically committed into the fix branch/PR to permanently prevent regressions.
- **Dual-Pass Evidence Cards**: Markdown and SARIF reports now provide side-by-side Red-Phase failure tracebacks and Blue-Phase resolution logs.
- **6-Metric Benchmark Suite**: Extended benchmark evaluation harness to explicitly measure Red-Phase triggering and Blue-Phase resolution alongside SAST, Triage, and Regression.

---

## [0.1.0] - 2026-09-06

### Added
- **LangGraph StateGraph Core**: Built deterministic state machine managing the complete AppSec loop: SAST line extraction ➔ DeepSeek triage ➔ sandbox verification ➔ DeepSeek-R1 minimal patch synthesis ➔ regression test validation ➔ SARIF/PR generation.
- **DeepSeek Integration**: Native support for DeepSeek-Chat (V3) and DeepSeek-Reasoner (R1) with chain-of-thought extraction and mock evaluation fallback.
- **DeepSeek Harness (`dsh`) Native Skill**: Provided turnkey `.dsh/skills/secagent/SKILL.md` for seamless plug-and-play capability in the DeepSeek agent runtime ecosystem.
- **Controlled Subprocess Sandbox**: Implemented lightweight process execution with strict timeouts, environment variable scrubbing (protecting API tokens), and output limits.
- **SAST Analyzers**: Integrated Bandit scanner with intelligent noise filtering and test-suite exclusion.
- **OASIS SARIF 2.1.0 Support**: Implemented GitHub Code Scanning compatible SARIF output (`results.sarif.json`).
- **Rich CLI Interface**: Developed Typer-based CLI providing `secagent audit`, `secagent fix`, and `secagent version`.
- **Benchmark Evaluation Harness**: Added realistic vulnerable repository target (`benchmark/sample_vulnerable_repo`) and test runner evaluating detection rate, false positive rejection, dynamic verification, and patch pass rate.
- **CI/CD Automation**: Added GitHub Actions workflows for continuous integration across Linux, Windows, and macOS, alongside PR security scanning action templates.
- **Open Source Governance**: Added Contributor Covenant Code of Conduct, Security policy, Contributing guide, and MIT license.

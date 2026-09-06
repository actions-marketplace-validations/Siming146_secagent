# SecAgent Project Roadmap

This roadmap outlines the planned development and milestones for **SecAgent** as part of our mission to deliver enterprise-grade autonomous security infrastructure for the modern open-source software ecosystem, powered by DeepSeek AI and native agent runtimes.

---

## 🎯 Phase 1: MVP & Foundation (Current - Q3 2026) :white_check_mark:

- [x] LangGraph StateGraph deterministic orchestration architecture.
- [x] Multi-engine support for DeepSeek-V4 (Flash & Pro Reasoning Engine).
- [x] DeepSeek Harness (`dsh`) native skill package (`.dsh/skills/secagent/`).
- [x] SAST candidate extraction via Bandit with false-positive filtering.
- [x] Controlled lightweight subprocess sandbox with environment scrubbing & timeouts.
- [x] Automated minimal patch synthesis with regression testing verification.
- [x] OASIS standard SARIF 2.1.0 output for GitHub Code Scanning integration.
- [x] Rich developer CLI (`secagent audit`, `secagent fix`).
- [x] Evaluation Benchmark Harness with 100% pass verification.

---

## 🚀 Phase 2: Ecosystem Integration & Multi-Language Support (Q4 2026)

- [ ] **Multi-Language Expansion**:
  - JavaScript / TypeScript support via ESLint Security & Semgrep rules.
  - Go support via `gosec`.
  - Rust support via `cargo-audit` and `clippy`.
- [ ] **GitHub App & PR Bot**:
  - Deployable GitHub App for zero-config PR security reviews with inline code suggestions.
  - Interactive bot comments explaining vulnerability attack vectors directly in GitHub PRs.
- [ ] **Advanced Sandbox Isolation**:
  - Pluggable container execution runtime (Docker SDK / Podman) for projects requiring complex service dependencies (e.g. Postgres, Redis).
  - Cloud sandbox adapters (E2B / Modal Code Interpreter).
- [ ] **Semgrep Rule Engine**:
  - Built-in Semgrep community rules integration for high-accuracy taint analysis.

---

## 🌐 Phase 3: Community Benchmark & Continuous Security Infrastructure (2027)

- [ ] **Open Benchmark Dataset**:
  - Curate a public AppSec benchmark dataset containing 100+ real-world verified CVE/CWE scenarios from popular open-source projects.
- [ ] **Community False-Positive Learning Hub**:
  - Enable opt-in telemetry for maintainer-confirmed false positives to fine-tune and continuously prompt-optimize vulnerability triage.
- [ ] **Supply Chain & Dependency Security**:
  - Integrate automated dependency vulnerability analysis (OSV / Dependabot alerts triage).
  - Autonomous dependency upgrade patch verification with regression testing.

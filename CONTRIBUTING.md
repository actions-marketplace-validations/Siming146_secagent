# Contributing to SecAgent

Thank you for your interest in contributing to **SecAgent**!

SecAgent is an open-source security research and remediation agent designed for the open-source software ecosystem. We welcome all contributions, including bug reports, new vulnerability analyzers, agent prompt improvements, and benchmark test cases.

---

## Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors. Please treat others with respect and professionalism.

---

## How Can I Contribute?

### 1. Reporting Bugs
- Search the [Issues](https://github.com/Siming146/secagent/issues) tracker to see if the issue has already been reported.
- If not, create a new issue using our **Bug Report** template. Provide clear steps to reproduce and system details.

### 2. Suggesting Enhancements
- Open a **Feature Request** issue describing the motivation, expected behavior, and potential implementation approach.

### 3. Submitting Pull Requests
1. Fork the repository and create a new branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Set up your local development environment:
   ```bash
   pip install -e ".[dev]"
   ```
3. Write unit tests in `tests/` for your changes.
4. Run code formatting and tests:
   ```bash
   ruff check secagent/ tests/
   pytest tests/
   ```
5. Commit your changes with clear, descriptive commit messages.
6. Push to your fork and submit a Pull Request to `main`.

---

## Architecture Principles

- **Deterministic Flow**: State transitions in LangGraph must be clean, typed via `AgentState`, and error-tolerant.
- **Defensive & Safe Sandbox**: Sandbox execution must enforce timeouts and environment isolation to prevent accidental damage during dynamic verification.
- **Zero Hallucination**: Triage and Verification must require concrete code evidence before generating fixes.

---

## Responsible Disclosure

If you discover a security vulnerability in SecAgent itself, please **DO NOT** open a public issue. Instead, report it privately via GitHub Security Advisories or by contacting the maintainers directly.

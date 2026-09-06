# Security Policy

## Supported Versions

We release patches and security fixes for the following versions of SecAgent:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

---

## Reporting a Vulnerability

The SecAgent maintainers take security issues very seriously. If you discover a vulnerability in SecAgent, please report it via private disclosure rather than creating a public issue.

### How to Report

1. **GitHub Security Advisories (Recommended)**:
   Navigate to the **Security** tab of this repository and click **"Report a vulnerability"** to submit an advisory draft privately.

2. **Email Disclosure**:
   If private advisories are unavailable, email your report to:
   **[2539027131@stu.xjtu.edu.cn](mailto:2539027131@stu.xjtu.edu.cn)**

### What to Include in Your Report

To help us triage and patch the issue quickly, please include:
- A description of the vulnerability and its potential impact.
- Step-by-step instructions to reproduce the issue (including any sample repositories, configuration files, or commands).
- Proof-of-concept (PoC) code or non-destructive reproduction steps.
- Your assessment of affected components and suggested remediation (if known).

### Our Commitment

- We will acknowledge receipt of your vulnerability report within **48 hours**.
- We will provide an estimated timeline for validation and patch development.
- We will coordinate public disclosure with you, crediting your contribution once the fix is verified and released.

---

## Sandbox & Execution Safety Policy

SecAgent executes test suites and dynamic reproduction scripts inside a local, controlled subprocess sandbox:
- Sensitive environment variables (such as `DEEPSEEK_API_KEY`, `GITHUB_TOKEN`, and cloud credentials) are automatically scrubbed from the sandbox process environment.
- Strict CPU and execution timeouts are enforced to prevent hang or resource denial-of-service.
- Dynamic verification tests must be defensive, self-contained unit tests. SecAgent will never intentionally perform destructive operations or communicate with unauthorized external networks.

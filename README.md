<div align="center">

# 🛡️ SecAgent (DeepSeek Security Agent)

**面向开源生态的 AI 应用安全研究与自动修复智能体**  
*An Autonomous AI Security Agent for Open Source Ecosystems — Powered by DeepSeek & LangGraph*

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![DeepSeek](https://img.shields.io/badge/Powered%20by-DeepSeek--V3%20%7C%20R1-4D6BFE.svg)](https://deepseek.com)
[![DeepSeek Harness](https://img.shields.io/badge/DeepSeek%20Harness-Native%20Skill-brightgreen.svg)](https://github.com/deepseek-ai/deepseek-harness)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## 📖 简介 (Overview)

**SecAgent** 是一款专门为开源软件仓库设计的自主 AI 安全研究与代码自动修复智能体。传统 SAST 工具（如 Bandit、Semgrep、CodeQL 等）往往会产生大量误报，且止步于发出告警，无法验证漏洞真实可达性，更需要维护者耗费大量精力人工排查、手写 Patch 和补充回归测试。

SecAgent 改变了这一现状：
1. **协同专业 SAST**：以 Bandit/Semgrep 告警作为线索切入，大幅节省全仓 Token 消耗；
2. **DeepSeek 深度甄别**：结合项目全局架构与调用链，由 **DeepSeek-Chat** / **DeepSeek-Reasoner (R1)** 过滤假阳性（False Positives），锁定可达攻击路径；
3. **轻量沙箱动态验证**：在受控轻量级进程沙箱中自动构造 Pytest 复现用例，动态验证漏洞是否真实存在；
4. **根因分析与最小 Patch**：利用 DeepSeek-R1 强大的逻辑推理能力合成规范最小补丁，并执行完整回归测试确保业务功能不受损；
5. **双模交付**：支持作为独立 **CLI / GitHub Action** 自动提交修复 PR，同时作为 **DeepSeek Harness (`dsh`)** 原生技能即插即用。

---

## 🏛️ 工作流与架构 (Architecture)

```text
       Target GitHub Repository
                  │
                  ▼
       ┌─────────────────────┐
       │   SAST Analyzer     │ ◄─── Bandit / Semgrep 候选线索收集
       └──────────┬──────────┘
                  ▼
       ┌─────────────────────┐
       │   Triage Agent      │ ◄─── DeepSeek 分析上下文可达性，剔除误报
       └──────────┬──────────┘
                  ▼
       ┌─────────────────────┐
       │   Verifier Agent    │ ◄─── 自动生成可运行的动态复现测试用例
       └──────────┬──────────┘
                  ▼
       ┌─────────────────────┐
       │   Isolated Sandbox  │ ◄─── 轻量进程/受控 venv 动态执行验证
       └──────────┬──────────┘
                  ▼
       ┌─────────────────────┐
       │    Fixer Agent      │ ◄─── DeepSeek-R1 合成最小化安全 Patch
       └──────────┬──────────┘
                  ▼
       ┌─────────────────────┐
       │   Regression Test   │ ◄─── 验证 Patch 修复漏洞且原有用例全部通过
       └──────────┬──────────┘
                  ▼
       ┌─────────────────────┐
       │  Reviewer / PR Gen  │ ◄─── 生成详细安全分析报告 (SARIF / PR)
       └─────────────────────┘
```

---

## ✨ 核心特性 (Key Features)

* **精确去误报 (Noise Reduction)**：深度理解函数边界、中间校验器与输入过滤逻辑，精准排除无法利用的虚假告警。
* **可证伪验证 (Provable Validation)**：不信口雌黄（No Hallucination），对每个高置信度漏洞自动生成复现测试并运行校验。
* **零破坏性 Patch (Safe Remediation)**：在合入前必须通过仓库原有的测试套件，杜绝补丁引发次生缺陷。
* **双模生态支持**：
  * **Standalone**：命令行 `secagent audit` / `secagent fix` 或 GitHub Actions CI 自动流水线。
  * **DeepSeek Harness (dsh)**：内置 `.dsh/skills/secagent/`，支持在 `dsh` 智能体平台内一键挂载。
* **标准 SARIF 2.1.0**：无缝对接 GitHub Advanced Security (Code Scanning) 面板。

---

## 🚀 快速上手 (Quick Start)

### 1. 安装

```bash
git clone https://github.com/your-org/secagent.git
cd secagent
pip install -e .
```

### 2. 配置环境变量

复制 `.env.example` 并填入您的 DeepSeek API Key（如需自动提 PR，可配置 GitHub Token）：

```bash
cp .env.example .env
```

```ini
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

### 3. 使用命令行 (CLI)

#### 运行安全审计与去误报分析（输出终端表格与 SARIF 报告）
```bash
secagent audit /path/to/your/repo
```

#### 完整自动闭环：审计 ➔ 动态验证 ➔ 自动修补 ➔ 回归测试
```bash
secagent fix /path/to/your/repo
```

#### 自动修复并在 GitHub 创建 Pull Request
```bash
secagent fix /path/to/your/repo --create-pr --branch secagent/fix-vulnerabilities
```

---

## 🤖 DeepSeek Harness (`dsh`) 技能挂载

如果您正在使用 DeepSeek 官方智能体运行环境 **DeepSeek Harness (`dsh`)**：

1. 本项目自带符合规范的 DSH Skill 定义文件 `.dsh/skills/secagent/SKILL.md`。
2. 将本目录软链接或复制到全局技能目录：
   ```bash
   cp -r .dsh/skills/secagent ~/.agents/skills/
   ```
3. 在 `dsh` 终端或 Web 工作台中即可直接让智能体调用：
   > *"请使用 secagent 审计当前项目的安全问题，并在沙箱中生成复现用例与修复补丁。"*

---

## 🔄 GitHub Actions CI/CD 集成范例

在您的仓库创建 `.github/workflows/security.yml`：

```yaml
name: Autonomous Security Agent

on:
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1' # 每周一定时全仓巡检

jobs:
  secagent-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install SecAgent
        run: |
          pip install git+https://github.com/your-org/secagent.git

      - name: Run SecAgent Audit
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          secagent audit . --sarif results.sarif

      - name: Upload SARIF report
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: results.sarif
```

---

## 📊 评测基准 (Benchmark Harness)

本项目内置针对典型 Python 安全漏洞（SQL 注入、命令注入、路径穿越、任意反序列化）的微型基准靶场：

```bash
# 使用内置模拟器运行 Benchmark
python benchmark/run_benchmark.py --mock-llm

# 或使用真实 DeepSeek API 运行
python benchmark/run_benchmark.py
```

---

## 🤝 贡献与负责任披露

- **贡献指南**：请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。
- **安全漏洞披露**：如在 SecAgent 本身发现安全缺陷，请通过 GitHub Security Advisory 或私信邮箱联系维护团队，遵循负责任的协同披露原则。

---

## 📄 开源许可证

本项目基于 [Apache License 2.0](LICENSE) 协议开源。

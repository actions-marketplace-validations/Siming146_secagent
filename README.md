<div align="center">

# 🛡️ SecAgent (DeepSeek Security Agent)

**面向开源生态的 AI 应用安全研究与自动修复智能体**  
*An Autonomous AI Security Agent for Open Source Ecosystems — Powered by DeepSeek & LangGraph*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![DeepSeek](https://img.shields.io/badge/Powered%20by-DeepSeek--V3%20%7C%20R1-4D6BFE.svg)](https://deepseek.com)
[![DeepSeek Harness](https://img.shields.io/badge/DeepSeek%20Harness-Native%20Skill-brightgreen.svg)](https://github.com/deepseek-ai/deepseek-harness)
[![SARIF 2.1.0](https://img.shields.io/badge/SARIF-2.1.0-orange.svg)](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)
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
git clone https://github.com/Siming146/secagent.git
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
          pip install git+https://github.com/Siming146/secagent.git

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

## 🌟 为什么选择 SecAgent？赋能开源维护者的闭环安全体系

开源项目的核心维护者常常陷入“告警疲劳（Alert Fatigue）”：安全工具报告了海量潜在告警，但其中大量是死代码或已过滤的假阳性；真正的高危漏洞缺少复现 PoC，手写修复补丁耗时耗力，还容易引发次生 Bug。

SecAgent 将传统的“告警生成器”升级为“**端到端自主安全研究员**”：

| 维护者核心痛点 | 传统工具缺陷 (如传统静态扫描) | SecAgent 自主闭环解决方案 |
|---|---|---|
| **海量噪音与告警疲劳** | 规则匹配产生海量误报，维护者精力被淹没 | 利用 DeepSeek 大模型结合项目架构与调用链，精准剔除死路径与不可达误报 |
| **可达性难以证明** | 仅给出代码行告警，无法证明是否真实可被利用 | 在受控隔离沙箱中自动合成针对性 Pytest 复现用例，以可运行代码证明漏洞 |
| **人工写 Patch 成本高** | 漏洞修复全靠人工深入排查根因并逐行手写补丁 | 基于 DeepSeek-R1 深度推理思维链，全自动合成遵循代码规范的最小补丁 |
| **破坏既有业务风险** | 修复补丁容易破坏既有功能或引入次生缺陷 | 在沙箱中自动运行全仓原有测试套件进行严格回归验证，确保通过率 100% |
| **工程化协同成本** | 扫描结果脱离现有工作流，沟通交割繁琐 | 原生输出标准 OASIS SARIF 2.1.0，并可全自动提交包含复现依据的 Pull Request |

> [!NOTE]
> 本项目专注于“**静态线索 ➔ 语义去噪 ➔ 沙箱动态验证 ➔ 最小补丁合成 ➔ 回归测试 ➔ 自动 PR**”六位一体的确定性闭环，旨在为开源生态提供开箱即用（Batteries-Included）、零误扰的工业级自动化安全防护。

---

## 🗺️ 项目路线图 (Roadmap)

请参阅完整的技术路线图与长期愿景规划：[ROADMAP.md](ROADMAP.md)。

---

## 📜 社区治理与合规规范 (Community & Governance)

- **贡献指南**：[CONTRIBUTING.md](CONTRIBUTING.md)
- **行为准则**：[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **安全负责任披露**：[SECURITY.md](SECURITY.md)
- **版本更新日志**：[CHANGELOG.md](CHANGELOG.md)

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 协议开源。


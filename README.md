# KratosQA-Architect

> **AI-Augmented Test Automation Framework — Architecture Showcase**
> Java 17 · Playwright · TestNG · Allure · Claude API · GitHub Actions

[![Java](https://img.shields.io/badge/Java-17-blue)](https://openjdk.org/projects/jdk/17/)
[![Playwright](https://img.shields.io/badge/Playwright-1.50-green)](https://playwright.dev/)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204-purple)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**KratosQA-Architect** is a senior-level, production-grade test automation framework architecture targeting a SaaS web application. It goes beyond conventional frameworks by embedding a full AI agent system that learns from every CI run, self-heals broken locators, validates requirements before test generation, and autonomously fills coverage gaps.

> ⚠️ **Portfolio Note:** This is a public architecture showcase. The actual test suite targets a proprietary SaaS application and remains in a private repository. All framework infrastructure, AI agents, CI workflows, and architectural patterns are presented here as a portfolio reference.

---

## Live Architecture

| | |
|---|---|
| 🔄 CI Workflows | 13 fully automated GitHub Actions workflows |
| 🧠 AI Agents | 7 Claude-powered agents with persistent learning |
| 🔬 Test Intelligence | Self-learning brain that improves every CI run |
| 🔧 Self-Healing | Broken locators auto-fixed via PR |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Java 17 |
| Browser Automation | Microsoft Playwright 1.50 |
| Test Framework | TestNG 7.10 |
| Reporting | Allure 2.27 + GitHub Pages |
| AI Layer | Anthropic Claude API (Sonnet 4) |
| CI/CD | GitHub Actions (multi-browser matrix) |
| Build | Maven 3 |
| Notifications | Slack + Jira (via n8n) |

---

## Architecture Overview

```
KratosQA-Architect
├── Core Framework (Java 17 + Playwright + TestNG)
│   ├── Page Object Model with self-healing locators
│   ├── BaseTest + ThreadLocal browser management
│   ├── IRetryAnalyzer with global injection via IAnnotationTransformer
│   ├── Environment-aware test data (local/ci/staging JSON files)
│   └── Allure reporting with full environment properties
│
├── AI Agent System (Claude API)
│   ├── TestGeneratorAgent          — generates TC-NNN tests from page objects
│   ├── SentinelGuardAgent          — audits test code quality (C1-C5 criteria)
│   ├── BugAnalyzerAgent            — L1-L5 root cause classification on failures
│   ├── FlakyDetectorAgent          — detects + auto-quarantines flaky tests
│   ├── RequirementValidatorAgent   — validates requirements before strategy gen
│   ├── RequirementToStrategyAgent  — req → full test strategy document
│   └── AutoFixerAgent              — L1 locator fix → PR (no auto-merge)
│
├── Test Intelligence Brain (persistent learning layer)
│   ├── failure_root_causes.json    — L1-L5 per test over time, browser-specific
│   ├── flaky_patterns.json         — pass/fail history + severity per test
│   ├── risky_modules.json          — page objects ranked by failure rate
│   └── stable_locators.json        — locator stability tracking per page
│
└── CI/CD Pipeline (GitHub Actions — 13 workflows)
    ├── 3-job regression: select → prioritize → run
    ├── Auto-triggered AI analysis on every failure
    └── n8n integration for Jira + Slack
```

---

## CI/CD Pipeline — 3-Job Regression

The regression pipeline runs in 3 sequential jobs on every push to `main`:

```
Job 1: Intelligent Test Selection    (~30s)
       Rule-based git diff → maps changed files to impacted test classes
       Only runs tests relevant to what changed

Job 2: LLM Test Prioritization       (~15s)
       Claude API + Test Intelligence Brain → risk-scores selected tests
       Highest-risk tests always run first

Job 3: Full Regression               (Chromium + Firefox parallel)
       Runs tests in prioritized order
       Publishes Allure report to GitHub Pages
```

### All 13 Workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| Full Regression Suite | push / nightly / dispatch | 3-job: select → prioritize → run |
| Smoke Tests | push to main | Fast sanity check |
| API Tests | push to main | REST API validation |
| AI Failure Analysis | post-regression | L1-L5 RCA, Slack, Jira |
| AutoFixerAgent | post-AI analysis | L1 locator fix → PR |
| FlakyDetectorAgent | weekly + post-regression | Flaky detection + auto-quarantine |
| Test Intelligence Brain | post-regression | Updates persistent knowledge store |
| Active Coverage Gap Filler | post-regression + weekly | Scans all pages, fills gaps via PR |
| AI Requirement → Test Strategy | manual dispatch | Validates req + generates strategy |
| Coverage Gap Analyzer | weekly + manual | Gap reporting |
| Business Metrics Dashboard | post-regression | Executive metrics |
| Contract Tests | push to main | Pact consumer contract tests |
| Database Tests | push to main | JDBC integration tests |

---

## AI Agent System

### Test Intelligence Brain

The central learning layer — a persistent knowledge store on `gh-pages/brain/` that updates after every CI run.

```
Every CI run →
  brain_updater.py writes to gh-pages/brain/:
    ├── failure_root_causes.json   (L1-L5 per test, browser-specific)
    ├── flaky_patterns.json        (pass rate, severity, recent pattern)
    ├── risky_modules.json         (page risk scores + guidance)
    └── stable_locators.json       (locator stability per page)

Other agents read via brain_reader.py:
  ├── llm_prioritizer.py  → historical risk boosts Claude's score
  ├── req_to_strategy.py  → strategy warns about historically risky pages
  └── auto_fixer.py       → locator hints from stable history
```

### BugAnalyzerAgent — L1-L5 Classification

| Class | Type | Automated Action |
|---|---|---|
| L1 | Locator failure | AutoFixerAgent generates fix PR |
| L2 | Network/environment | Flagged as infra issue |
| L3 | Assertion mismatch | Jira bug created via n8n |
| L4 | Framework/browser crash | Critical Slack alert |
| L5 | Unknown/flaky | FlakyDetectorAgent monitors |

### RequirementValidatorAgent

Validates requirements **before** strategy generation:

```
Input:  "User can enter weight"
Output: 🔴 BLOCK (score 3/10)
        Missing: min/max, units, decimal rules, error states

Input:  "User enters weight in kg between 30-300,
         decimals allowed, error shown if out of range"
Output: ✅ PASS (score 9/10) → proceed to strategy generation
```

### AutoFixerAgent — Safe Mode

- Only modifies `LOC_*` constants in Page Object files
- Never touches assertions, BaseTest, or business logic
- LOW confidence fixes are skipped automatically
- Opens PR for human review — **no auto-merge ever**

---

## Repository Structure

```
KratosQA-Architect/
├── .github/
│   ├── workflows/          13 GitHub Actions workflow files
│   └── scripts/            AI agent Python scripts
│       ├── brain_updater.py        Test Intelligence Brain updater
│       ├── brain_reader.py         Brain reader utility (imported by agents)
│       ├── llm_prioritizer.py      LLM risk-based test prioritization
│       ├── select_tests.py         Intelligent test selection (git diff)
│       ├── ai_failure_analysis.py  L1-L5 failure classification
│       ├── auto_fixer.py           Autonomous locator fix generator
│       ├── flaky_detector.py       Flakiness detection + auto-quarantine
│       ├── coverage_gap_analyzer.py Active coverage gap filling
│       ├── req_to_strategy.py      Requirement → test strategy generator
│       ├── req_validator.py        Requirement pre-validation agent
│       └── metrics_dashboard.py    Business metrics dashboard
├── .claude/
│   ├── agents.md           Agent architecture + invocation guide
│   └── skills/             Claude Code skill definitions
│       ├── test-generator-agent/SKILL.md
│       ├── sentinel-playwright-java/SKILL.md
│       ├── bug-analyzer-agent/SKILL.md
│       ├── flaky-detector-agent/SKILL.md
│       └── req-to-strategy-agent/SKILL.md
└── docs/
    └── ARCHITECTURE.md     Deep-dive architecture documentation
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| `parallel="none"` in TestNG | Target app rate-limits parallel requests |
| `@BeforeClass` for browser, `@BeforeMethod` for context | Thread isolation + performance balance |
| `IRetryAnalyzer` via `IAnnotationTransformer` | No per-test annotation needed |
| Brain stored on gh-pages branch | Already writable, no new infrastructure |
| AutoFixerAgent — PR only, no auto-merge | Human review required, prevents weakening tests |
| WARN vs BLOCK in RequirementValidator | Allows proceeding with stated assumptions |
| Brain boost on top of Claude scoring | Historical data + semantic analysis combined |

---

## GitHub Secrets Required

| Secret | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API — all AI agents |
| `GH_PAT` | GitHub PAT — branch creation, PR opening, gh-pages write |
| `SLACK_WEBHOOK_URL` | Slack notifications |
| `N8N_WEBHOOK_URL` | n8n → Jira auto-bug creation |

---

## What Separates This From Standard Frameworks

Most enterprise QA frameworks have: page objects + CI + reporting.

This architecture additionally has:

- **Self-learning** — the Test Intelligence Brain gets smarter after every run
- **Self-healing** — broken locators are automatically fixed via PR
- **Self-prioritizing** — highest-risk tests always run first using Claude + history
- **Self-filling** — coverage gaps detected and filled automatically post-regression
- **Shift-left validation** — requirements validated before any test is written
- **Autonomous operations** — failures trigger triage → fix → PR without human intervention

---

## Getting Started (Adapting to Your Project)

```bash
# Clone this repo
git clone https://github.com/SpartanzWarrior47/KratosQA-Architect.git

# Add required secrets to your GitHub repo:
# ANTHROPIC_API_KEY, GH_PAT, SLACK_WEBHOOK_URL, N8N_WEBHOOK_URL

# Install Claude Code CLI for local agent usage
npm install -g @anthropic-ai/claude-code

# Launch agents locally
cd your-project
claude

# Available slash commands
/generate-strategy <requirement>
/generate-tests <PageName> starting from TC-001
/analyze-failure <stack trace>
/detect-flaky
/sentinel-audit <file path>
```

---

## Author

**Naveen** — Senior QA Lead
[GitHub Profile](https://github.com/SpartanzWarrior47)

---

*Built with Java 17 · Playwright · TestNG · Allure · Claude API · GitHub Actions*

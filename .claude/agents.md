# KratosQA-Architect — Claude Code Agents

All agents run via Claude Code CLI and use skills in `.claude/skills/`.

## Agent roster

| Agent | Skill | Trigger | Responsibility |
|---|---|---|---|
| TestGeneratorAgent | skills/test-generator-agent/SKILL.md | `/generate-tests` | Generate TC-NNN test cases |
| SentinelGuardAgent | skills/sentinel-playwright-java/SKILL.md | auto on .java edit | Audit test code quality |
| BugAnalyzerAgent | skills/bug-analyzer-agent/SKILL.md | `/analyze-failure` | L1-L5 RCA |
| FlakyDetectorAgent | skills/flaky-detector-agent/SKILL.md | `/detect-flaky` | Flaky detection |
| RequirementToStrategyAgent | skills/req-to-strategy-agent/SKILL.md | `/generate-strategy` | Req → test strategy |

## Full pipeline

```
PM writes requirement
    ↓
RequirementValidatorAgent  (BLOCK / WARN / PASS)
    ↓
RequirementToStrategyAgent  (risk, scope, TC-NNN cases, page objects)
    ↓
TestGeneratorAgent  (Java test code)
    ↓
SentinelGuardAgent  (quality audit — C1-C5)
    ↓
[CI — 3-job pipeline]
select-tests → prioritize-tests → regression
    ↓
FlakyDetectorAgent  (weekly + post-regression → auto-quarantine PR)
    ↓
[On failure]
BugAnalyzerAgent → L1-L5
  L1 → AutoFixerAgent → locator fix PR
  L3 → n8n → Jira bug + Slack
```

## Slash commands

```bash
/generate-strategy User can add item to cart and proceed to checkout
/generate-tests LoginPage starting from TC-001
/sentinel-audit src/test/java/com/qa/tests/LoginTests.java
/analyze-failure <paste stack trace>
/detect-flaky
```

## Flaky severity thresholds

| Pass Rate | Severity | Action |
|---|---|---|
| < 50% | 🔴 CRITICAL | Auto-quarantine PR |
| 50–70% | 🟠 HIGH | Auto-quarantine PR |
| 70–80% | 🟡 MEDIUM | Slack digest |
| 80–90% | 🟢 LOW | Monitor |

## CI workflows map

| Workflow | File | Trigger |
|---|---|---|
| Full Regression Suite (3 jobs) | regression.yml | push / nightly |
| AI Failure Analysis | ai-failure-analysis.yml | post-regression |
| AutoFixerAgent | auto-fixer.yml | post-AI analysis |
| FlakyDetectorAgent | flaky-detector.yml | weekly + post-regression |
| Test Intelligence Brain | brain-updater.yml | post-regression |
| Coverage Gap Analyzer | coverage-gap-analyzer.yml | post-regression + weekly |
| AI Requirement → Strategy | req-to-strategy.yml | manual |

## Environment variables required

```bash
export ANTHROPIC_API_KEY=your_key_here
export GH_PAT=your_github_pat
export SLACK_WEBHOOK_URL=your_slack_webhook
export N8N_WEBHOOK_URL=your_n8n_webhook
```

## Claude Code setup

```bash
npm install -g @anthropic-ai/claude-code
cd your-project
claude
```

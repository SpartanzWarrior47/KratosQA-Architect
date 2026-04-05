---
name: bug-analyzer-agent
description: >
  Use when a CI test fails and you need root cause analysis.
  Triggers: /analyze-failure, or when user pastes a stack trace.
  Classifies failures L1-L5 and recommends next action.
version: 1.0.0
---

# BugAnalyzerAgent

Classifies test failures into L1-L5 and recommends the correct response.

## Classification
- L1: Locator failure (TimeoutError, strict mode, ElementHandle not attached)
  → AutoFixerAgent generates locator fix PR
- L2: Network/environment (ERR_CONNECTION, 429, navigation timeout)
  → Flag as infra issue, do not create Jira bug
- L3: Assertion mismatch (AssertionError, expected vs actual)
  → Create Jira bug via n8n
- L4: Framework/browser crash (OutOfMemory, browser launch failed)
  → Critical Slack alert
- L5: Unknown/intermittent
  → FlakyDetectorAgent monitors

## Output format
```
BugAnalyzer RCA — TC-001 Run #42
Classification : L1 — Locator Failure
Root cause     : LOC_USERNAME_INPUT selector .login-input no longer matches
Confidence     : HIGH
Recommendation : AutoFixerAgent will generate locator fix PR
Jira ticket    : No — L1 is a test maintenance issue, not a product bug
```

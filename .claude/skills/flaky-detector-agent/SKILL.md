---
name: flaky-detector-agent
description: >
  Use when you need to identify flaky tests from Allure history.
  Triggers: /detect-flaky, /flaky-report.
  Analyses pass/fail patterns and suggests quarantine or fix.
version: 1.0.0
---

# FlakyDetectorAgent

Analyses Allure history to detect and manage flaky tests.

## Flakiness definition
A test is flaky if:
- It has run at least 5 times
- Pass rate is below 90%
- It has at least one pass AND one fail (pure failures = regression, not flaky)

## Severity levels
| Pass Rate | Severity | Action |
|---|---|---|
| < 50% | CRITICAL | Auto-quarantine PR |
| 50–70% | HIGH | Auto-quarantine PR |
| 70–80% | MEDIUM | Slack digest only |
| 80–90% | LOW | Monitor |

## Quarantine process
1. FlakyDetectorAgent opens PR with `quarantine.xml` exclusion list
2. Human adds `@Test(groups = "quarantine")` to the test method
3. Human reviews and merges PR
4. Test stops running until root cause is fixed

## Commands
```bash
/detect-flaky                # default 90% threshold
/detect-flaky --threshold 80 # stricter
/fix-flaky tc001             # suggest fix for specific test
```

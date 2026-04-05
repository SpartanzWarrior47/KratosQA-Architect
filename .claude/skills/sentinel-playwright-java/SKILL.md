---
name: sentinel-playwright-java
description: >
  Auto-activates when .java test files are edited. Also triggers on:
  /sentinel-audit, /audit-tests. Reviews test code against 5 quality criteria.
version: 1.0.0
---

# SentinelGuardAgent

Audits test code quality against 5 criteria. Blocks commit if CRITICAL violations found.

## Criteria
- C1 CRITICAL: Hard-coded test data (use TestDataFactory)
- C2 CRITICAL: Thread.sleep() usage (use Playwright waitFor)
- C3 MAJOR: Missing Allure annotations (@Story, @Severity, @Description)
- C4 MAJOR: No assertion failure message (always add meaningful message)
- C5 MINOR: LOC_* constant not defined (locator inline in test)

## Decision
- CRITICAL violations → BLOCK (do not commit)
- MAJOR only → WARN (commit with caveats)
- MINOR only → PASS with notes

## Output format
```
SentinelGuard Audit — {ClassName}.java
❌ C1 [CRITICAL] Hard-coded string found: "standard_user"
   Fix: Use TestDataFactory.validUsername()
⚠️ C3 [MAJOR] Missing @Story on tc002_loginWithInvalidPassword
   Fix: Add @Story("Login — Invalid Credentials")

Decision: BLOCK — fix CRITICAL violations before committing
```

# Architecture Deep-Dive — KratosQA-Architect

## Framework Layers

### Layer 1 — Core Test Infrastructure

```
src/
├── main/java/com/qa/
│   ├── base/
│   │   ├── BaseTest.java      ThreadLocal browser + context management
│   │   └── BasePage.java      Common page interactions + waitForPageLoad
│   ├── pages/             Page Object Model classes (one per page)
│   ├── utils/
│   │   ├── ConfigReader.java  config.properties loader (system property override)
│   │   ├── TestDataReader.java env-aware JSON loader (local/ci/staging)
│   │   └── AllureEnvironmentWriter.java
│   └── listeners/
│       ├── RetryListener.java  IRetryAnalyzer via IAnnotationTransformer (global)
│       └── HealingListener.java Self-healing locator event listener
└── test/
    ├── java/com/qa/
    │   ├── tests/             Test classes (TC-NNN pattern)
    │   └── data/
    │       └── TestDataFactory.java Centralised test data factory
    └── resources/
        ├── config.properties
        ├── allure.properties
        └── testdata/
            ├── testdata-local.json
            ├── testdata-ci.json
            └── testdata-staging.json
```

### Layer 2 — Test Intelligence Brain

Persistent knowledge store on `gh-pages/brain/`. Updated after every CI run.

```
gh-pages/brain/
├── failure_root_causes.json
│   Structure: { "tc001_login": { "total_runs": 12, "classifications": {"L1": 3, "L3": 1}, ... } }
├── flaky_patterns.json
│   Structure: { "tc001_login": { "pass_rate": 66.7, "is_flaky": true, "severity": "HIGH", ... } }
├── risky_modules.json
│   Structure: { "LoginPage": { "risk_score": 7.4, "risk_level": "HIGH", "guidance": "..." } }
└── stable_locators.json
    Structure: { "LoginPage": { "stable_runs": 45, "unstable_runs": 2, "stability_pct": 95.7 } }
```

**How brain feeds other agents:**

```python
# In llm_prioritizer.py
brain   = BrainReader()
context = brain.get_context_for_llm()  # injected into Claude prompt
boosts  = brain.get_prioritization_boost(test_classes)  # added to Claude scores

# Result: historically unreliable tests run first,
# even if current diff doesn’t touch their code
```

### Layer 3 — Intelligent CI Pipeline

```
Job 1: select_tests.py
  Input:  git diff (BEFORE_SHA...GITHUB_SHA)
  Output: selected_tests="LoginTests,CartTests"

  Mapping rules:
    pages/LoginPage.java  → LoginTests
    base/BaseTest.java    → ALL (full run)
    .github/              → skip tests entirely
    pom.xml               → ALL (dependency change)

Job 2: llm_prioritizer.py
  Input:  selected_tests + git diff + brain context
  Claude: assigns risk score 1-10 per test class
  Brain:  adds boost score for historically unreliable tests
  Output: prioritized_tests="CartTests,LoginTests" (highest risk first)

Job 3: regression (Chromium + Firefox matrix)
  mvn test -Dtest="$prioritized_tests"
  Allure report → GitHub Pages
```

### Layer 4 — L1-L5 Failure Classification

```
L1 Locator failure
   Signals: TimeoutError, waiting for selector, strict mode violation
   Action:  AutoFixerAgent → locator fix → PR (human reviews)

L2 Environment/network failure
   Signals: ERR_CONNECTION, 429, navigation timeout
   Action:  Flag as infra issue, skip Jira

L3 Assertion failure
   Signals: AssertionError, expected vs actual mismatch
   Action:  n8n webhook → Jira bug + Slack notification

L4 Framework crash
   Signals: OutOfMemory, browser launch failed
   Action:  Critical Slack alert

L5 Unknown/flaky
   Signals: No clear pattern
   Action:  FlakyDetectorAgent monitors over time
```

### Layer 5 — Requirement Validation

```
Input: "User can enter weight"

Local pre-check (instant, no API):
  ⚠️  Input field but no constraints (min/max/format/type)
  ⚠️  No observable outcome defined

Claude deep analysis:
  Issues:
    🔴 MISSING_CONSTRAINT: No min/max weight specified
    🟠 MISSING_ERROR_STATE: No error message defined
    🟡 MISSING_EDGE_CASE: Decimal input not specified
  Score: 3/10 → BLOCK

  Questions for PM:
    1. What is the min and max weight accepted?
    2. Is decimal input allowed (e.g. 70.5)?
    3. What unit — kg or lbs?
    4. What error shows for invalid input?

Input: "User enters weight in kg between 30-300, decimals allowed,
        error message shown if out of range"
Score: 9/10 → PASS → proceed to strategy generation
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| `IRetryAnalyzer` via `IAnnotationTransformer` | Global retry without per-test annotation |
| `@BeforeClass` for browser, `@BeforeMethod` for context | Thread isolation + performance balance |
| `parallel="none"` in testng.xml | Target app rate-limits parallel requests |
| Brain on gh-pages branch | Already writable, zero new infrastructure |
| AutoFixerAgent PR-only, no auto-merge | Human review prevents weakened tests |
| WARN vs BLOCK in RequirementValidator | WARN allows proceeding with stated assumptions |
| Firefox timeout 90s vs Chromium 60s | Cold start compensation for target environment |
| Brain boost on top of Claude scoring | Historical data + semantic analysis combined |
| One PR per page per run in gap filler | Avoids overwhelming the PR queue |

## Secrets Architecture

```
GitHub Secrets:
  ANTHROPIC_API_KEY  → all Claude API calls
  GH_PAT             → gh-pages write, branch create, PR open
  SLACK_WEBHOOK_URL  → all Slack notifications
  N8N_WEBHOOK_URL    → n8n → Jira auto-bug creation

Passed to scripts as env vars — never in code.
```

## n8n Integration

```
CI failure (L3 classification)
    ↓
 ai_failure_analysis.py POSTs to N8N_WEBHOOK_URL
    {
      "jira_summary": "Regression Failure Run 99 chromium",
      "jira_description": "...",
      "run_url": "...",
      "allure_url": "..."
    }
    ↓
 n8n workflow:
  → Check if Jira ticket already exists (dedup)
  → Create Jira issue if new
  → Post to Slack #qa-alerts
```

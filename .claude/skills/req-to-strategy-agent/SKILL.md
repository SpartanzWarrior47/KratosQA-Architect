---
name: req-to-strategy-agent
description: >
  Use when asked to generate a test strategy from a product requirement.
  Triggers: /generate-strategy, /test-strategy, or when user describes
  a new feature and asks what to test.
version: 1.0.0
---

# RequirementToStrategyAgent

Turns a plain-English requirement into a complete test strategy.

## Pipeline
1. RequirementValidatorAgent validates first (BLOCK / WARN / PASS)
2. If PASS or WARN → generate full strategy

## Output structure
1. Risk assessment (HIGH / MEDIUM / LOW + rationale)
2. Test scope (in scope / out of scope)
3. Page objects needed (class name, file path, locators)
4. TestDataFactory additions
5. Test cases (TC-NNN format, grouped by category)
6. Implementation order (numbered steps)
7. Effort estimate (hours)

## Example
```
/generate-strategy User can add a product to cart from the inventory page

Output:
  Risk: HIGH (core purchase journey)
  TCs: TC-041 to TC-050 (10 cases)
  Page: CartPage.java (new)
  Effort: 5h
```

## Slash commands
```bash
/generate-strategy <requirement text>
/test-strategy --file requirements/cart-feature.md
```

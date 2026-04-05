---
name: test-generator-agent
description: >
  Use when asked to generate test cases for a page object or feature.
  Triggers: /generate-tests, /write-tests, or when user describes a page
  and asks for TC-NNN test methods.
version: 1.0.0
---

# TestGeneratorAgent

Generate complete, production-ready TestNG test classes for Java 17 + Playwright.

## Conventions
- Package: `com.qa.tests`
- Class: `{PageName}Tests`
- Extend `BaseTest`
- TC-IDs: TC-NNN (ask user for next TC number)
- Methods: `tc{NNN}_camelCaseDescription()`
- Allure: `@Epic`, `@Feature`, `@Story`, `@Severity`, `@Description` on every test
- Locators: `LOC_UPPER_SNAKE_CASE` constants in page object
- Data: `TestDataFactory.method()` for all test data

## Test categories to cover (in order)
1. UI presence (all elements visible on load)
2. Happy path (valid inputs, successful flow)
3. Boundary values (min/max edge cases)
4. Negative cases (invalid inputs, error messages)
5. Navigation (back button, breadcrumb, progress)

## Example output
```java
@Test(groups = {"smoke", "login"})
@Story("Login — Valid Credentials")
@Severity(SeverityLevel.BLOCKER)
@Description("TC-001: User can log in with valid credentials")
public void tc001_loginWithValidCredentials() {
    // ...
}
```

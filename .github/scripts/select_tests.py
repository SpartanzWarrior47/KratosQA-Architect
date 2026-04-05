#!/usr/bin/env python3
"""
Intelligent Test Selector — KratosQA-Architect
===============================================
Analyses the git diff between the current commit and the previous one,
maps changed files to impacted test classes, and outputs a filtered
-Dtest=... string for Maven Surefire.

Update MAPPINGS below to match your project's page objects and test classes.

Outputs:
  - selected_tests  → GITHUB_OUTPUT
  - run_all         → GITHUB_OUTPUT
  - ci_only_change  → GITHUB_OUTPUT
"""

import os
import json
import urllib.request
import urllib.error
import sys

REPO       = os.environ.get("GITHUB_REPOSITORY", "your-org/your-repo")
GH_PAT     = os.environ.get("GH_PAT", "")
GITHUB_SHA = os.environ.get("GITHUB_SHA", "")
GH_OUTPUT  = os.environ.get("GITHUB_OUTPUT", "")
BEFORE_SHA = os.environ.get("BEFORE_SHA", "")

# ── Update this to match your test classes ──
ALL_TESTS = "LoginTests,InventoryTests,CartTests,CheckoutTests"

# ── Update mappings to match your project structure ──
MAPPINGS = [
    # Base/utils changes → full run
    ("src/test/java/com/qa/base/",     None),
    ("src/test/java/com/qa/utils/",    None),
    ("src/test/java/com/qa/data/",     None),
    ("src/test/resources/",            None),
    ("pom.xml",                        None),
    ("testng.xml",                     None),

    # Page object changes → mapped test classes
    ("pages/LoginPage",     ["LoginTests"]),
    ("pages/InventoryPage", ["InventoryTests"]),
    ("pages/CartPage",      ["CartTests"]),
    ("pages/CheckoutPage",  ["CheckoutTests"]),

    # Test class changes → that class only
    ("tests/LoginTests",    ["LoginTests"]),
    ("tests/InventoryTests",["InventoryTests"]),
    ("tests/CartTests",     ["CartTests"]),
    ("tests/CheckoutTests", ["CheckoutTests"]),

    # CI/infra changes → skip tests
    (".github/",  []),
    (".claude/",  []),
    ("README",    []),
]


def gh_get(url):
    req = urllib.request.Request(url)
    if GH_PAT:
        req.add_header("Authorization", f"Bearer {GH_PAT}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[TestSelector] GitHub API error: {e}")
        return None


def get_changed_files():
    owner, repo = REPO.split("/")
    if BEFORE_SHA and GITHUB_SHA and BEFORE_SHA != GITHUB_SHA:
        url  = f"https://api.github.com/repos/{owner}/{repo}/compare/{BEFORE_SHA}...{GITHUB_SHA}"
        data = gh_get(url)
        if data and "files" in data:
            return [f["filename"] for f in data["files"]]
    if GITHUB_SHA:
        url  = f"https://api.github.com/repos/{owner}/{repo}/commits/{GITHUB_SHA}"
        data = gh_get(url)
        if data and "files" in data:
            return [f["filename"] for f in data["files"]]
    return None


def select_tests(changed_files):
    if not changed_files:
        return ALL_TESTS, True, ["No diff available — full run"]

    selected = set()
    run_all  = False
    ci_only  = True
    reasons  = []

    for filepath in changed_files:
        matched = False
        for pattern, tests in MAPPINGS:
            if pattern in filepath:
                matched = True
                if tests is None:
                    run_all = True
                    ci_only = False
                    reasons.append(f"FULL RUN — {filepath}")
                elif len(tests) == 0:
                    reasons.append(f"SKIP — {filepath} (CI/docs change)")
                else:
                    ci_only = False
                    selected.update(tests)
                    reasons.append(f"MAPPED — {filepath} → {', '.join(tests)}")
                break
        if not matched:
            ci_only = False
            run_all = True
            reasons.append(f"UNKNOWN — {filepath} → full run")
        if run_all:
            break

    if run_all:
        return ALL_TESTS, True, reasons
    if ci_only:
        return "", False, reasons
    if not selected:
        return ALL_TESTS, True, ["No mapping found — full run"]
    return ",".join(sorted(selected)), False, reasons


def main():
    print(f"[TestSelector] Repo: {REPO}")
    changed_files = get_changed_files()
    selected_tests, run_all, reasons = select_tests(changed_files) \
        if changed_files is not None else (ALL_TESTS, True, ["No diff"])

    ci_only     = (not run_all and not selected_tests)
    output_tests = selected_tests if selected_tests else ALL_TESTS

    print("\n" + "=" * 50)
    print("  INTELLIGENT TEST SELECTOR")
    print("=" * 50)
    for r in reasons:
        print(f"  {r}")
    print(f"\n  Selected: {output_tests}")
    print(f"  Run all : {run_all}")
    print("=" * 50 + "\n")

    if GH_OUTPUT:
        with open(GH_OUTPUT, "a") as f:
            f.write(f"selected_tests={output_tests}\n")
            f.write(f"run_all={str(run_all).lower()}\n")
            f.write(f"ci_only_change={str(ci_only).lower()}\n")


if __name__ == "__main__":
    main()

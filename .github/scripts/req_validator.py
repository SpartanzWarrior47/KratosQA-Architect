#!/usr/bin/env python3
"""
RequirementValidatorAgent — KratosQA-Architect
===============================================
Pre-validates a product requirement BEFORE passing it to the
AI Requirement → Test Strategy Generator.

Detects:
  - Ambiguous terms (valid, appropriate, reasonable)
  - Missing constraints (min/max, data types, units)
  - Missing edge cases (what happens on invalid input?)
  - Conflicting logic
  - Untestable requirements
  - Missing actor / missing observable outcome

Decision:
  PASS  → clear enough, proceed to strategy generation
  WARN  → minor gaps, proceed with stated assumptions
  BLOCK → too ambiguous, stop and ask PM to clarify

Usage:
  python req_validator.py "User can add item to cart"
  REQUIREMENT="..." python req_validator.py

Environment variables:
  ANTHROPIC_API_KEY       — Claude API key
  SKIP_VALIDATION         — set "true" to bypass (emergency only)
  VALIDATION_STRICT_MODE  — set "true" to treat WARN as BLOCK
"""

import os
import sys
import json
import urllib.request
import urllib.error

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SKIP_VALIDATION   = os.environ.get("SKIP_VALIDATION", "false").lower() == "true"
STRICT_MODE       = os.environ.get("VALIDATION_STRICT_MODE", "false").lower() == "true"
CLAUDE_MODEL      = "claude-sonnet-4-20250514"

AMBIGUOUS_TERMS = [
    "valid", "invalid", "appropriate", "reasonable", "proper",
    "correct", "incorrect", "good", "bad", "normal", "acceptable",
    "some", "various", "certain", "several", "many", "few",
    "quickly", "slowly", "fast", "soon", "big", "small",
]

MISSING_CONSTRAINT_SIGNALS = [
    "enter", "input", "type", "fill", "provide",
    "submit", "select", "choose", "upload", "set",
]

UNTESTABLE_SIGNALS = [
    "should feel", "should look", "user-friendly",
    "intuitive", "easy to use", "simple", "clean", "nice",
]


def quick_local_check(requirement):
    req_lower = requirement.lower()
    signals   = []
    for term in AMBIGUOUS_TERMS:
        if f" {term} " in f" {req_lower} ":
            signals.append(f"Ambiguous term: '{term}'")
    has_input  = any(v in req_lower for v in MISSING_CONSTRAINT_SIGNALS)
    has_constraint = any(c in req_lower for c in [
        "min", "max", "maximum", "minimum", "between", "range",
        "required", "optional", "characters", "digits", "decimal",
        "integer", "number", "text", "date", "format",
    ])
    if has_input and not has_constraint:
        signals.append("Input field mentioned but no constraints (min/max/format/type)")
    for term in UNTESTABLE_SIGNALS:
        if term in req_lower:
            signals.append(f"Subjective/untestable term: '{term}'")
    has_actor = any(a in req_lower for a in [
        "user", "admin", "guest", "customer", "manager", "system", "app",
    ])
    if not has_actor:
        signals.append("No actor defined")
    has_outcome = any(o in req_lower for o in [
        "see", "view", "display", "show", "navigate", "proceed",
        "submit", "save", "update", "receive", "send",
        "error", "message", "redirect", "enable", "disable",
    ])
    if not has_outcome:
        signals.append("No observable outcome defined")
    return signals


def call_claude_validate(requirement, local_signals):
    if not ANTHROPIC_API_KEY:
        return None

    local_str = "\n".join(f"  - {s}" for s in local_signals) if local_signals else "  None"
    prompt = f"""You are the RequirementValidatorAgent for a QA automation framework.
Validate this requirement before test strategy generation.

REQUIREMENT: "{requirement}"

PRE-CHECK SIGNALS:
{local_str}

Analyse for: AMBIGUITY, MISSING_CONSTRAINT, MISSING_EDGE_CASE,
CONFLICTING_LOGIC, MISSING_ACTOR, UNTESTABLE, MISSING_ERROR_STATE.

Respond ONLY with valid JSON:
{{
  "decision": "PASS | WARN | BLOCK",
  "summary": "one sentence",
  "issues": [
    {{"type": "...", "severity": "CRITICAL|MAJOR|MINOR",
      "description": "...", "example": "..."}}
  ],
  "clarifying_questions": ["Question 1", "Question 2"],
  "assumptions_if_proceeding": ["Assumption 1"],
  "testability_score": 7
}}

PASS = score >= 8, WARN = 5-7, BLOCK = < 5"""

    payload = {
        "model": CLAUDE_MODEL, "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}]
    }
    data    = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json",
               "x-api-key": ANTHROPIC_API_KEY,
               "anthropic-version": "2023-06-01"}
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=data, headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result  = json.loads(resp.read().decode())
            content = result["content"][0]["text"].strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(content)
    except Exception as e:
        print(f"[Validator] Claude API error: {e}")
        return None


def validate_requirement(requirement):
    if SKIP_VALIDATION:
        return {"decision": "PASS", "summary": "Skipped", "issues": [],
                "clarifying_questions": [], "assumptions_if_proceeding": [],
                "testability_score": 10, "local_signals": []}

    local_signals = quick_local_check(requirement)
    result        = call_claude_validate(requirement, local_signals)

    if not result:
        decision = "WARN" if len(local_signals) >= 3 else "PASS"
        return {"decision": decision,
                "summary": f"Local check only. {len(local_signals)} signal(s) found.",
                "issues": [{"type": "LOCAL", "severity": "MINOR",
                            "description": s, "example": ""} for s in local_signals],
                "clarifying_questions": [], "assumptions_if_proceeding": [],
                "testability_score": max(5, 8 - len(local_signals)),
                "local_signals": local_signals}

    result["local_signals"] = local_signals
    if STRICT_MODE and result.get("decision") == "WARN":
        result["decision"]  = "BLOCK"
        result["summary"]  += " [Strict mode]"
    return result


def print_report(result):
    decision = result.get("decision", "UNKNOWN")
    icon     = {"PASS": "✅", "WARN": "⚠️ ", "BLOCK": "🔴"}.get(decision, "⚪")
    print(f"\n{'=' * 60}")
    print("  REQUIREMENT VALIDATOR AGENT")
    print(f"{'=' * 60}")
    print(f"  Decision : {icon} {decision}")
    print(f"  Score    : {result.get('testability_score', '?')}/10")
    print(f"  Summary  : {result.get('summary', '')}")
    if result.get("issues"):
        print()
        for issue in result["issues"]:
            sev_icon = {"CRITICAL": "🔴", "MAJOR": "🟠", "MINOR": "🟡"}.get(issue.get("severity"), "⚪")
            print(f"  {sev_icon} [{issue.get('type')}] {issue.get('description')}")
    if result.get("clarifying_questions"):
        print("\n  📋 Questions for PM:")
        for i, q in enumerate(result["clarifying_questions"], 1):
            print(f"     {i}. {q}")
    print(f"{'=' * 60}\n")


def write_github_output(result):
    gh_output = os.environ.get("GITHUB_OUTPUT", "")
    if not gh_output:
        return
    with open(gh_output, "a") as f:
        f.write(f"validation_decision={result.get('decision', 'PASS')}\n")
        f.write(f"testability_score={result.get('testability_score', 10)}\n")
        f.write(f"validation_passed={str(result.get('decision') != 'BLOCK').lower()}\n")


def main():
    req = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not req and not sys.stdin.isatty():
        req = sys.stdin.read().strip()
    if not req:
        print("Usage: python req_validator.py \"Your requirement here\"")
        sys.exit(1)

    result = validate_requirement(req)
    print_report(result)
    write_github_output(result)
    sys.exit(1 if result["decision"] == "BLOCK" else 0)


if __name__ == "__main__":
    main()

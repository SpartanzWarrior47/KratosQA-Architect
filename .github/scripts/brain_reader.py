#!/usr/bin/env python3
"""
Test Intelligence Brain — Reader
==================================
Utility module imported by other agents to read historical intelligence
from the brain knowledge store on gh-pages.

Usage (in other scripts):
  from brain_reader import BrainReader

  brain = BrainReader()
  context = brain.get_context_for_llm()  # inject into Claude prompts
  risky   = brain.get_risky_modules()    # for prioritization
  flaky   = brain.get_flaky_tests()      # for quarantine decisions
  hints   = brain.get_locator_hints("LoginPage")  # for auto-fixer
"""

import os
import json
import base64
import urllib.request
import urllib.error

REPO   = os.environ.get("GITHUB_REPOSITORY", "your-org/your-repo")
GH_PAT = os.environ.get("GH_PAT", "")
BRANCH = "gh-pages"
PREFIX = "brain"


class BrainReader:
    """Read-only access to the Test Intelligence Brain knowledge store."""

    def __init__(self):
        self._cache  = {}

    def _gh_get(self, url):
        req = urllib.request.Request(url)
        if GH_PAT:
            req.add_header("Authorization", f"Bearer {GH_PAT}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return None

    def _read(self, filename):
        if filename in self._cache:
            return self._cache[filename]
        owner, repo = REPO.split("/")
        data = self._gh_get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/"
            f"{PREFIX}/{filename}?ref={BRANCH}"
        )
        if data and "content" in data:
            try:
                result = json.loads(base64.b64decode(data["content"]).decode())
                self._cache[filename] = result
                return result
            except Exception:
                pass
        self._cache[filename] = {}
        return {}

    def get_failure_root_causes(self):
        return self._read("failure_root_causes.json")

    def get_flaky_tests(self, min_severity="LOW"):
        rank     = {"STABLE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        min_rank = rank.get(min_severity, 0)
        flaky    = self._read("flaky_patterns.json")
        return {
            name: data for name, data in flaky.items()
            if data.get("is_flaky") and rank.get(data.get("severity", "LOW"), 0) >= min_rank
        }

    def get_risky_modules(self, min_level="LOW"):
        rank     = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        min_rank = rank.get(min_level, 0)
        risky    = self._read("risky_modules.json")
        return {
            page: data for page, data in risky.items()
            if rank.get(data.get("risk_level", "LOW"), 0) >= min_rank
        }

    def get_stable_locators(self):
        return self._read("stable_locators.json")

    def get_locator_hints(self, page_class):
        stable = self._read("stable_locators.json")
        risky  = self._read("risky_modules.json")
        hints  = []
        page_stable = stable.get(page_class, {})
        page_risky  = risky.get(page_class, {})
        if page_stable.get("unstable_runs", 0) > 0:
            hints.append(
                f"{page_class} has had {page_stable['unstable_runs']} "
                f"locator failures. Prefer data-testid over CSS class selectors."
            )
        if page_stable.get("notes"):
            hints.extend(page_stable["notes"][-3:])
        if page_risky.get("guidance"):
            hints.append(page_risky["guidance"])
        return hints

    def get_test_risk_history(self, test_name):
        failures = self._read("failure_root_causes.json")
        flaky    = self._read("flaky_patterns.json")
        failure_entry = failures.get(test_name, {})
        flaky_entry   = flaky.get(test_name, {})
        total_failures = sum(failure_entry.get("classifications", {}).values())
        return {
            "total_failures":      total_failures,
            "dominant_class":      failure_entry.get("dominant_class"),
            "last_classification": failure_entry.get("last_classification"),
            "is_flaky":            flaky_entry.get("is_flaky", False),
            "pass_rate":           flaky_entry.get("pass_rate", 100.0),
            "severity":            flaky_entry.get("severity", "STABLE"),
        }

    def get_context_for_llm(self, max_items=10):
        """
        Returns a formatted string summary of brain insights
        for injection into Claude API prompts.
        Every agent that calls Claude should include this context.
        """
        lines = ["\n=== TEST INTELLIGENCE BRAIN CONTEXT ==="]

        risky = self.get_risky_modules(min_level="MEDIUM")
        if risky:
            lines.append("\nHIGH-RISK PAGE OBJECTS (from historical failures):")
            for page, data in list(risky.items())[:5]:
                lines.append(
                    f"  {page}: risk={data['risk_level']}, "
                    f"failures={data['total_failures']}, "
                    f"L1={data['l1_failures']}, L3={data['l3_failures']}"
                )
                lines.append(f"    Guidance: {data['guidance']}")

        flaky = self.get_flaky_tests(min_severity="HIGH")
        if flaky:
            lines.append("\nCRITICAL/HIGH FLAKY TESTS:")
            for test, data in list(flaky.items())[:max_items]:
                lines.append(
                    f"  {test}: {data['pass_rate']}% pass rate "
                    f"({data['severity']}) — {data.get('root_cause_hint', 'unknown')}"
                )

        failures = self.get_failure_root_causes()
        l1_heavy = [
            (name, data) for name, data in failures.items()
            if data.get("classifications", {}).get("L1", 0) >= 3
        ]
        if l1_heavy:
            lines.append("\nREPEATED L1 (LOCATOR) FAILURES — avoid these selector patterns:")
            for name, data in sorted(
                l1_heavy, key=lambda x: x[1]["classifications"]["L1"], reverse=True
            )[:5]:
                lines.append(
                    f"  {name} on {data['page_class']}: "
                    f"{data['classifications']['L1']} L1 failures"
                )

        if len(lines) == 1:
            lines.append("  No historical data yet — brain not populated.")
        lines.append("=" * 42)
        return "\n".join(lines)

    def get_prioritization_boost(self, test_classes):
        boosts = {}
        for tc in test_classes:
            history = self.get_test_risk_history(tc)
            boost   = 0.0
            if history["is_flaky"]:
                pass_rate = history["pass_rate"]
                if pass_rate < 50:   boost += 3.0
                elif pass_rate < 70: boost += 2.0
                elif pass_rate < 90: boost += 1.0
            if history["total_failures"] >= 5:
                boost += 0.5
            boosts[tc] = round(boost, 1)
        return boosts


if __name__ == "__main__":
    brain = BrainReader()
    print(brain.get_context_for_llm())
    print("\nRisky modules:", list(brain.get_risky_modules().keys()))
    print("Flaky tests:",   list(brain.get_flaky_tests().keys()))

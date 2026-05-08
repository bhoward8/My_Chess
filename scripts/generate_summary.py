"""
Parse a pytest JUnit XML report and write a Markdown summary to
$GITHUB_STEP_SUMMARY, grouped by test module (test_evaluation,
test_predicates, test_search, …).

Usage:
    python scripts/generate_summary.py <path/to/test-results.xml>

Falls back to stdout when $GITHUB_STEP_SUMMARY is not set (local runs).
"""

import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict


def parse_junit(xml_path: str):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    suites = root.findall("testsuite") if root.tag == "testsuites" else [root]

    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for suite in suites:
        totals["tests"]    += int(suite.get("tests",    0))
        totals["failures"] += int(suite.get("failures", 0))
        totals["errors"]   += int(suite.get("errors",   0))
        totals["skipped"]  += int(suite.get("skipped",  0))

        for tc in suite.findall("testcase"):
            classname = tc.get("classname", "unknown")
            module    = classname.split(".")[-1]   # e.g. "tests.test_eval" -> "test_eval"
            name      = tc.get("name", "unknown")

            if tc.find("failure") is not None:
                status = "FAIL"
            elif tc.find("error") is not None:
                status = "ERROR"
            elif tc.find("skipped") is not None:
                status = "SKIP"
            else:
                status = "PASS"

            groups[module].append((name, status))

    return groups, totals


def write_summary(groups: dict, totals: dict, out) -> None:
    passed = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]

    out.write("## Test Results\n\n")
    out.write(
        f"**{passed} passed** | "
        f"**{totals['failures'] + totals['errors']} failed** | "
        f"**{totals['skipped']} skipped** | "
        f"**{totals['tests']} total**\n\n"
    )

    for module in sorted(groups):
        tests = groups[module]
        n_passed = sum(1 for _, s in tests if s == "PASS")
        out.write(f"### `{module}` &mdash; {n_passed}/{len(tests)} passed\n\n")
        out.write("| Result | Test |\n")
        out.write("|--------|------|\n")
        for name, status in tests:
            out.write(f"| {status} | `{name}` |\n")
        out.write("\n")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: generate_summary.py <junit-xml>", file=sys.stderr)
        sys.exit(1)

    xml_path = sys.argv[1]
    groups, totals = parse_junit(xml_path)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            write_summary(groups, totals, f)
    else:
        write_summary(groups, totals, sys.stdout)


if __name__ == "__main__":
    main()

"""CLI entry point for the journal copy-edit tool.

Reads ``.copyedit-rules.yaml`` from the repo root and applies regex
substitutions to the files passed on the command line. Designed to run as a
pre-commit hook (auto-fix mode) and as a CI check (``--check``).

Examples
--------
    # Pre-commit: rewrite files in place; exit non-zero if anything changed so
    # the developer is prompted to re-stage.
    copyedit file1.tex file2.tex

    # CI / one-off audit: report violations without touching files.
    copyedit --check $(git ls-files '*.tex')

    # Full audit including audit-only rules (e.g. 5-digit number candidates).
    copyedit --check --audit $(git ls-files '*.tex')
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lsst.dptwo.utils.copyedit import apply_rule, find_matches, load_rules, report_match


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rules",
        default=".copyedit-rules.yaml",
        help="Path to rules YAML (default: .copyedit-rules.yaml)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report violations only; do not modify files. Exit 1 on hits.",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Also report audit-only rules (never auto-applied; for human review).",
    )
    parser.add_argument("files", nargs="*", help="Files to process.")
    args = parser.parse_args()

    rules_path = Path(args.rules)
    if not rules_path.exists():
        print(f"copyedit: rules file not found: {rules_path}", file=sys.stderr)
        return 2
    rules = load_rules(rules_path)
    if not rules:
        return 0

    fix_rules = [r for r in rules if not r["audit_only"]]
    audit_rules = [r for r in rules if r["audit_only"]] if args.audit else []

    any_fixes = False
    any_audits = False
    for f in args.files:
        path = Path(f)
        if not path.is_file():
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue

        running = text
        per_file_summary: list[tuple[dict, int]] = []
        check_reports: list[tuple[dict, str, re.Match]] = []
        for rule in fix_rules:
            matches = find_matches(running, rule)
            if not matches:
                continue
            per_file_summary.append((rule, len(matches)))
            if args.check:
                for m in matches:
                    check_reports.append((rule, running, m))
            running, _ = apply_rule(running, rule)

        if per_file_summary:
            any_fixes = True
            if args.check:
                for rule, snapshot, m in check_reports:
                    print(report_match(f, snapshot, rule, m))
            else:
                path.write_text(running)
                summary = ", ".join(
                    f"{rule['name']}×{n}" for rule, n in per_file_summary
                )
                print(f"copyedit: fixed {f} ({summary})")

        for rule in audit_rules:
            for m in find_matches(running, rule):
                any_audits = True
                print(report_match(f, running, rule, m))

    if args.audit and any_audits:
        return 1
    return 1 if any_fixes else 0

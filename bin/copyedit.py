#!/usr/bin/env python
"""CLI entry point for the journal copy-edit tool.

Reads ``.copyedit-rules.yaml`` from the repo root and applies regex
substitutions to the files passed on the command line.
Designed to run as stand alone and as a pre-commit hook

Examples
--------
    # Rewrite files in place; exit non-zero if anything changed
    bin/copyedit.py file1.tex file2.tex

    # Report violations without touching files.
    bin/copyedit.py --check $(git ls-files '*.tex')

    # Full audit including audit-only rules (e.g. 5-digit number candidates).
    bin/copyedit.py --check --audit $(git ls-files '*.tex')
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from lsst.dptwo.utils.copyedit import load_rules, process_file


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
        fixed, audited = process_file(Path(f), fix_rules, audit_rules, args.check)
        any_fixes = any_fixes or fixed
        any_audits = any_audits or audited

    if args.audit and any_audits:
        return 1
    return 1 if any_fixes else 0


if __name__ == "__main__":
    sys.exit(main())

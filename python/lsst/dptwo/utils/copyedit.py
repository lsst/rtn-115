"""Apply journal copy-edit rules to LaTeX files.

Reads ``.copyedit-rules.yaml`` from the repo root and applies regex
substitutions to the files passed on the command line. Designed to run as a
pre-commit hook (auto-fix mode) and as a CI check (``--check``).

Examples
--------
    # Pre-commit: rewrite files in place; exit non-zero if anything changed so
    # the developer is prompted to re-stage.
    python scripts/copyedit.py file1.tex file2.tex

    # CI / one-off audit: report violations without touching files.
    python scripts/copyedit.py --check $(git ls-files '*.tex')

    # Full audit including audit-only rules (e.g. 5-digit number candidates).
    python scripts/copyedit.py --check --audit $(git ls-files '*.tex')
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml


def load_rules(path: Path) -> list[dict]:
    """Parse the rules YAML and pre-compile each pattern.

    Per-rule fields:
      pattern, replacement       -- required.
      note                        -- free text.
      audit_only                  -- if true, never auto-applied; only reported
                                     when the script runs with --audit. For
                                     high-false-positive rules.
      skip_lines_matching         -- optional regex. Whole input lines matching
                                     this expression are excluded from the rule
                                     (used to leave LaTeX section/caption titles
                                     alone while still rewriting body prose).
    """
    data = yaml.safe_load(path.read_text()) or {}
    out: list[dict] = []
    for r in data.get("rules") or []:
        skip = r.get("skip_lines_matching")
        out.append(
            {
                "name": r.get("name") or r["pattern"],
                "pattern": re.compile(r["pattern"]),
                "replacement": r["replacement"],
                "note": r.get("note", ""),
                "audit_only": bool(r.get("audit_only", False)),
                "skip_lines_matching": re.compile(skip) if skip else None,
            }
        )
    return out


def _skip_ranges(text: str, skip_re: re.Pattern | None) -> list[tuple[int, int]]:
    """Return (start, end) byte ranges of lines that match ``skip_re``."""
    if skip_re is None:
        return []
    ranges: list[tuple[int, int]] = []
    pos = 0
    for line in text.splitlines(keepends=True):
        end = pos + len(line)
        if skip_re.search(line):
            ranges.append((pos, end))
        pos = end
    return ranges


def _in_skip(pos: int, ranges: list[tuple[int, int]]) -> bool:
    return any(s <= pos < e for s, e in ranges)


def find_matches(text: str, rule: dict) -> list[re.Match]:
    """All matches of ``rule['pattern']`` outside any skip range."""
    skip_ranges = _skip_ranges(text, rule["skip_lines_matching"])
    return [
        m for m in rule["pattern"].finditer(text)
        if not _in_skip(m.start(), skip_ranges)
    ]


def apply_rule(text: str, rule: dict) -> tuple[str, int]:
    """Return ``(new_text, count)``. Skipped matches are left as-is."""
    skip_ranges = _skip_ranges(text, rule["skip_lines_matching"])
    counter = [0]

    def replace(m: re.Match) -> str:
        if _in_skip(m.start(), skip_ranges):
            return m.group(0)
        counter[0] += 1
        return m.expand(rule["replacement"])

    new_text = rule["pattern"].sub(replace, text)
    return new_text, counter[0]


def report_match(path_str: str, text: str, rule: dict, m: re.Match) -> str:
    """Format a single violation as ``path:line: [rule] line-content``."""
    line_no = text.count("\n", 0, m.start()) + 1
    line_start = text.rfind("\n", 0, m.start()) + 1
    line_end = text.find("\n", m.end())
    if line_end == -1:
        line_end = len(text)
    snippet = text[line_start:line_end].strip()
    return f"{path_str}:{line_no}: [{rule['name']}] {snippet}"



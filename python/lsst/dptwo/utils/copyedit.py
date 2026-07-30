"""Library functions for applying journal copy-edit rules to LaTeX files."""

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
        m
        for m in rule["pattern"].finditer(text)
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


def process_file(
    path: Path,
    fix_rules: list[dict],
    audit_rules: list[dict],
    check: bool,
) -> tuple[bool, bool]:
    """Apply rules to one file; return ``(any_fixes, any_audits)``.

    In fix mode rewrites the file in place and prints a summary line.
    In check mode prints each violation without modifying the file.
    """
    if not path.is_file():
        return False, False
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        return False, False

    running = text
    per_file_summary: list[tuple[dict, int]] = []
    check_reports: list[tuple[dict, str, re.Match]] = []
    for rule in fix_rules:
        matches = find_matches(running, rule)
        if not matches:
            continue
        per_file_summary.append((rule, len(matches)))
        if check:
            for m in matches:
                check_reports.append((rule, running, m))
        running, _ = apply_rule(running, rule)

    any_fixes = bool(per_file_summary)
    if any_fixes:
        if check:
            for rule, snapshot, m in check_reports:
                print(report_match(str(path), snapshot, rule, m))
        else:
            path.write_text(running)
            summary = ", ".join(f"{rule['name']}×{n}" for rule, n in per_file_summary)
            print(f"copyedit: fixed {path} ({summary})")

    any_audits = False
    for rule in audit_rules:
        for m in find_matches(running, rule):
            any_audits = True
            print(report_match(str(path), running, rule, m))

    return any_fixes, any_audits

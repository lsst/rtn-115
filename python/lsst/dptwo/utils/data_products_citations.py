# This file is part of texmf.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.
"""Check that every data product subsection in ``data_products.tex`` cites
a reference in its first sentence.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = [
    "find_uncited_sections",
    "check_citations",
]

_SECTION_HEADING_RE = re.compile(r"^\\(subsubsection|paragraph)\*?\{(?P<title>[^{}]*)\}\s*$")
_LABEL_RE = re.compile(r"^\\label\{")
_CITE_RE = re.compile(r"\\cite[a-z]*\*?\{")
_SENTENCE_END_RE = re.compile(r"[.!?]\s*$")


def _first_sentence(lines: list[str], start: int, end: int) -> str | None:
    """Join lines[start:end] up to (and including) the first sentence-ending
    line, skipping blank lines, comments, and \\label{} lines. Returns None
    if the span contains no body text at all.
    """
    buf: list[str] = []
    for line in lines[start:end]:
        stripped = line.strip()
        if not stripped:
            if buf:
                break
            continue
        if stripped.startswith("%") or _LABEL_RE.match(stripped):
            continue
        buf.append(stripped)
        if _SENTENCE_END_RE.search(stripped):
            break
    return " ".join(buf) if buf else None


def find_uncited_sections(text: str) -> list[tuple[int, str, str]]:
    """Return ``(line_no, kind, title)`` for every \\subsubsection or
    \\paragraph whose first sentence contains no \\cite... command.

    A \\subsubsection that directly contains \\paragraph headings (before the
    next \\subsubsection) is not itself checked; only its \\paragraph children
    are, on the assumption that the subsubsection's own text is scene-setting
    and citations belong with the specific paragraph they support.

    Sections with no body text at all (heading immediately followed by
    another heading) are reported as violations too.
    """
    lines = text.splitlines()
    headings: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines):
        m = _SECTION_HEADING_RE.match(line.strip())
        if m:
            headings.append((i, m.group(1), m.group("title")))

    violations: list[tuple[int, str, str]] = []
    for idx, (line_idx, kind, title) in enumerate(headings):
        if kind == "subsubsection":
            has_paragraph_child = False
            for _, nxt_kind, _title in headings[idx + 1:]:
                if nxt_kind == "subsubsection":
                    break
                if nxt_kind == "paragraph":
                    has_paragraph_child = True
                    break
            if has_paragraph_child:
                continue

        end_line = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines)
        sentence = _first_sentence(lines, line_idx + 1, end_line)
        if sentence is None or not _CITE_RE.search(sentence):
            violations.append((line_idx + 1, kind, title))

    return violations


def check_citations(path: Path) -> bool:
    """Print a report line for every uncited subsubsection/paragraph in
    ``path``. Returns True if any violations were found.
    """
    if not path.is_file():
        return False
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        return False

    violations = find_uncited_sections(text)
    for line_no, kind, title in violations:
        print(f"{path}:{line_no}: [{kind}-citation] no DOI citation in first sentence of \"{title}\"")
    return bool(violations)

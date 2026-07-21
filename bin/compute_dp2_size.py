#!/usr/bin/env python3
"""Compute total DP2 size from data/dp2_size_breakdown.txt.

Sums the "File Size" column (human-readable) without multiplying by File Count.
"""

import re
import sys
from pathlib import Path

DEFAULT_INPUT = Path(__file__).parent.parent / "data" / "dp2_size_breakdown.txt"

UNITS = {
    "kB": 1e3,
    "MB": 1e6,
    "GB": 1e9,
    "TB": 1e12,
    "PB": 1e15,
}


def parse_file_size(s: str) -> float:
    m = re.match(r"([\d.]+)\s*(\w+)", s.strip())
    if not m:
        raise ValueError(f"Cannot parse size: {s!r}")
    value, unit = float(m.group(1)), m.group(2)
    return value * UNITS[unit]


def parse_size_breakdown(path: Path) -> float:
    total = 0.0
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|") or line.startswith("|-"):
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if cols[0] == "Dataset Type":
                continue
            total += parse_file_size(cols[3])
    return total


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    total_bytes = parse_size_breakdown(path)
    print(f"Total TB:    {total_bytes / 1e12:.2f} TB")
    print(f"Total PB:    {total_bytes / 1e15:.3f} PB")


if __name__ == "__main__":
    main()

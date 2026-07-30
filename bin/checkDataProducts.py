#!/usr/bin/env python
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
"""Check ``sections/data_products.tex`` for subsections missing a citation.

Every \\subsubsection{} is expected to cite a reference in its first
sentence, unless it is broken up into \\paragraph{} blocks, in which case
each \\paragraph{} is checked instead (and the subsubsection's own intro
text is not).

Example
-------
    bin/checkDataProducts.py sections/data_products.tex
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from lsst.dptwo.utils.data_products_citations import check_citations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "file",
        nargs="?",
        default="sections/data_products.tex",
        help="Path to data_products.tex (default: sections/data_products.tex).",
    )
    args = parser.parse_args()

    any_violations = check_citations(Path(args.file))
    return 1 if any_violations else 0


if __name__ == "__main__":
    sys.exit(main())

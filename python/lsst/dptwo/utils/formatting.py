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
"""Shared utilities for DP2 LaTeX helpers."""

from __future__ import annotations

__all__ = [
    "custom_float",
    "num2word",
    "round_sf",
    "unit_to_latex",
]

import math
from typing import Any

import numpy as np


def custom_float(value: Any) -> Any:
    """Render floats with three decimal places for display."""
    if isinstance(value, float):
        return f"{value:.3f}"
    return value


def num2word(num: int) -> str:
    """Convert selected integers to English words."""
    num_to_word = {
        0: "Zero",
        1: "One",
        2: "Two",
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
        8: "Eight",
        9: "Nine",
        10: "Ten",
        11: "Eleven",
        12: "Twelve",
        13: "Thirteen",
        14: "Fourteen",
        15: "Fifteen",
        16: "Sixteen",
        17: "Seventeen",
        18: "Eighteen",
        19: "Nineteen",
        20: "Twenty",
        30: "Thirty",
        40: "Forty",
        50: "Fifty",
        60: "Sixty",
        70: "Seventy",
        80: "Eighty",
        90: "Ninety",
    }
    return num_to_word.get(num, str(num))


_UNIT_TO_LATEX = {
    "square degrees": "deg$^{\\rm 2}$",
}


def unit_to_latex(unit: str) -> str:
    """Return the LaTeX representation of a plain-text unit string.

    Returns the original string unchanged if no mapping is defined.
    """
    return _UNIT_TO_LATEX.get(unit, unit)


def round_sf(value: float, sig: int = 3) -> float:
    """Round a number to the requested significant figures."""
    if value == 0:
        return 0.0
    return float(np.round(value, sig - int(math.floor(math.log10(abs(value)))) - 1))

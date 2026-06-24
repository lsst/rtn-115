# This file is part of rtn-115
#
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.

"""Tests for small reusable DP2 utilities."""

from __future__ import annotations

import unittest

from lsst.dptwo.utils import num2word, round_sf


class UtilsTestCase(unittest.TestCase):
    """Tests for helper utilities used by table and parameter code."""

    def test_num2word(self) -> None:
        self.assertEqual(num2word(1), "One")
        self.assertEqual(num2word(20), "Twenty")
        self.assertEqual(num2word(99), "99")

    def test_round_sf(self) -> None:
        self.assertAlmostEqual(round_sf(1.23456, sig=3), 1.23)
        self.assertAlmostEqual(round_sf(0.004567, sig=2), 0.0046)
        self.assertAlmostEqual(round_sf(12345.0, sig=2), 12000.0)


if __name__ == "__main__":
    unittest.main()

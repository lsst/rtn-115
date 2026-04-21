# This file is part of rtn-115
#
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.

"""Tests for the DP2 parameter writer."""

import unittest
from pathlib import Path

from lsst.texmf.parameters import DP2Parameters, addParameter, formatParameter

OUTPUT_DIR = Path("tests/outputs")
OUTPUT_FILE = OUTPUT_DIR / "test_parameters_output.tex"


class ParameterWriterTestCase(unittest.TestCase):
    """Tests for the callable parameter-writing API."""

    def setUp(self) -> None:
        self.params = DP2Parameters()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def test_add_parameter_stores_value_and_unit(self) -> None:
        self.params.add("nvisits", 1792)
        self.params.add("exposuretime", 30, unit="s")

        self.assertEqual(list(self.params.values.keys()), ["nvisits", "exposuretime"])
        self.assertEqual(self.params.values["nvisits"], 1792)
        self.assertEqual(self.params.units["exposuretime"], "s")

    def test_add_parameter_rounds_significant_figures(self) -> None:
        self.params.add("bestimagequality", 0.5793, unit="\\arcsec", sig=2)
        self.assertAlmostEqual(self.params.values["bestimagequality"], 0.58)

    def test_format_parameter_for_plain_value(self) -> None:
        self.params.add("campaignstartdate", "2024-10-24")
        self.assertEqual(
            formatParameter(self.params, "campaignstartdate"),
            "\\newcommand{\\campaignstartdate}{2024-10-24\\xspace}\n",
        )

    def test_format_parameter_for_regular_unit(self) -> None:
        self.params.add("exposuretime", 30, unit="s")
        self.assertEqual(
            formatParameter(self.params, "exposuretime"),
            "\\newcommand{\\exposuretime}{30\\xspace s\\xspace}\n",
        )

    def test_format_parameter_for_angular_unit(self) -> None:
        self.params.add("bestimagequality", 0.58, unit="\\arcsec")
        self.assertEqual(
            formatParameter(self.params, "bestimagequality"),
            "\\newcommand{\\bestimagequality}{0\\farcs58\\xspace}\n",
        )

    def test_format_parameter_for_url_value(self) -> None:
        self.params.add(
            "sciencepipelinesurl",
            r"\nolinkurl{https://pipelines.lsst.io/v/v29\_1\_1}",
        )
        self.assertEqual(
            formatParameter(self.params, "sciencepipelinesurl"),
            "\\newcommand{\\sciencepipelinesurl}{\\nolinkurl{https://pipelines.lsst.io/v/v29\\_1\\_1}\\xspace}\n",
        )

    def test_format_parameter_for_angular_unit_with_suffix(self) -> None:
        self.params.add("visitimageplatescale", 0.2, unit="\\arcsec per pixel")
        self.assertEqual(
            formatParameter(self.params, "visitimageplatescale"),
            "\\newcommand{\\visitimageplatescale}{0\\farcs2 per pixel\\xspace}\n",
        )

    def test_add_parameter_wrapper_returns_store(self) -> None:
        returned = addParameter(self.params, "nfields", "seven")
        self.assertIs(returned, self.params)
        self.assertEqual(self.params.values["nfields"], "seven")

    def test_write_creates_tex_file(self) -> None:
        self.params.add("campaignstartdate", "2024-10-24")
        self.params.add("nvisits", 1792)
        self.params.add("bestimagequality", 0.58, unit="\\arcsec")

        written = self.params.write(OUTPUT_FILE)

        self.assertEqual(written, OUTPUT_FILE.resolve())
        self.assertTrue(OUTPUT_FILE.exists())
        content = OUTPUT_FILE.read_text()
        self.assertIn("automatically generated", content)
        self.assertIn("python/lsst/texmf/parameters.py", content)
        self.assertIn("\\newcommand{\\campaignstartdate}{2024-10-24\\xspace}", content)
        self.assertIn("\\newcommand{\\nvisits}{1792\\xspace}", content)
        self.assertIn("\\newcommand{\\bestimagequality}{0\\farcs58\\xspace}", content)

    def test_write_creates_explicit_output_in_test_directory(self) -> None:
        self.params.add("campaignstartdate", "2024-10-24")
        written = self.params.write(OUTPUT_FILE)

        self.assertEqual(written, OUTPUT_FILE.resolve())
        self.assertTrue(written.exists())

if __name__ == "__main__":
    unittest.main()

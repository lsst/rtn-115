import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from lsst.dptwo.render.tables import (
    make_simple_table, make_per_band_summary_table,
)

def get_per_band_summary_dataframe():
    """Build the example IQ-per-band-per-target DataFrame.
    including aggregate column and row
    """
    data = {
        "g":   [3.42, 2.77, 3.34, 2.87, 3.32, 2.72, 3.80, 2.93],
        "i":   [2.61, 2.12, 2.57, 1.84, 1.99, 2.55, np.nan, 2.25],
        "r":   [3.33, 2.48, 3.06, 1.45, 2.78, 2.70, 3.00, 2.67],
        "u":   [np.nan, 4.18, 7.50, np.nan, 4.15, np.nan, 4.80, 4.65],
        "y":   [3.77, 2.44, 2.07, np.nan, 1.44, np.nan, np.nan, 2.18],
        "z":   [np.nan, 2.14, 2.94, np.nan, 2.91, 3.14, 3.03, 2.60],
        "All": [3.18, 2.48, 2.99, 1.55, 2.99, 2.71, 3.35, 2.69],
    }
    targets = [
        "47_Tuc", "ECDFS", "EDFS_comcam", "Fornax_dSph",
        "Rubin_SV_095_-25", "Rubin_SV_38_7", "Seagull", "All",
    ]
    df = pd.DataFrame(data, index=targets)
    df.index.name = "target"
    df.columns.name = "band"
    df.attrs["label"] = "per_band_summary"

    # Define the desired column order
    band_order = ['u', 'g', 'r', 'i', 'z', 'y']
    df = df[band_order + ['All']]  # Keep 'All' as the last column
    return df

class TablesTestCase(unittest.TestCase):
    """Tests for DP2 tables."""

    OUTPUT_DIR = Path("tests/outputs")
    PER_BAND_CAPTION_BASE = (
        "DP1 Median image quality per field and per band quantified "
        "as the PSF at FWHM in arcseconds. "
    )
    PER_BAND_LABEL = "tab:DP2_per_band_summary"

    @classmethod
    def setUpClass(cls):
        """Set up the global setup for the tests."""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Open the LaTeX file for writing the preamble
        cls.file_path = cls.OUTPUT_DIR / "test_tables_output.tex"
        with open(cls.file_path, "w", encoding="utf-8") as f:
            f.write(r"\documentclass{aastex7}" + "\n")
            f.write(r"\begin{document}" + "\n")

    @classmethod
    def tearDownClass(cls):
        """Global teardown to close the LaTeX document."""
        with open(cls.file_path, "a", encoding="utf-8") as f:
            f.write(r"\end{document}" + "\n")

    def setUp(self):
        """Set up for each individual test."""

        self.test_simple_3 = pd.DataFrame({
            "Name": ["a", "b", "c"],
            "Value": ["1", "2", "3"],
            "Description": ["ParA", "ParB", "Pr3"]
        })
        self.test_simple_3.attrs["label"] = "simple_table_3"

        self.test_simple_2 = pd.DataFrame({
            "Name": ["a", "b", "c"],
            "Value": ["1", "2", "3"],
        })
        self.test_simple_2.attrs["label"] = "simple_table_2"

        self.test_simple_4 = pd.DataFrame({
            "Name": ["a", "b", "c"],
            "Description": [
                "A longer description with several words to mimic realistic manuscript table content.",
                "Another extended description containing enough text to exercise wider cell content.",
                "Randomized-style placeholder prose for testing how longer descriptions render in LaTeX.",
            ],
        })
        self.test_simple_4.attrs["label"] = "simple_table_4"

        self.per_band_summary = get_per_band_summary_dataframe()

    def write_latex_to_file(self, latex_str):
        """Helper function to write LaTeX string to file with a new page."""
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(latex_str + "\n")
            f.write(r"\newpage" + "\n")  # Add a new page after each table

    def test_simple_tables(self):
        cases = [
            ("simple_table_2", self.test_simple_2, False, r"\begin{deluxetable}"),
            ("simple_table_3", self.test_simple_3, False, r"\begin{deluxetable}"),
            ("simple_table_3_wide", self.test_simple_3, True, r"\begin{deluxetable*}"),
        ]

        for name, df, expand_across_columns, expected_environment in cases:
            with self.subTest(name=name):
                latex_str = make_simple_table(
                    df,
                    caption="Test caption",
                    expand_across_columns=expand_across_columns,
                )
                self.assertIsNotNone(latex_str)
                self.assertIn(expected_environment, latex_str)
                self.assertIn(r"\tablewidth{0pt}", latex_str)
                self.assertIn("Test caption", latex_str)
                self.write_latex_to_file(latex_str)

    def test_simple_table_single_column_width(self):
        expected_column_spec = "l" + "c" * (self.test_simple_3.shape[1] - 1)
        latex_str = make_simple_table(
            self.test_simple_3,
            caption="Single-column caption",
        )
        self.assertIn(r"\begin{deluxetable}", latex_str)
        self.assertNotIn(r"\begin{deluxetable*}", latex_str)
        self.assertIn(r"\tablewidth{0pt}", latex_str)
        self.assertIn(
            rf"\begin{{deluxetable}}{{{expected_column_spec}}}",
            latex_str,
        )
        self.write_latex_to_file(latex_str)

    def test_simple_table_full_width(self):
        expected_column_spec = "l" + "c" * (self.test_simple_4.shape[1] - 1)
        latex_str = make_simple_table(
            self.test_simple_4,
            caption="Full-width caption",
            expand_across_columns=True,
        )
        self.assertIn(r"\begin{deluxetable*}", latex_str)
        self.assertIn(r"\tablewidth{0pt}", latex_str)
        self.assertIn(
            rf"\begin{{deluxetable*}}{{{expected_column_spec}}}",
            latex_str,
        )
        self.write_latex_to_file(latex_str)

    def test_per_band_summary_variants(self):
        """Generate the IQ table across the supported aggregation modes."""
        cases = [
            (
                "with_aggregation",
                "with aggregate across and aggregate All row",
                {},
            ),
            (
                "no_aggregation",
                "",
                {"include_all_col": False, "include_all_row": False},
            ),
            (
                "row_aggregation",
                "with aggregate All row",
                {"include_all_col": False, "include_all_row": True},
            ),
            (
                "col_aggregation",
                "with aggregate per row",
                {"include_all_col": True, "include_all_row": False},
            ),
        ]

        for name, caption_suffix, kwargs in cases:
            with self.subTest(name=name):
                caption = self.PER_BAND_CAPTION_BASE + caption_suffix
                latex_str = make_per_band_summary_table(
                    self.per_band_summary,
                    caption=caption,
                    label="tab:iq_band_field",
                    **kwargs,
                )
                self.assertIsNotNone(latex_str)
                self.assertIn(r"\begin{deluxetable}", latex_str)
                self.assertIn(self.PER_BAND_LABEL, latex_str)
                self.assertIn(caption, latex_str)
                self.write_latex_to_file(latex_str)

if __name__ == "__main__":
    unittest.main()

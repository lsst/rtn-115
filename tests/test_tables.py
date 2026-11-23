import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from lsst.dptwo.utils.tables import (
    make_simple_table,
    make_per_band_summary_table,
)


def get_per_band_summary_dataframe():
    """Build the example IQ-per-band-per-target DataFrame.
    including aggregate column and row
    """
    data = {
        "g": [3.42, 2.77, 3.34, 2.87, 3.32, 2.72, 3.80, 2.93],
        "i": [2.61, 2.12, 2.57, 1.84, 1.99, 2.55, np.nan, 2.25],
        "r": [3.33, 2.48, 3.06, 1.45, 2.78, 2.70, 3.00, 2.67],
        "u": [np.nan, 4.18, 7.50, np.nan, 4.15, np.nan, 4.80, 4.65],
        "y": [3.77, 2.44, 2.07, np.nan, 1.44, np.nan, np.nan, 2.18],
        "z": [np.nan, 2.14, 2.94, np.nan, 2.91, 3.14, 3.03, 2.60],
        "All": [3.18, 2.48, 2.99, 1.55, 2.99, 2.71, 3.35, 2.69],
    }
    targets = [
        "47_Tuc",
        "ECDFS",
        "EDFS_comcam",
        "Fornax_dSph",
        "Rubin_SV_095_-25",
        "Rubin_SV_38_7",
        "Seagull",
        "All",
    ]
    df = pd.DataFrame(data, index=targets)
    df.index.name = "target"
    df.columns.name = "band"
    df.attrs["label"] = "per_band_summary"

    # Define the desired column order
    band_order = ["u", "g", "r", "i", "z", "y"]
    df = df[band_order + ["All"]]  # Keep 'All' as the last column
    return df


class TablesTestCase(unittest.TestCase):
    """Tests for DP2 tables."""

    OUTPUT_DIR = Path("tests/outputs")
    PER_BAND_CAPTION_BASE = (
        "DP2 Median image quality per field and per band quantified "
        "as the PSF at FWHM in arcseconds. "
    )
    PER_BAND_LABEL = "tab:dp2_per_band_summary"

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

        self.test_simple_3 = pd.DataFrame(
            {
                "Name": ["a", "b", "c"],
                "Value": ["1", "2", "3"],
                "Description": ["ParA", "ParB", "Pr3"],
            }
        )
        self.test_simple_3.attrs["label"] = "simple_table_3"

        self.test_simple_2 = pd.DataFrame(
            {
                "Name": ["a", "b", "c"],
                "Value": ["1", "2", "3"],
            }
        )
        self.test_simple_2.attrs["label"] = "simple_table_2"

        self.test_simple_4 = pd.DataFrame(
            {
                "Name": ["a", "b", "c"],
                "Description": [
                    "A longer description with several words to mimic realistic manuscript table content.",
                    "Another extended description containing enough text to exercise wider cell content.",
                    "Randomized-style placeholder prose for testing how longer descriptions render in LaTeX.",
                ],
            }
        )
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

    def test_simple_table_units_row(self):
        """Units go on a second header row; no units keeps one row."""
        df = pd.DataFrame(
            {"Field": ["a_b"], "R.A.": ["1.0"], "Nights": ["3"], "Baseline": ["5"]}
        )
        df.attrs["label"] = "simple_units"

        latex_str = make_simple_table(
            df, caption="Units caption", units={"R.A.": "deg", "Baseline": "days"}
        )
        self.assertIn(
            "\\tablehead{\n"
            "  \\colhead{\\textbf{Field}} & \\colhead{\\textbf{R.A.}} & "
            "\\colhead{\\textbf{Nights}} & \\colhead{\\textbf{Baseline}}\\\\\n"
            "   & \\colhead{(deg)} &  & \\colhead{(days)}\n}",
            latex_str,
        )
        self.assertIn(r"a\_b & 1.0 & 3 & 5 \\", latex_str)
        self.write_latex_to_file(latex_str)

        single = make_simple_table(df, caption="No units")
        self.assertNotIn("(deg)", single)
        self.assertIn(
            r"\colhead{\textbf{Baseline}}\\" + "\n}", single
        )

        with self.assertRaises(ValueError):
            make_simple_table(df, caption="Bad", units={"Dec": "deg"})

    def test_per_band_summary_variants(self):
        """Generate the IQ table across the supported aggregation modes."""
        cases = [
            (
                "with_aggregation",
                "with aggregate across and aggregate All row",
                {},
                True,
                True,
            ),
            (
                "no_aggregation",
                "",
                {"include_all_col": False, "include_all_row": False},
                False,
                False,
            ),
            (
                "row_aggregation",
                "with aggregate All row",
                {"include_all_col": False, "include_all_row": True},
                False,
                True,
            ),
            (
                "col_aggregation",
                "with aggregate per row",
                {"include_all_col": True, "include_all_row": False},
                True,
                False,
            ),
        ]

        for name, caption_suffix, kwargs, has_all_col, has_all_row in cases:
            with self.subTest(name=name):
                caption = self.PER_BAND_CAPTION_BASE + caption_suffix
                latex_str = make_per_band_summary_table(
                    self.per_band_summary,
                    caption=caption,
                    **kwargs,
                )
                self.assertIn(r"\begin{deluxetable}", latex_str)
                # AASTeX deluxetables need the label inside the caption block.
                self.assertIn(
                    rf"\tablecaption{{{caption}\label{{{self.PER_BAND_LABEL}}}}}",
                    latex_str,
                )
                self.assertIn(r"\multicolumn{6}{c}{\textbf{Band}}", latex_str)
                self.assertIn(r"\cline{2-7}", latex_str)
                self.assertEqual(
                    r"\colhead{\textbf{All}}" in latex_str, has_all_col
                )
                self.assertEqual(r"\textbf{All} &" in latex_str, has_all_row)
                self.assertEqual(r"\hline" in latex_str, has_all_row)
                n_cols = 1 + 6 + int(has_all_col)
                self.assertIn(
                    rf"\begin{{deluxetable}}{{l{'c' * (n_cols - 1)}}}", latex_str
                )
                self.write_latex_to_file(latex_str)

    def test_per_band_summary_values(self):
        """Missing values, default formatting and row-name escaping."""
        latex_str = make_per_band_summary_table(
            self.per_band_summary, caption="Values", include_all_col=False
        )
        rows = _data_rows(latex_str)
        # 47_Tuc: u missing, g = 3.42.
        self.assertEqual(
            rows[0],
            r"47\_Tuc & \nodata & 3.42 & 3.33 & 2.61 & \nodata & 3.77 \\",
        )
        # Missing values in the summary row are blank, not \nodata.
        df = self.per_band_summary.copy()
        df.loc["All", "u"] = np.nan
        latex_str = make_per_band_summary_table(df, caption="Values")
        self.assertTrue(_data_rows(latex_str)[-1].startswith(r"\textbf{All} &  &"))

    def test_per_band_summary_leading_trailing_columns(self):
        """Single columns before and after the band group, with units."""
        df = _visits_dataframe()
        latex_str = make_per_band_summary_table(
            df,
            caption="Visits",
            bands=BANDS,
            units={"R.A.": "deg", "Decl.": "deg", "Baseline": "days"},
            formats={"R.A.": "{:.1f}", "Decl.": "{:.1f}", "Baseline": "{:.0f}"},
            total_row="Total",
            expand_across_columns=True,
        )
        self.assertIn(r"\begin{deluxetable*}{l" + "c" * 10 + "}", latex_str)
        self.assertIn(r"\label{tab:dp2_visits}", latex_str)
        self.assertIn(
            r"\colhead{\textbf{Decl.}} & \multicolumn{6}{c}{\textbf{Band}} "
            r"& \colhead{\textbf{Total}}",
            latex_str,
        )
        # Band group occupies LaTeX columns 4-9 (index, R.A., Decl. first).
        self.assertIn(r"\cline{4-9}", latex_str)
        self.assertIn(
            r" & \colhead{(deg)} & \colhead{(deg)} & $u$ & $g$ & $r$ & $i$ "
            r"& $z$ & $y$ &  & \colhead{(days)}",
            latex_str,
        )
        rows = _data_rows(latex_str)
        self.assertEqual(
            rows[0],
            r"M49 & 186.3 & 6.9 & 234 & 280 & \nodata & \nodata & \nodata "
            r"& \nodata & 514 & 10 \\",
        )
        self.assertEqual(rows[-2], r"\hline")
        self.assertEqual(
            rows[-1],
            r"\textbf{Total} &  &  & 241 & 280 & 5 & 0 & 0 & 0 & 526 &  \\",
        )
        self.write_latex_to_file(latex_str)

    def test_per_band_summary_no_total_row(self):
        """total_row=None writes every row as data."""
        df = _visits_dataframe()
        latex_str = make_per_band_summary_table(
            df, caption="Visits", bands=BANDS, total_row=None
        )
        self.assertNotIn(r"\hline", latex_str)
        self.assertIn(r"Total & \nodata & \nodata & 241", latex_str)

    def test_per_band_summary_column_spec(self):
        latex_str = make_per_band_summary_table(
            self.per_band_summary, caption="Spec", column_spec="lrrrrrrr"
        )
        self.assertIn(r"\begin{deluxetable}{lrrrrrrr}", latex_str)

    def test_per_band_summary_index_header(self):
        latex_str = make_per_band_summary_table(
            self.per_band_summary, caption="Header", index_header="Field"
        )
        self.assertIn(r"\multicolumn{1}{l}{\textbf{Field}}", latex_str)

    def test_per_band_summary_band_errors(self):
        df = _visits_dataframe()
        with self.assertRaisesRegex(ValueError, "not in DataFrame"):
            make_per_band_summary_table(df, caption="x", bands=["u", "w"])
        with self.assertRaisesRegex(ValueError, "adjacent"):
            make_per_band_summary_table(df, caption="x", bands=["u", "r"])
        with self.assertRaisesRegex(ValueError, "adjacent"):
            make_per_band_summary_table(df, caption="x", bands=["g", "u"])


BANDS = ["u", "g", "r", "i", "z", "y"]


def _visits_dataframe():
    """Visit counts with leading, band and trailing columns and a total row."""
    columns = ["R.A.", "Decl.", *BANDS, "Total", "Baseline"]
    rows = {
        "M49": [186.3, 6.9, 234, 280, None, None, None, None, 514, 10.2],
        "Abell_2764": [5.5, -49.0, 7, None, None, None, None, None, 7, 1.0],
        "Trifid-Lagoon": [271.7, -23.9, None, None, 5, None, None, None, 5, np.nan],
        "Total": [np.nan, np.nan, 241, 280, 5, 0, 0, 0, 526, np.nan],
    }
    df = pd.DataFrame.from_dict(rows, orient="index", columns=columns)
    df[BANDS + ["Total"]] = df[BANDS + ["Total"]].astype("Int64")
    df.attrs["label"] = "visits"
    return df


def _data_rows(latex_str):
    """Lines between \\startdata and \\enddata."""
    lines = latex_str.splitlines()
    return lines[lines.index(r"\startdata") + 1 : lines.index(r"\enddata")]

if __name__ == "__main__":
    unittest.main()

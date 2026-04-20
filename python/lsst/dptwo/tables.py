# This file is part of dptwo.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# Use of this source code is governed by a 3-clause BSD-style
# license that can be found in the LICENSE file.
"""Utilities related to making latex tables for the DP2 paper."""

from __future__ import annotations

__all__ = [
    "make_simple_table",
    "make_per_band_summary_table",
]

import numpy as np
import pandas as pd
from typing import Any, Optional


TABLE_LABEL_PREFIX = "tab"
DP_RELEASE = "DP2"
AUTOGEN_STR = "%%%%% This table is auto generated from data, DO NOT EDIT"

def get_table_label(df_name: str) -> str:
    """
    Generate a standardized LaTeX table label for use in all
    latex tables

    Parameters
    ----------
    dp_version : str
        The data processing version (e.g., 'dp1', 'dp2').
    df_name : str
        A short identifier for the table / DataFrame.

    Returns
    -------
    label : str
        A LaTeX-safe label string, e.g., 'tab:dp1_dimensions'.
    """
    # Remove spaces, replace with underscores, lowercase
    df_name_clean = df_name.strip().replace(" ", "_").lower()
    return f"{TABLE_LABEL_PREFIX}:{DP_RELEASE}_{df_name_clean}"


def make_simple_table(
    df: pd.DataFrame,
    caption: str = None,
    column_spec: Optional[str] = None,
    expand_across_columns: bool = False,
) -> str:
    """
    Make a simple AAS `deluxetable` from a pandas DataFrame.
    The number of columns is the number of columns in the pandas DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing columns to include in the table.
    caption : str
        The table caption.
    label : str
        LaTeX label for referencing the table.
    column_spec : str, optional
        LaTeX column specification string (e.g., 'lp{3.5cm}p{8cm}').
        If not provided, the function generates a dynamic column spec
        based on the number of columns and the target manuscript width.
    expand_across_columns : bool, optional
        If `True`, render the table as a `deluxetable*` spanning both
        columns of a two-column manuscript. Otherwise render a
        single-column `deluxetable`.

    Returns
    -------
    latex_str : str
        The formatted LaTeX deluxetable as a string.
    """

    # Get the table label from DataFrame metadata.
    label = get_table_label(df.attrs["label"])
    environment = "deluxetable*" if expand_across_columns else "deluxetable"

    n_cols = df.shape[1]
    # Use user-provided column spec or generate dynamically
    if column_spec is None:
        column_spec = "l" + "c" * (n_cols - 1)

    table_lines = [r"%%%%% This table is auto generated from data, DO NOT EDIT"]
    table_lines.append(r"\setlength{\tabcolsep}{3pt}")
    table_lines.append(f"\\begin{{{environment}}}{{{column_spec}}}")
    table_lines.append(r"\tablewidth{0pt}")

    table_lines.append(f"\\tablecaption{{{caption}}}")
    table_lines.append(f"\\label{{{label}}}")

    # Table header
    header_cols = " & ".join([f"\\colhead{{\\textbf{{{col}}}}}" for col in df.columns]) + r"\\"
    table_lines.append(r"\tablehead{")
    table_lines.append("  " + header_cols)
    table_lines.append(r"}")
    table_lines.append(r"\startdata")

    # Table rows
    for _, row in df.iterrows():
        row_vals = " & ".join([
            str(val).replace("_", r"\_") if i == 0 else str(val)
            for i, val in enumerate(row)
        ])
        table_lines.append(f"{row_vals} \\\\")

    table_lines.append(r"\enddata")
    table_lines.append(f"\\end{{{environment}}}")

    return "\n".join(table_lines)


def make_per_band_summary_table(
    df: pd.DataFrame,
    caption: str,
    label: str,
    include_all_col: bool = True,
    include_all_row: bool = True,
    column_spec: Optional[str] = None
) -> str:
    """
    Create a LaTeX AAS deluxetable for per-band summary statistics.

    Parameters
    ----------
    data_frame : pd.DataFrame
        DataFrame indexed by target, columns = bands (e.g., u,g,r,i,z,y,All).
    caption : str
        Table caption (mandatory).
    label : str
        LaTeX label (mandatory).
    include_all_col : bool
        Whether to include the 'All' column.
    include_all_row : bool
        Whether to include the 'All' row.
    column_spec : str, optional
        Provide and explicit column specification (e.g., 'lccccccc').
        If None, then the specification is auto-generated.

    Returns
    -------
    table_text : str
        LaTeX deluxetable as a string.
    """

    # Get the table label from DataFrame metadata.
    label = get_table_label(df.attrs["label"])

    # Handle optional inclusion of "All" column/row
    if not include_all_col and "All" in df.columns:
        df = df.drop(columns=["All"])
    if not include_all_row and "All" in df.index:
        df = df.drop(index="All")

    bands = [col for col in df.columns if col != "All"]
    n_band_cols = len(bands)

    # Column specification
    if column_spec is None:
        n_cols = df.shape[1] + 1  # +1 for index column
        # Ensure the first column (for row labels) is left-aligned ('l')
        column_spec = "l" + "c" * (n_cols - 1)

    lines = []
    lines.append(AUTOGEN_STR)
    lines.append(r"\setlength{\tabcolsep}{3pt}")
    lines.append(f"\\begin{{deluxetable}}{{{column_spec}}}")
    lines.append(f"\\tablecaption{{{caption}}}")
    lines.append(f"\\label{{{label}}}")

    # Header
    lines.append(r"\tablehead{")

    # First header row
    if include_all_col and "All" in df.columns:
        lines.append(
            r"  \colhead{\textbf{Field Code}} & "
            + rf"\multicolumn{{{n_band_cols}}}{{c}}{{\textbf{{Band}}}} & \textbf{{All}}\\"
        )
        lines.append(rf"  \cline{{2-{n_band_cols + 1}}}")
    else:
        lines.append(
            r"  \colhead{\textbf{Field Code}} & "
            + rf"\multicolumn{{{n_band_cols}}}{{c}}{{\textbf{{Band}}}}\\"
        )
        lines.append(rf"  \cline{{2-{n_band_cols + 1}}}")

    # Second header row
    band_headers = " & ".join([f"${b}$" for b in bands])
    if include_all_col and "All" in df.columns:
        lines.append(f"   & {band_headers} & ")
    else:
        lines.append(f"   & {band_headers} ")

    lines.append(r"}")
    lines.append(r"\startdata")

    # Rows (Normal data rows)
    for idx, row in df.iterrows():
        name = str(idx).replace("_", r"\_")
        values = []
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                values.append(r"\nodata")
            else:
                values.append(f"{val:.2f}")

        # Only format a true summary row, not just the final row in the frame.
        if include_all_row and idx == "All":
            lines.append(r"\hline")  # Add horizontal line before the last "All" row
            name = r"\textbf{All}"

        lines.append(f"{name} & " + " & ".join(values) + r" \\")

    lines.append(r"\enddata")
    lines.append(r"\end{deluxetable}")

    return "\n".join(lines)

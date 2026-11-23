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
"""Utilities related to making latex tables for the DP2 paper."""

from __future__ import annotations

__all__ = [
    "make_simple_table",
    "make_per_band_summary_table",
]

import numbers
from collections.abc import Mapping, Sequence
from typing import Any, Optional

import pandas as pd


TABLE_LABEL_PREFIX = "tab"
DP_RELEASE = "DP2"
AUTOGEN_STR = "%%%%% This table is auto generated from data, DO NOT EDIT"


def get_table_label(df_name: str) -> str:
    """
    Generate a standardized LaTeX table label for use in all
    latex tables

    Parameters
    ----------
    df_name : str
        A short identifier for the table / DataFrame.

    Returns
    -------
    label : str
        A LaTeX-safe, all-lowercase label string, e.g., 'tab:dp2_dimensions'.
    """
    # Remove spaces, replace with underscores, lowercase
    df_name_clean = df_name.strip().replace(" ", "_").lower()
    return f"{TABLE_LABEL_PREFIX}:{DP_RELEASE.lower()}_{df_name_clean}"


def make_simple_table(
    df: pd.DataFrame,
    caption: str = None,
    column_spec: Optional[str] = None,
    expand_across_columns: bool = False,
    units: Optional[Mapping[str, str]] = None,
    subheads: Optional[Mapping[str, str]] = None,
) -> str:
    """
    Make a simple AAS `deluxetable` from a pandas DataFrame.
    The number of columns is the number of columns in the pandas DataFrame.

    The header is one row of column names. If ``units`` is given, a second
    header row holds the units, in parentheses, under their columns;
    columns without a unit are blank there.

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
    units : mapping of str to str, optional
        Units keyed by column name (e.g. ``{"R.A.": "deg"}``), written on a
        second header row. If `None`, the header has a single row.
    subheads : mapping of str to str, optional
        Text keyed by column name, written as-is (no parentheses) on the
        second header row, e.g. the second line of a two-line column name.
        A column may not have both a unit and a subhead.

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

    # The label must sit inside the caption block for AASTeX deluxetables.
    table_lines.append(f"\\tablecaption{{{caption}\\label{{{label}}}}}")

    # Table header
    header_cols = (
        " & ".join([f"\\colhead{{\\textbf{{{col}}}}}" for col in df.columns]) + r"\\"
    )
    table_lines.append(r"\tablehead{")
    table_lines.append("  " + header_cols)
    units = dict(units or {})
    subheads = dict(subheads or {})
    if units or subheads:
        unknown = [col for col in {**units, **subheads} if col not in df.columns]
        if unknown:
            raise ValueError(
                f"Units or subheads given for columns not in DataFrame: {unknown}"
            )
        both = sorted(set(units) & set(subheads))
        if both:
            raise ValueError(f"Columns with both a unit and a subhead: {both}")

        def _second_row_cell(col):
            if col in units:
                return f"\\colhead{{({units[col]})}}"
            if col in subheads:
                return f"\\colhead{{\\textbf{{{subheads[col]}}}}}"
            return ""

        table_lines.append("  " + " & ".join(_second_row_cell(c) for c in df.columns))
    table_lines.append(r"}")
    table_lines.append(r"\startdata")

    # Table rows
    for _, row in df.iterrows():
        row_vals = " & ".join(
            [
                str(val).replace("_", r"\_") if i == 0 else str(val)
                for i, val in enumerate(row)
            ]
        )
        table_lines.append(f"{row_vals} \\\\")

    table_lines.append(r"\enddata")
    table_lines.append(f"\\end{{{environment}}}")

    return "\n".join(table_lines)


def _format_cell(value: Any, fmt: Optional[str], empty: str) -> str:
    """Format one table cell.

    Missing values (NaN, None, pd.NA) become ``empty``. Otherwise ``fmt``
    is applied if given; integers are written as-is and other reals with
    two decimals.
    """
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return empty
    if fmt is not None:
        return fmt.format(value)
    if isinstance(value, numbers.Integral):
        return str(value)
    if isinstance(value, numbers.Real):
        return f"{value:.2f}"
    return str(value)


def make_per_band_summary_table(
    df: pd.DataFrame,
    caption: str,
    bands: Optional[Sequence[str]] = None,
    *,
    units: Optional[Mapping[str, str]] = None,
    formats: Optional[Mapping[str, str]] = None,
    total_row: Optional[str] = "All",
    include_all_col: bool = True,
    include_all_row: bool = True,
    index_header: str = "Field Code",
    column_spec: Optional[str] = None,
    expand_across_columns: bool = False,
) -> str:
    """
    Make an AAS `deluxetable` laid out as N single columns, then the band
    columns grouped under a spanning "Band" header, then M single columns.

    N and M are set by the DataFrame column order: every column before the
    first band is a leading column, every column after the last band is a
    trailing column. Either may be zero.

    The header has two rows. The first holds the column names, with a
    single "Band" heading spanning the band columns. The second holds the
    band names (as ``$u$``, ``$g$``, ...) and, if ``units`` is given, the
    units of the single columns; single columns without units are blank
    there. An optional summary row is set off by a horizontal rule and
    written in bold.

    Parameters
    ----------
    df : pd.DataFrame
        One row per table row; the index gives the row names. Columns are
        written in DataFrame order. ``df.attrs["label"]`` sets the LaTeX
        label via `get_table_label`.
    caption : str
        The table caption.
    bands : sequence of str, optional
        Names of the band columns. They must be adjacent in ``df``.
        Defaults to every column except "All", which gives the plain
        per-band summary layout (bands, then an optional "All" column).
    units : mapping of str to str, optional
        Units for non-band columns, written in parentheses in the second
        header row (e.g. ``{"R.A.": "deg"}``).
    formats : mapping of str to str, optional
        Format strings per column (e.g. ``{"R.A.": "{:.1f}"}``). Columns
        without a format use `str` for integers and two decimals for
        other reals.
    total_row : str or None, optional
        Index value of a summary row. It is preceded by ``\\hline``,
        its name is bold, and its missing values are left blank instead
        of ``\\nodata``. Ignored if no row has this index value.
    include_all_col : bool, optional
        If `False`, drop the "All" column if present.
    include_all_row : bool, optional
        If `False`, drop the "All" row if present.
    index_header : str, optional
        Header for the row-name column.
    column_spec : str, optional
        LaTeX column specification. Defaults to ``l`` followed by ``c``
        for every data column.
    expand_across_columns : bool, optional
        If `True`, use ``deluxetable*`` to span both manuscript columns.

    Returns
    -------
    latex_str : str
        The formatted LaTeX deluxetable as a string.

    Notes
    -----
    Missing values are written as ``\\nodata``. Use a nullable integer
    dtype (``"Int64"``) for count columns that can be missing, so the
    remaining values stay integers.
    """
    label = get_table_label(df.attrs["label"])
    environment = "deluxetable*" if expand_across_columns else "deluxetable"
    units = dict(units or {})
    formats = dict(formats or {})

    if not include_all_col and "All" in df.columns:
        df = df.drop(columns=["All"])
    if not include_all_row and "All" in df.index:
        df = df.drop(index="All")

    columns = list(df.columns)
    if bands is None:
        bands = [col for col in columns if col != "All"]
    missing = [b for b in bands if b not in columns]
    if missing:
        raise ValueError(f"Band columns not in DataFrame: {missing}")
    positions = [columns.index(b) for b in bands]
    first = positions[0]
    if positions != list(range(first, first + len(bands))):
        raise ValueError("Band columns must be adjacent and in the given order.")

    if column_spec is None:
        column_spec = "l" + "c" * len(columns)

    lines = [AUTOGEN_STR]
    lines.append(r"\setlength{\tabcolsep}{3pt}")
    lines.append(f"\\begin{{{environment}}}{{{column_spec}}}")
    lines.append(r"\tablewidth{0pt}")
    # The label must sit inside the caption block for AASTeX deluxetables.
    lines.append(f"\\tablecaption{{{caption}\\label{{{label}}}}}")

    # First header row: names, with one spanning "Band" heading.
    head1 = [rf"\multicolumn{{1}}{{l}}{{\textbf{{{index_header}}}}}"]
    head2 = [""]
    for i, col in enumerate(columns):
        if col in bands:
            if i == first:
                head1.append(
                    rf"\multicolumn{{{len(bands)}}}{{c}}{{\textbf{{Band}}}}"
                )
            head2.append(f"${col}$")
        else:
            head1.append(rf"\colhead{{\textbf{{{col}}}}}")
            head2.append(rf"\colhead{{({units[col]})}}" if col in units else "")

    # LaTeX column numbers are 1-based and the index is column 1.
    cline = rf"\cline{{{first + 2}-{first + len(bands) + 1}}}"
    lines.append(r"\tablehead{")
    lines.append("  " + " & ".join(head1) + r" \\")
    lines.append("  " + cline)
    lines.append("  " + " & ".join(head2))
    lines.append(r"}")
    lines.append(r"\startdata")

    for idx in df.index:
        is_total = total_row is not None and idx == total_row
        name = str(idx).replace("_", r"\_")
        if is_total:
            lines.append(r"\hline")
            name = rf"\textbf{{{name}}}"
        empty = "" if is_total else r"\nodata"
        cells = [
            _format_cell(df.at[idx, col], formats.get(col), empty) for col in columns
        ]
        lines.append(f"{name} & " + " & ".join(cells) + r" \\")

    lines.append(r"\enddata")
    lines.append(f"\\end{{{environment}}}")

    return "\n".join(lines)

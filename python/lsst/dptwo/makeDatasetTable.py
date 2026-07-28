from lsst.dptwo.utils.tables import make_simple_table
import pandas as pd

ROWS = [
    ("Deep Coadd", "--", "\\texttt{deep\_coadd}"),
    ("Object", "dp2.Object", "\\texttt{object}"),
    (
        "Isolated Star Stellar Motions",
        "dp2.IsolatedStarStellarMotions",
        "\\texttt{isolated\_star\_stellar\_motions}",
    ),
    ("Object Shear", "dp2.ShearObject", "\\texttt{object\_shear\_all}"),
    ("Source", "dp2.Source", "\\texttt{source}"),
    ("Forced Source", "dp2.ForcedSource", "\\texttt{object\_forced\_source}"),
    (
        "Forced Source at DIA Object",
        "dp2.ForcedSourceOnDiaObject",
        "\\texttt{dia\_object\_forced\_source}",
    ),
    ("DIA Object", "dp2.DiaObject", "\\texttt{dia\_object}"),
    ("DIA Source", "dp2.DiaSource", "\\texttt{dia\_source}"),
    ("Solar System Object", "dp2.SSObject", "\\texttt{ss\_object}"),
    ("MPC Orbit", "dp2.mpc\_orbits", "--"),
    ("Calibration Reference Catalog", "--", "\\texttt{the\_monster\_20250219}"),
    (
        "Survey Property Maps",
        "--",
        "\\texttt{deepCoadd\_<PROPERTY>\_consolidated\_map\_<STATISTIC>}",
    ),
    ("HiPS Maps", "--", "--"),
    ("Skymap", "--", "\\texttt{skyMap}"),
    ("Standard Passbands", "--", "\\texttt{standard\_passband}"),
    ("Object Scarlet Models", "--", "\\texttt{object\_scarlet\_models}"),
    ("Deep Coadd Input Summary", "--", "\\texttt{deep\_coadd\_input\_summary}"),
    ("Visit", "dp2.Visit", "\\texttt{visit\_table}"),
    ("Visit Detector", "dp2.VisitDetector", "\\texttt{visit\_detector\_table}"),
    ("Visit Summary", "--", "\\texttt{visit\_summary}"),
]

CAPTION = """
Summary of dataset types released in EDP2, together with the names by which they are referred to
within the QServ database and the Data Butler.
"""

data = {
    "Dataset Type": [row[0] for row in ROWS],
    "QServe Name": [row[1] for row in ROWS],
    "Butler Name": [row[2] for row in ROWS],
}
df = pd.DataFrame(data)
df.attrs = {"label": "datasetnames"}
table = make_simple_table(df, caption=CAPTION, expand_across_columns=True)

with open("tables/datasetnames.tex", "w") as f:
    f.write(table)

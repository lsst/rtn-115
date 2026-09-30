"""
DP2 delivered image quality (PSF FWHM)

Usage
-----
    python image_quality.py 
"""

import os
 
import numpy as np
import pandas as pd
from statsmodels.distributions.empirical_distribution import ECDF

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
 
from lsst.daf.butler import Butler
import lsst.geom  
 
from lsst.utils.plotting import publication_plots
from lsst.utils.plotting import (
    get_multiband_plot_colors,
    get_multiband_plot_symbols,
    get_multiband_plot_linestyles,
)

# Set fill style ("solid" or "gradient")
FILL_STYLE = "gradient"

# Whether to include labels in the legend or put them on top of the curves
LABELS_IN_LEGENDS = False

# Butler configuration 
DP2_CONFIG = {
    "repo": "dp2",
    "instrument": "LSSTCam",
    "collections": ["LSSTCam/runs/DRP/DP2"],
    "outfile": "./figures/dp2_lsstcam_median_iq.pdf",
}

# Lower cut on PSF FWHM (arcsec) used to exclude non-physical values,
PSF_FWHM_MIN_CUT = 0.0
 
QUANTILES = [25, 50, 75]

# pixel scale of 0.2"/pix
SIGMA_TO_FWHM_ARCSEC = 2.355 * 0.2  

# Set publication style
publication_plots.set_rubin_plotstyle()
bands_dict = publication_plots.get_band_dicts() 
colors = get_multiband_plot_colors()
symbols = get_multiband_plot_symbols()  
linestyles = get_multiband_plot_linestyles()  
bands = colors.keys()

def compute_summary(df, bands):
    """Per-visit, per-band mean/median of seeing and psfFwhm."""
    summary = df.groupby(["visitId", "band"])[["seeing", "psfFwhm"]].agg(["mean", "median"])
    summary.columns = [f"{stat}_{col}" for col, stat in summary.columns]
    summary = summary.reset_index()
    summary = summary.round(2)
    return summary
    return iq_summary.sort_index()

def plot_ecdf(summary):
    """ Plot ECDF to file """    
    plt.figure()
    xmin, xmax = 0.4, 2.7

    median_xs = []
    for band, color in colors.items():
        d = summary.loc[summary["band"] == band, "median_psfFwhm"].dropna()
        if len(d) == 0:
            continue

        ecdf = ECDF(d)
        plt.plot(ecdf.x, ecdf.y, linestyle="-", color=color, label=band)

        median_x = np.median(d)
        median_xs.append(median_x)
        plt.vlines(median_x, ymin=0, ymax=0.5, linestyle=":", color=color)

    # horizontal reference line from the left edge to the rightmost median
    plt.hlines(0.5, xmin=xmin, xmax=max(median_xs), linestyle=":", color="black")


    plt.xlabel("Median PSF FWHM per visit [arcsec]")
    plt.ylabel("Fraction of Visits")
    plt.grid(True)
    plt.xlim(xmin, xmax)
    plt.legend()
    
    outfile = "../figures/dp2_median_per_visit_psf_fwhm_ecdf.pdf"
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    plt.savefig(outfile, bbox_inches='tight', transparent=True)
    plt.close()

def main():

    # DP2 Butler
    cfg = DP2_CONFIG
    butler = Butler(cfg["repo"], 
                    instrument=cfg["instrument"], 
                    collections=cfg["collections"]
                   )


    # Visit detector table
    visit_detector_table = butler.get("visit_detector_table", 
                                      storageClass="DataFrame")
    # Select relevant columns and derive psfFwhm in arcsec.
    df = visit_detector_table[["detectorId", "visitId", "band", "psfSigma", "seeing"]].copy()
    df["psfFwhm"] = df["psfSigma"] * SIGMA_TO_FWHM_ARCSEC

    # Apply non physical cutoff
    min_iq_all = df.loc[df["psfFwhm"].idxmin()]
    print(f"Best delivered IQ before cut:\n{min_iq_all}\n")
 
    df = df[df["psfFwhm"] >= PSF_FWHM_MIN_CUT]

    min_iq_physical = df.loc[df["psfFwhm"].idxmin()]
    print(f"Best delivered image quality after cut:\n{min_iq_physical}\n")
    
    # Compute summary statistics
    iq_summary = compute_summary(df, bands)
    print(iq_summary)

    # Plot 
    plot_ecdf(iq_summary)
 
 
if __name__ == "__main__":
    main()
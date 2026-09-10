"""
Plot the DP2 visit acquisition timeline - all bands, all fields

"""

import numpy as np

from astropy.time import Time

from lsst.daf.butler import Butler
from lsst.utils.plotting import get_multiband_plot_colors, publication_plots

import matplotlib.pyplot as plt


# Set publication style
publication_plots.set_rubin_plotstyle()
colors = get_multiband_plot_colors()
bands = colors.keys()


def main():
    butler = Butler('dp2', collections='dp2')
    registry = butler.registry

    visit_table = butler.get("visit_table", storageClass="DataFrame")

    # Visit accumulation over time - all bands, all fields
    notable_mjds = sorted(set([
        np.floor(np.min(visit_table['expMidptMJD'])),
        60857, 60881, 60973,
        np.floor(np.max(visit_table['expMidptMJD'])),
    ]))
    
    mjd_sorted = np.sort(visit_table['expMidptMJD'])
    n_visits = len(visit_table)
    
    fig, ax = plt.subplots()
    
    ax.plot(mjd_sorted, np.arange(1, n_visits + 1), ls='solid', lw=1, color='black')
    
    ymax = n_visits
    label_y = ymax * 0.97
    
    for mjd in notable_mjds:
        ax.axvline(mjd, ls='dotted', color='grey', lw=0.8)
        date_str = Time(mjd, format='mjd', scale='utc').to_datetime().strftime('%Y-%m-%d')
        ax.text(mjd + 2, label_y, date_str, rotation=90, va='top', ha='left', fontsize=8)
    
    ax.set_xlabel('MJD')
    ax.set_ylabel('Total number of visits')
    #ax.set_title('Cumulative distribution of visit MJDs')
    ax.set_ylim(0, ymax * 1.05)
    fig.tight_layout()
    
    fig.savefig('../figures/dp2_visit_mjd_cumulative.pdf')
    plt.close(fig)

if __name__ == "__main__":
    main()
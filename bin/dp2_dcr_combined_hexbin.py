#!/usr/bin/env python
# coding: utf-8

# # DP2 DCR Combination Hexbin Plot — Reference Code
# 
# *Author: Audrey Budlong*
# 
# After running the `dp2_dcr.py` script twice (once for the ECDFS field and the other for the ecliptic), you can use the following code to take the resulting catalogs and make the combined (side-by-side vertical/horizontal) hexbin plot for the DP2 paper (rtn-115).

# In[1]:


import io
import matplotlib.patheffects as pathEffects
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd

from lsst.utils.plotting import stars_cmap, accent_color
from unittest import mock


# In[2]:


ecdfs_data = pd.read_csv('ecdfs-finalMatchedDf.csv')
ecdfs_data


# In[3]:


ecliptic_data = pd.read_csv('ecliptic-finalMatchedDf.csv')
ecliptic_data


# In[4]:


ecdfs_differential_refraction = ecdfs_data['differentialRefractionBlackbody']
ecdfs_parallel = ecdfs_data['parallel']
ecdfs_perpendicular = ecdfs_data['perpendicular']
ecdfs_magnitude = ecdfs_data['g-i mag']

ecliptic_differential_refraction = ecliptic_data['differentialRefractionBlackbody']
ecliptic_parallel = ecliptic_data['parallel']
ecliptic_perpendicular = ecliptic_data['perpendicular']
ecliptic_magnitude = ecliptic_data['g-i mag']


# In[5]:


def hexbinDp1Paper(differential_refraction, parallel, perpendicular, magnitude, title_label, cmap=stars_cmap(),
                   accentColor=accent_color()):
    """Generate a hexbin plot illustrating the differential chromatic
    refraction (DCR) effect as seen in the input dataset. This visualization is
    intended specifically for the DP1 paper.

    Parameters
    ----------
    differential_refraction : `numpy.array`
        Array of differential refraction values for each source.
    parallel : `list` of `float`
        List of angular separation values between the source and reference
        locations for each object when considering the parallel component of
        the parallactic angle; in radians.
    perpendicular : `list` of `float`
        List of angular separation values between the source and reference
        locations for each object when considering the perpendicular component
        of the parallactic angle; in radians.
    magnitude : `list` of `float`
        'g-i' magnitude difference for each source.
    cmap : `string`, optional
        Plot color map.
    accentColor : `string`, optional
        Accent color used for zero angular offset comparison line in plot.
    """
    fig, ax = plt.subplots(ncols=2, nrows=2, sharey=True)
    plt.subplots_adjust(hspace=0, wspace=0, left=0.12, bottom=0.15)

    xlim = differential_refraction.min(), differential_refraction.max()
    ylim = magnitude.min(), magnitude.max()
    hb = ax[0, 0].hexbin(
        parallel, magnitude, gridsize=50, cmap=cmap, mincnt=1
    )
    ax[0, 0].set(xlim=xlim, ylim=ylim)
    ax[0, 0].set_title("Parallel", fontsize=15)
    ax[0, 0].axvline(x=0, color=accentColor, linestyle="--")
    ax[0, 0].tick_params("x", labelbottom=False)

    ax[0, 0].text(
        0.01, 0.4, r"MagAB (g-i)", rotation="vertical", transform=fig.transFigure
    )
    ax[0, 0].text(0.35, 0.05, r"Angular Offset (arcsec)", transform=fig.transFigure)

    hb = ax[0, 1].hexbin(
        perpendicular,
        magnitude,
        gridsize=50,
        cmap=cmap,
        mincnt=1,
    )
    ax[0, 1].set(xlim=xlim, ylim=ylim)
    ax[0, 1].set_title("Perpendicular", fontsize=15)
    ax[0, 1].axvline(x=0, color=accentColor, linestyle="--")
    ax[0, 1].tick_params("x", labelbottom=False)

    label = "Number of Sources"
    axBbox = ax[0, 1].get_position()
    cax = fig.add_axes([axBbox.x1, axBbox.y0, 0.04, axBbox.y1 - axBbox.y0])
    fig.colorbar(hb, cax=cax)
    text = cax.text(
        0.5,
        0.5,
        label,
        color="k",
        rotation="vertical",
        transform=cax.transAxes,
        ha="center",
        va="center",
        fontsize=10,
    )
    text.set_path_effects(
        [pathEffects.Stroke(linewidth=3, foreground="w"), pathEffects.Normal()]
    )

    hb = ax[1, 0].hexbin(
        parallel,
        magnitude,
        gridsize=50,
        bins="log",
        cmap=cmap,
        mincnt=1,
    )
    ax[1, 0].set(xlim=xlim, ylim=ylim)
    ax[1, 0].axvline(x=0, color=accentColor, linestyle="--")

    hb = ax[1, 1].hexbin(
        perpendicular,
        magnitude,
        gridsize=50,
        bins="log",
        cmap=cmap,
        mincnt=1,
    )
    ax[1, 1].set(xlim=xlim, ylim=ylim)
    ax[1, 1].axvline(x=0, color=accentColor, linestyle="--")
    label2 = "Log(Number of Sources)"
    axBbox = ax[1, 1].get_position()
    cax = fig.add_axes([axBbox.x1, axBbox.y0, 0.04, axBbox.y1 - axBbox.y0])
    fig.colorbar(hb, cax=cax)
    text = cax.text(
        0.5,
        0.5,
        label2,
        color="k",
        rotation="vertical",
        transform=cax.transAxes,
        ha="center",
        va="center",
        fontsize=10,
    )
    text.set_path_effects(
        [pathEffects.Stroke(linewidth=3, foreground="w"), pathEffects.Normal()]
    )

    plt.suptitle(f"{title_label} DCR", fontsize=18, y=1.02)

    plt.show()


# In[6]:


def render(*args, **kwargs):
    """Run hexbinDp1Paper unchanged and return the result as an image array."""
    with mock.patch.object(plt, "show", lambda *a, **k: None):
        hexbinDp1Paper(*args, **kwargs)
    fig = plt.gcf()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return mpimg.imread(buf)

imgA = render(ecdfs_differential_refraction, ecdfs_parallel, ecdfs_perpendicular, ecdfs_magnitude, 'ECDFS',
              cmap=stars_cmap(), accentColor=accent_color())
imgB = render(ecliptic_differential_refraction, ecliptic_parallel, ecliptic_perpendicular, ecliptic_magnitude, 'Ecliptic',
              cmap=stars_cmap(), accentColor=accent_color())

# fig, axs = plt.subplots(1, 2, figsize=(16, 7)) # for horizontal plot
fig, axs = plt.subplots(2, 1, figsize=(7, 7)) # for vertical plot
for a, img in zip(axs, (imgA, imgB)):
    a.imshow(img)
    a.axis("off")
fig.tight_layout()
# plt.savefig("dp2_dcr_horizontal.png")
plt.savefig("dp2_dcr_vertical.png")
plt.show()


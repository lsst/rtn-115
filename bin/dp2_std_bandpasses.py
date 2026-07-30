"""Extract and plot the standard passbands for DP2 from the Butler.

A comparison check is also carried out with DP1 standard bandpasses.

"""

import numpy as np

from lsst.daf.butler import Butler
from lsst.utils.plotting import get_multiband_plot_colors, publication_plots

import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from matplotlib import patheffects as pe
from matplotlib.colors import LinearSegmentedColormap

# Set publication style
publication_plots.set_rubin_plotstyle()
colors = get_multiband_plot_colors()
bands = colors.keys()

# Set fill style ("solid" or "gradient")
fill = "gradient"

# Whether to include labels in the legend or put them on top of the curves
labels_in_legend = False

# Butler configuration per data release.
RELEASES = {
    "dp1": {
        "repo": "dp1",
        "instrument": "LSSTComCam",
        "collections": ["LSSTComCam/DP1"],
        "outfile": "./figures/dp1_lsstcomcam_std_bandpasses.pdf",
    },
    "dp2": {
        "repo": "dp2",
        "instrument": "LSSTCam",
        "collections": ["LSSTCam/runs/DRP/DP2"],
        "outfile": "./figures/dp2_lsstcam_std_bandpasses.pdf",
    },
}


def get_throughputs(butler):
    """Get the throughputs for filters by band, not 'physical_filter'.

    Conceptual passbands, not pieces of glass.
    """
    throughputs = {}
    for band in bands:
        std_bp = butler.get("standard_passband", band=band)
        throughputs[band] = std_bp

    assert len(throughputs) == len(bands)
    return throughputs


def plot_gradient(ax, color, band, wavelengths, tputs, alpha=0.5):
    """Plot the gradient under the curve."""
    # Create a vertical gradient under the curve.
    cmap = LinearSegmentedColormap.from_list("grad", ["white", color])

    # Create the gradient image.
    grad = ax.imshow(
        np.linspace(0, 1, 2000).reshape(-1, 1),
        cmap=cmap,
        norm=mcolors.PowerNorm(gamma=0.64),
        extent=[wavelengths.min(), wavelengths.max(), 0, tputs.max()],
        aspect="auto",
        origin="lower",
        alpha=alpha,
        zorder=1,
    )

    # Clip the gradient image to the area under the curve.
    poly = ax.fill_between(wavelengths, 0, tputs, alpha=0)
    grad.set_clip_path(poly.get_paths()[0], transform=ax.transData)
    poly.remove()


def plot_std_bandpasses(throughputs, outfile):
    """Plot the standard bandpasses and save to outfile."""
    if labels_in_legend:
        fig, ax = plt.subplots()  # i.e. figsize: 6.4, 4.8
    else:
        fig, ax = plt.subplots(figsize=(6.4, 4))

    for i, (band, std_bp) in enumerate(throughputs.items()):
        color = colors[band[0]]
        wavelengths = std_bp["wavelength"]
        tputs = std_bp["throughput"]
        ax.plot(wavelengths, tputs, lw=1.5, color=color, alpha=0.95, zorder=2)

        if fill == "solid":
            ax.fill_between(
                wavelengths, tputs, 0, where=tputs > 0, color=color, alpha=0.3, zorder=1
            )
        elif fill == "gradient":
            plot_gradient(ax, color, band, wavelengths, tputs, alpha=0.5)

        # Place a band label somewhere in the middle of each wavelength range.
        label_wl = np.average(wavelengths, weights=tputs)
        idx = np.argmin(np.abs(wavelengths - label_wl))
        color = colors[band[0]]
        offset = 5.2 if band[0] in ["u", "y"] else 3.0
        ax.text(
            wavelengths[idx],
            tputs[idx] + offset,
            band[0],
            fontsize=13,
            fontweight="normal",
            color=color,
            ha="center",
            va="bottom",
            alpha=1,
            path_effects=[
                pe.Stroke(linewidth=0.7, foreground=color, alpha=0.7),
                pe.Normal(),
            ],
            zorder=3,
        )

    # Add axis labels and adjust limits.
    ax.set_xlabel("Wavelength (nm)", fontsize=13, labelpad=11)
    ax.set_ylabel("Standard Bandpass (%)", fontsize=13, labelpad=9)
    ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=8, prune=None))
    ax.yaxis.set_major_locator(plt.MultipleLocator(10))
    ax.set_xlim(300, 1100)

    if labels_in_legend:
        ax.set_ylim(0, 80)
        ax.legend(
            loc="upper center",
            ncols=6,
            bbox_to_anchor=(0.05, 0.48, 0.88, 0.48),
            mode="expand",
            handlelength=3,
        )
    else:
        ax.set_ylim(0, 70)

    plt.savefig(
        outfile,
        bbox_inches="tight",
        transparent=True,
        format="pdf",
    )
    plt.close(fig)


def assert_bandpasses_differ(throughputs_by_release):
    """Assert that the standard passband for each band differs between releases.

    The standard passbands are periodically recalibrated, so DP1 and DP2
    should not report identical throughput curves for the same band.
    """
    releases = list(throughputs_by_release.keys())
    if len(releases) < 2:
        return

    ref_release, *other_releases = releases
    ref_throughputs = throughputs_by_release[ref_release]

    for other_release in other_releases:
        other_throughputs = throughputs_by_release[other_release]
        for band in ref_throughputs:
            if band not in other_throughputs:
                continue
            ref_bp = ref_throughputs[band]
            other_bp = other_throughputs[band]
            same_shape = ref_bp["throughput"].shape == other_bp["throughput"].shape
            identical = same_shape and np.array_equal(
                ref_bp["throughput"], other_bp["throughput"]
            )
            assert not identical, (
                f"Band '{band}' standard passband is identical between "
                f"{ref_release.upper()} and {other_release.upper()}; expected different curves."
            )


# Line style/color per release for the DP1-vs-DP2 comparison plots.
COMPARISON_STYLE = {
    "dp1": {"color": "blue", "linestyle": ":"},
    "dp2": {"color": "red", "linestyle": "-"},
}


def plot_release_comparison(throughputs_by_release, band, outfile):
    """Plot the standard passband for a single band, overlaid across releases."""
    fig, ax = plt.subplots(figsize=(6.4, 4))

    for release, throughputs in throughputs_by_release.items():
        if band not in throughputs:
            continue
        std_bp = throughputs[band]
        wavelengths = std_bp["wavelength"]
        tputs = std_bp["throughput"]
        style = COMPARISON_STYLE.get(release, {})
        ax.plot(
            wavelengths,
            tputs,
            lw=1.5,
            label=f"{release.upper()} {band}",
            **style,
        )

    ax.set_xlabel("Wavelength (nm)", fontsize=13, labelpad=11)
    ax.set_ylabel("Standard Bandpass (%)", fontsize=13, labelpad=9)
    ax.legend()

    plt.savefig(
        outfile,
        bbox_inches="tight",
        transparent=True,
        format="pdf",
    )
    plt.close(fig)


def plot_release_comparison_grid(throughputs_by_release, outfile, nrows=2, ncols=3):
    """Plot the standard passband for every band, overlaid across releases,
    laid out in a nrows x ncols grid of subplots (one panel per band)."""
    band_list = list(bands)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(ncols * 4.2, nrows * 3), sharex=False
    )
    axes = np.atleast_1d(axes).flatten()

    for ax, band in zip(axes, band_list):
        for release, throughputs in throughputs_by_release.items():
            if band not in throughputs:
                continue
            std_bp = throughputs[band]
            wavelengths = std_bp["wavelength"]
            tputs = std_bp["throughput"]
            style = COMPARISON_STYLE.get(release, {})
            ax.plot(
                wavelengths,
                tputs,
                lw=1.5,
                label=f"{release.upper()} {band}",
                **style,
            )
        ax.set_xlabel("Wavelength (nm)", fontsize=11, labelpad=8)
        ax.set_ylabel("Standard Bandpass (%)", fontsize=11, labelpad=6)
        ax.legend(fontsize=9)

    # Hide any unused panels if there are fewer bands than grid cells.
    for ax in axes[len(band_list) :]:
        ax.set_visible(False)

    fig.tight_layout()
    plt.savefig(
        outfile,
        bbox_inches="tight",
        transparent=True,
        format="pdf",
    )
    plt.close(fig)


if __name__ == "__main__":
    throughputs_by_release = {}
    for release, cfg in RELEASES.items():
        butler = Butler(
            cfg["repo"], instrument=cfg["instrument"], collections=cfg["collections"]
        )
        throughputs_by_release[release] = get_throughputs(butler)

    assert_bandpasses_differ(throughputs_by_release)

    for release, cfg in RELEASES.items():
        if release == "dp2":
            plot_std_bandpasses(throughputs_by_release[release], cfg["outfile"])
            print(f"Saved {release.upper()} standard bandpasses to {cfg['outfile']}")

    # Plot a comparison for interest between all releases per band
    grid_outfile = "./figures/std_bandpass_compare_dp1dp2.pdf"
    # plot_release_comparison_grid(throughputs_by_release, grid_outfile)
    # print(f"Saved DP1 vs DP2 comparison grid to {grid_outfile}")

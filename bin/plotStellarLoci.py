#!/usr/bin/env python
"""
Stellar locus colour-colour plot for Rubin DP1/DP2.
Outputs: stellar_locus.png
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patheffects import withStroke
from astropy.coordinates import SkyCoord
import astropy.units as u
from lsst.rsp import RSPDiscovery
from lsst.utils.plotting import stars_cmap

# --- Query ---
discovery = RSPDiscovery("dp1")
service = discovery.get_tap_client()
assert service is not None

query = """
SELECT TOP 2000000
objectId, coord_ra, coord_dec,
u_psfMag,u_psfMagErr,u_extendedness,u_psfFlux,u_psfFluxErr,u_psfFlux_flag,u_extendedness_flag,
g_psfMag,g_psfMagErr,g_extendedness,g_psfFlux_flag,g_extendedness_flag,
r_psfMag,r_psfMagErr,r_extendedness,r_psfFlux_flag,r_extendedness_flag,
i_psfMag,i_psfMagErr,i_extendedness,i_psfFlux_flag,i_extendedness_flag,
z_psfMag,z_psfMagErr,z_extendedness,z_psfFlux_flag,z_extendedness_flag,
y_psfMag,y_psfMagErr,y_extendedness,y_psfFlux_flag,y_extendedness_flag,
detect_isIsolated
FROM dp2.Object
WHERE (g_psfFlux_flag = 0
    AND g_extendedness = 0
    AND g_extendedness_flag = 0
    AND g_pixelFlags_saturatedCenter = 0
    AND r_psfMag < 22.5
    AND r_psfFlux_flag = 0
    AND r_extendedness = 0
    AND r_extendedness_flag = 0
    AND r_pixelFlags_saturatedCenter = 0
    AND i_psfFlux_flag = 0
    AND i_extendedness = 0
    AND i_sizeExtendedness_flag = 0
    AND i_pixelFlags_saturatedCenter = 0
    AND i_psfFlux / i_psfFluxErr > 200
    AND z_psfFlux_flag = 0
    AND y_psfFlux_flag = 0
    AND z_psfMag < 22.5
    AND y_psfMag < 22.5
    AND detect_isIsolated = 0
)
"""

job = service.submit_job(query)
job.run()
job.wait(phases=['COMPLETED', 'ERROR'])
print('Job phase is', job.phase)
if job.phase == 'ERROR':
    job.raise_if_error()
assert job.phase == 'COMPLETED'
results = job.fetch_result().to_table()

# --- Galactic coordinates ---
coords = SkyCoord(ra=results['coord_ra'], dec=results['coord_dec'], unit='deg', frame='icrs')
results['l'] = coords.galactic.l.deg
results['b'] = coords.galactic.b.deg

# --- Subsample ---
idx = np.random.choice(len(results), size=1000000, replace=False)
subset = results[idx]

gr   = subset['g_psfMag'] - subset['r_psfMag']
ri   = subset['r_psfMag'] - subset['i_psfMag']
iz   = subset['i_psfMag'] - subset['z_psfMag']
ug   = subset['u_psfMag'] - subset['g_psfMag']
usnr = subset['u_psfFlux'] / subset['u_psfFluxErr']
b    = subset['b']

panels = [
    (gr, ri, 'g - r (mag)', 'r - i (mag)', (-0.8, 2.8), (-0.5, 2.5), 400, 10, None),
    (ri, iz, 'r - i (mag)', 'i - z (mag)', (-0.4, 3.2), (-0.2, 1.2), 600, 10, None),
    (ug, gr, 'u - g (mag)', 'g - r (mag)', ( 0.5, 2.8), ( 0.0, 1.5), 400, 20, usnr > 50),
]

# --- Plot ---
fig, axes = plt.subplots(1, 3, figsize=(15, 5), layout='constrained')

for ax, (x, y, xlabel, ylabel, xlim, ylim, bins, threshold, extra_mask) in zip(axes, panels):
    mask = np.isfinite(x) & np.isfinite(y) & (np.abs(b) > 20)
    if extra_mask is not None:
        mask &= extra_mask
    xm, ym = x[mask], y[mask]

    H, xedges, yedges = np.histogram2d(xm, ym, bins=bins)
    H_masked = np.where(H < threshold, np.nan, H)

    im = ax.imshow(
        H_masked.T,
        origin='lower',
        aspect='auto',
        extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
        cmap=stars_cmap(),
        norm=LogNorm(),
        interpolation='nearest',
    )

    ix = np.searchsorted(xedges, xm, side='right').clip(1, len(xedges)-1) - 1
    iy = np.searchsorted(yedges, ym, side='right').clip(1, len(yedges)-1) - 1
    sparse = H[ix, iy] < threshold

    ax.scatter(xm[sparse], ym[sparse], s=1, color='k', alpha=0.5, zorder=2)

    ax.set_xlabel(xlabel, fontsize=16)
    ax.set_ylabel(ylabel, fontsize=16)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.minorticks_on()
    ax.tick_params(axis='both', labelsize=14)

cbar = fig.colorbar(im, ax=axes, label='Points Per Bin', pad=0.01)
cbar.ax.set_ylabel('')
cbar.ax.text(0.6, 0.5, 'Points Per Bin', transform=cbar.ax.transAxes,
             ha='center', va='center', rotation=90, fontsize=14, color='k',
             path_effects=[withStroke(linewidth=3, foreground='white')])
cbar.ax.tick_params(labelsize=14)
cbar.set_ticks([20, 100])
cbar.set_ticklabels(['20', r'$10^2$'])
cbar.ax.minorticks_off()

# --- Save ---
fig.savefig('stellar_locus.png', dpi=300, bbox_inches='tight')
print('Saved stellar_locus.png')

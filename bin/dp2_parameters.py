#!/usr/bin/env python
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
#
# Contact Authors: James Mullaney, Leanne Guy
"""Generate LaTeX parameter files for the RTN-115 DP2 paper.

Writes two output files to the sections/ directory:

- ``parameters_static.tex`` -- values from ``data/static_parameters.yaml``;
  no Butler connection required, suitable for CI.
- ``parameters_data.tex`` -- values derived from the DP2 Butler repository;
  requires a pre-existing Butler and must be committed manually.

Run with ``--static-only``  to produce only ``parameters_static.tex``.
"""

from __future__ import annotations

import argparse
import logging
import os
import warnings
from datetime import datetime
from pathlib import Path
import logging

import numpy as np
import yaml
from astropy import units as u
from haversine import haversine, Unit
from tqdm import tqdm

from lsst.dptwo.utils.parameters import DP2Parameters, addParameter

STATIC_PARAMETERS_FILE = (
    Path(__file__).parent.parent / "data" / "static_parameters.yaml"
)

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def staticParameters(params: DP2Parameters) -> DP2Parameters:
    """Populate ``params`` with values from ``data/static_parameters.yaml``.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    with open(STATIC_PARAMETERS_FILE) as f:
        data = yaml.safe_load(f)
    for section, content in data.items():
        for entry in content["parameters"]:
            params = addParameter(
                params, entry["name"], entry["value"], unit=entry.get("unit")
            )
    return params


def nightsBetween(start_date: str, end_date: str) -> int:
    """Return the number of nights between two ISO-format date strings."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return (end - start).days


def campaignNights(params: DP2Parameters) -> DP2Parameters:
    """Add night counts for the SV and DP2 campaigns if start and end dates are present.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    if "svcampaignstartdate" in params.values and "svcampaignenddate" in params.values:
        params = addParameter(
            params,
            "svcampaignnnights",
            nightsBetween(
                params.values["svcampaignstartdate"], params.values["svcampaignenddate"]
            ),
        )
    if "dptwostartdate" in params.values and "dptwoenddate" in params.values:
        params = addParameter(
            params,
            "dptwonnights",
            nightsBetween(
                params.values["dptwostartdate"], params.values["dptwoenddate"]
            ),
        )
    return params


def observingCampaign(params: DP2Parameters) -> DP2Parameters:
    """Add visit counts, date range, and median exposure times per band.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    visitRecords = registry.queryDimensionRecords("visit")
    params = addParameter(params, "nvisits", len(list(visitRecords)))

    exposureRecords = registry.queryDimensionRecords("exposure")
    params = addParameter(params, "nexposures", len(list(visitRecords)))

    fields = set(
        [
            record.target_name
            for record in exposureRecords
            if record.target_name != "slew_icrs"
        ]
    )
    params = addParameter(
        params,
        "nfields",
        params.values["nfields"] if "nfields" in params.values else str(len(fields)),
    )

    visit_table = butler.get("visit_table")
    firstVisitTime = min(visit_table["obsStart"])
    lastVisitTime = max(visit_table["obsStart"])
    lastVisitNight = lastVisitTime - np.timedelta64(1, "D")
    params = addParameter(
        params, "dptwostartdate", np.datetime_as_string(firstVisitTime, unit="D")
    )
    params = addParameter(
        params, "dptwoenddate", np.datetime_as_string(lastVisitNight, unit="D")
    )

    u_selection = visit_table["band"] == "u"
    params = addParameter(
        params,
        "exposuretime",
        f"{np.median(visit_table['expTime'][~u_selection]):.0f}",
        unit="s",
    )
    params = addParameter(
        params,
        "exposuretimeuband",
        f"{np.median(visit_table['expTime'][u_selection]):.0f}",
        unit="s",
    )
    return params


def observingQuality(params: DP2Parameters) -> DP2Parameters:
    """Add PSF FWHM statistics (best, median overall, median per band).

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding observing quality parameters...")

    visit_detector_table = butler.get("visit_detector_table")
    visit_detector_table["psfFwhm"] = visit_detector_table["psfSigma"] * 2.355 * 0.2

    minSeeing = np.min(
        visit_detector_table["psfFwhm"][visit_detector_table["nPsfStar"] > 100]
    )
    params = addParameter(
        params, "bestimagequality", minSeeing.item(), unit="\\arcsec", sig=2
    )

    medSeeing = np.median(
        visit_detector_table["psfFwhm"][visit_detector_table["nPsfStar"] > 100]
    )
    params = addParameter(
        params, "medianimagequalityallbands", medSeeing.item(), unit="\\arcsec", sig=3
    )

    df = visit_detector_table[visit_detector_table["nPsfStar"] > 100].to_pandas()
    bandSeeing = df.groupby("band")["psfFwhm"].median()
    bandSeeing = bandSeeing.reindex(bands)
    for band in bandSeeing.index:
        params = addParameter(
            params,
            f"{band}medianimagequality",
            float(bandSeeing[band]),
            unit="\\arcsec",
            sig=3,
        )
    return params


def imageStats(params: DP2Parameters, imageId: tuple) -> DP2Parameters:
    """Add count, file size, pixel dimensions, plate scale, and FOV for one dataset type.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.
    imageId : `tuple`
        ``(dataset_type, data_id)`` pair identifying the image to characterise.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    imageType = imageId[0]
    imageDataId = imageId[1]
    imageName = imageType.replace("_", "")

    refs = list(registry.queryDatasets(imageType))
    params = addParameter(params, f"n{imageName}s", len(list(refs)))

    # ref = list(registry.queryDatasets(imageType, dataId=imageDataId))[0]
    # filepath = butler.getURI(ref)
    
    # Filesize not currently working:
    #roughFileSize = round(os.path.getsize(filepath.path) / 1e6, 2)
    #params = addParameter(params, f"{imageName}hdd", f"{roughFileSize:.0f}", unit="MB")

    # image = butler.get(ref)
    # params = addParameter(params, f"n{imageName}pixx", image.bbox.shape.x)
    # params = addParameter(params, f"n{imageName}pixy", image.bbox.shape.y)

    # platescale = image.getWcs().getPixelScale().asArcseconds()
    # params = addParameter(
    #     params, f"{imageName}platescale", f"{platescale:.1f}", unit="\\arcsec per pixel"
    # )

    # fovx = image.getDimensions().x * image.getWcs().getPixelScale().asDegrees()
    # fovy = image.getDimensions().y * image.getWcs().getPixelScale().asDegrees()
    # params = addParameter(params, f"{imageName}fovx", f"{fovx:.2f}", unit="\\degree")
    # params = addParameter(params, f"{imageName}fovy", f"{fovy:.2f}", unit="\\degree")
    # area = fovx * fovy
    # params = addParameter(
    #     params, f"{imageName}fov", f"{area:.3f}", unit="deg$^{\\rm 2}$"
    # )
    return params


def imageDatasets(params: DP2Parameters) -> DP2Parameters:
    """Add image stats for raw, visit_image, deep_coadd, template_coadd, and difference_image.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding image dataset stats...")

    datasets = {
        "deep_coadd": {
            "band": "i",
            "skymap": "lsst_cells_v2",
            "tract": 9813,
            "patch": 50,
        },
        "template_coadd": {
            "band": "i",
            "skymap": "lsst_cells_v2",
            "tract": 9813,
            "patch": 50,
        },
    }
    for dataset in datasets.items():
        params = imageStats(params, dataset)

    # params = addParameter(
    #     params,
    #     "ndeepcoaddpixtotal",
    #     params.values["ndeepcoaddpixx"] * params.values["ndeepcoaddpixy"] / 1e6,
    #     sig=3,
    #     unit="million",
    # )
    return params


def nRaws(params: DP2Parameters) -> DP2Parameters:
    """Add the number of exposures, raw images, and active detectors.

    Note: nraws and nexposures will populated for DP2. They are not
    included in EPD2.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding number of exposures and raws...")
    # params = addParameter(params, "nexposures")

    visit_detector_table = butler.get("visit_detector_table")
    params = addParameter(params, "nactivedetectors", len(set(visit_detector_table["detector"])))
    # params = addParameter(params, "nraws", )
    return params


def skymapData(params: DP2Parameters) -> DP2Parameters:
    """Add tract/patch geometry and area parameters from the skymap.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding skymap parameters...")

    params = addParameter(params, "ntracts", len(skymap))

    coveredTractIds = {
        dataId["tract"] for dataId in registry.queryDataIds(["tract"], datasets="object")
    }
    params = addParameter(params, "ncoveredtracts", len(coveredTractIds))

    tract = skymap.generateTract(9000)
    verticesInDegrees = [
        (vertex[0].asDegrees() % 360 - 180, vertex[1].asDegrees())
        for vertex in tract.getVertexList()
    ]
    tractArea = haversine(
        verticesInDegrees[0][::-1], verticesInDegrees[1][::-1], unit=Unit.DEGREES
    ) * haversine(
        verticesInDegrees[1][::-1], verticesInDegrees[2][::-1], unit=Unit.DEGREES
    )
    params = addParameter(
        params, "tractarea", f"{tractArea:.1f}", unit="deg$^{\\rm 2}$"
    )

    tractOverlap = skymap.config.tractOverlap * 60.0
    params = addParameter(
        params, "tractoverlap", f"{tractOverlap:.1f}", unit="\\arcmin"
    )

    numXPatches, numYPatches = skymap[0].getNumPatches()
    numPatches = numXPatches * numYPatches
    params = addParameter(params, "npatchx", numXPatches)
    params = addParameter(params, "npatchy", numYPatches)
    params = addParameter(params, "npatch", numPatches)

    patchArea = tractArea / numPatches
    params = addParameter(
        params, "patchareanooverlap", f"{patchArea:.3f}", unit="deg$^{\\rm 2}$"
    )

    refs = list(butler.query_datasets("deep_coadd",
        where="tract=9813 AND patch=50 AND band='g' AND skymap='lsst_cells_v2'")
    )


    coadd = butler.get(refs[0])
    bbox = coadd.bbox
    sky_projection = coadd.sky_projection

    corner_00 = sky_projection.pixel_to_sky(x=bbox.x.min, y=bbox.y.min)
    corner_01 = sky_projection.pixel_to_sky(x=bbox.x.min+1, y=bbox.y.min)
    corner_x1 = sky_projection.pixel_to_sky(x=bbox.x.stop, y=bbox.y.min)
    corner_y1 = sky_projection.pixel_to_sky(x=bbox.x.min, y=bbox.y.stop)

    fovx = corner_00.separation(corner_x1).degree
    fovy = corner_00.separation(corner_y1).degree
    params = addParameter(
        params, "patcharea", f"{fovx.item() * fovy.item():.3f}", unit="deg$^{\\rm 2}$"
    )

    npatchpixx = bbox.x.size
    npatchpixy = bbox.y.size
    coaddpixsize = corner_00.separation(corner_01).arcsec
    params = addParameter(params, "npatchpixx", npatchpixx)
    params = addParameter(params, "npatchpixy", npatchpixy)
    params = addParameter(params, "coaddpixsize", coaddpixsize.item(), unit="\\arcsec", sig=2)

    wcs = tract.getWcs()
    patchInfo = tract.getPatchInfo((5, 5))
    patchOverlap = (
        patchInfo.getOuterBBox().getWidth() - patchInfo.getInnerBBox().getWidth()
    ) * wcs.getPixelScale().asArcseconds()
    params = addParameter(
        params, "patchoverlap", f"{patchOverlap:.1f}", unit="\\arcsec"
    )

    numXCells, numYCells = patchInfo.getNumCells()
    params = addParameter(params, "ncellx", numXCells)
    params = addParameter(params, "ncelly", numYCells)

    numCellsInPatchBorder = skymap.config.tractBuilder["cells"].numCellsInPatchBorder
    params = addParameter(params, "ncellpatchoverlap", numCellsInPatchBorder, unit="cell")
    return params


def coaddSelectionCriteria(params: DP2Parameters) -> DP2Parameters:
    """Add the maximum PSF FWHM threshold used to select visits for deep coadds.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding coadd selection criteria...")
    refs = list(registry.queryDatasets("selectDeepCoaddVisits_config"))
    config = butler.get(refs[0])
    return addParameter(
        params, "deepcoaddselectionfwhm", config.maxPsfFwhm, sig=2, unit="\\arcsec"
    )


def surveyPropertyMaps(params: DP2Parameters) -> DP2Parameters:
    """Add the count of HealSparse survey property maps.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding numbers of survey maps...")
    allSurveyPropMaps = []
    for datasetType in butler.registry.queryDatasetTypes():
        if registry.queryDatasets(datasetType).any(execute=False, exact=False):
            if datasetType.storageClass.name == "HealSparseMap":
                allSurveyPropMaps.append(datasetType.name)
    return addParameter(params, "nsurveypropertymaps", len(allSurveyPropMaps))


def nCatalogDatasets(params: DP2Parameters) -> DP2Parameters:
    """Add the number of datasets (as words) for each catalog type.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding catalog dataset stats...")
    from lsst.dptwo.utils.formatting import num2word

    for name, dataset in [
        ("nsourcecatalogs", "source"),
        ("nobjectcatalogs", "object"),
        ("ndiaobjectcatalogs", "dia_object"),
        ("ndiasourcecatalogs", "dia_source"),
        ("nsolarsystemsourcecatalogs", "ss_source"),
        ("nvisitsummarytables", "visit_table"),
        ("nvisitdetectorsummarytables", "visit_detector_table"),
        ("nobjectforcedcatalogs", "object_forced_source"),
        ("ndiaobjectforcedcatalogs", "dia_object_forced_source"),
    ]:
        refs = list(registry.queryDatasets(dataset))
        params = addParameter(params, name, num2word(len(refs)).lower())
    return params


def tableLengths(params: DP2Parameters) -> DP2Parameters:
    """Add row counts for visit summary, visit-detector summary, and SS catalog tables.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding table lengths...")
    refs = list(registry.queryDatasets("visit_table"))
    table = butler.get(refs[0])
    params = addParameter(params, "nvisitsummaries", len(table))

    refs = list(registry.queryDatasets("visit_detector_table"))
    table = butler.get(refs[0])
    params = addParameter(params, "nvisitdetectorsummaries", len(table))

    refs = list(registry.queryDatasets("ss_source"))
    catalog = butler.get(refs[0])
    params = addParameter(params, "nsolarsystemsources", len(catalog))

    refs = list(registry.queryDatasets("ss_object"))
    catalog = butler.get(refs[0])
    params = addParameter(params, "nsolarsystemobjects", len(catalog))
    return params


def misc(params: DP2Parameters) -> DP2Parameters:
    """Add derived parameters computed from previously stored values.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate; must already contain ``nraws`` and
        ``nvisitimages``.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding misc data...")
    params = addParameter(
        params, "nsfpfails", params.values["nraws"] - params.values["nvisitimages"]
    )
    return params


def totalDP2Area(params: DP2Parameters) -> DP2Parameters:
    """Add total survey area by counting non-NO_DATA pixels.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.

    Notes
    -----
    Slow -- iterates all r-band coadds.
    """
    log.info("Adding total DP2 area. This is a slow step...")
    coaddRefs = list(registry.queryDatasets("deep_coadd", where="band = 'r'"))
    pixcount = 0
    for coaddRef in tqdm(coaddRefs):
        im = butler.get("deep_coadd.mask", dataId=coaddRef.dataId)
        pixcount += im.array.size - np.sum(
            (im.array & im.getPlaneBitMask("NO_DATA")) > 0
        )
    area = pixcount * ((0.2 / 3600) ** 2)
    params = addParameter(
        params, "totalarea", f"{np.round(area):.0f}", unit="deg$^{\\rm 2}$"
    )
    return params


def _nEntries(tableName: str) -> int:
    """Returns the number of entries in a TAP table.

    Parameters
    ----------
    tableName : `str`
        The name of the table to return the number of entries of.

    Returns
    --------
    result : `int`
        The number of entries in table `tableName`.

    Notes
    -----
    Uses the TAP service. Throws a warning and returns NaN if the
    TAP service is unavailable.
    """
    if not dp2_available:
        warnings.warn(f"TAP service unavailable, skipping query of {tableName}.")
        return np.nan

    query = f"SELECT COUNT(*) AS nEntries FROM {tableName}"
    job = service.submit_job(query)
    job.run()
    job.wait(phases=['COMPLETED', 'ERROR'])
    results = job.fetch_result()

    return results['nEntries'][0]

def nObjects(params: DP2Parameters) -> DP2Parameters:
    """Add total object count (in millions) across all object catalog patches.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding total number of objects...")
    nObjects = _nEntries('dp2.Object')
    params = addParameter(params, "nobjects", nObjects / 1e6, sig=2, unit="million")

    return params


def nSources(params: DP2Parameters) -> DP2Parameters:
    """Add total source count (in millions) across all source catalog patches.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding total number of sources...")
    nSources = _nEntries('dp2.Source')
    params = addParameter(params, "nsources", nSources / 1e9, sig=2, unit="billion")

    return params


def nDiaObjects(params: DP2Parameters) -> DP2Parameters:
    """Add total DIAObject count (in millions) across all dia_object catalog patches.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding total number of diaObjects...")
    nDiaObjects = _nEntries('dp2.DiaObject')
    params = addParameter(
        params, "ndiaobjects", nDiaObjects / 1e6, sig=2, unit="million"
    )
    return params


def nDiaSources(params: DP2Parameters) -> DP2Parameters:
    """Add total DIASource count (in millions) across all dia_source catalog patches.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding total number of diaSources...")
    nDiaSources = _nEntries('dp2.DiaSource')
    params = addParameter(
        params, "ndiasources", nDiaSources / 1e9, sig=2, unit="billion"
    )
    return params


def nForced(params: DP2Parameters) -> DP2Parameters:
    """Add forced-source and unique forced-object counts from object_forced_source.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding total number of forced sources")
    nForcedSources = _nEntries('dp2.ForcedSource')
    params = addParameter(
        params, "nforcedsources", nForcedSources / 1e9, sig=2, unit="billion"
    )
    return params

def nIsolatedStars(params: DP2Parameters) -> DP2Parameters:
    """Add forced-source and unique forced-object counts from object_forced_source.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding total number of isolated stars")
    nEntries = _nEntries('dp2.IsolatedStarStellarMotions')
    params = addParameter(
        params, "nisolatedstars", nEntries / 1e6, sig=2, unit="million"
    )
    return params

def nShearObjects(params: DP2Parameters) -> DP2Parameters:
    """Add forced-source and unique forced-object counts from object_forced_source.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding total number of shear objects")
    nEntries = _nEntries('dp2.ShearObject')
    params = addParameter(
        params, "nshearobjects", nEntries / 1e9, sig=2, unit="billion"
    )
    return params



def nDiaForced(params: DP2Parameters) -> DP2Parameters:
    """Add forced-source and unique forced-object counts from dia_object_forced_source.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding total number of DIA forced sources")
    nForcedSourcesOnDIA = _nEntries('dp2.ForcedSourceOnDiaObject')
    params = addParameter(
        params, "ndiaforcedsources", nForcedSourcesOnDIA / 1e9, sig=2, unit="billion"
    )
    return params


def nSSObjects(params: DP2Parameters) -> DP2Parameters:
    """Add total solar system object count from ss_object.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding total number of SS objects...")
    runningTotalObj = 0
    for ref in list(registry.queryDatasets("ss_object")):
        catalog = butler.get(ref, parameters={"columns": "ssObjectId"})
        runningTotalObj += len(catalog)
    params = addParameter(params, "nssobjects", runningTotalObj, sig=3)
    return params


def nStarsGals(params: DP2Parameters) -> DP2Parameters:
    """Add the count of extended (galaxy) objects based on per-band extendedness > 0.5.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding total number of stars and galaxies...")
    nGals = 0
    columns = [band + "_extendedness" for band in ["u", "g", "r", "i", "z", "y"]]
    for ref in tqdm(list(registry.queryDatasets("object"))):
        objectTable = butler.get(ref, parameters={"columns": columns})
        if len(objectTable) > 0:
            galSelection = (
                (
                    (objectTable["u_extendedness"] > 0.5)
                    & ~objectTable["u_extendedness"].mask
                )
                | (
                    (objectTable["g_extendedness"] > 0.5)
                    & ~objectTable["g_extendedness"].mask
                )
                | (
                    (objectTable["r_extendedness"] > 0.5)
                    & ~objectTable["r_extendedness"].mask
                )
                | (
                    (objectTable["i_extendedness"] > 0.5)
                    & ~objectTable["i_extendedness"].mask
                )
                | (
                    (objectTable["z_extendedness"] > 0.5)
                    & ~objectTable["z_extendedness"].mask
                )
                | (
                    (objectTable["y_extendedness"] > 0.5)
                    & ~objectTable["y_extendedness"].mask
                )
            )
            nGals += np.sum(galSelection.data)
    params = addParameter(
        params, "nextendedobjects", nGals / 1e6, sig=2, unit="million"
    )
    return params


def nDeepCoaddInputImages(params: DP2Parameters) -> DP2Parameters:
    """Add the number of unique visit-detector pairs contributing to deep coadds.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding number of deep coadd input images...")
    refs = list(registry.queryDatasets("deep_coadd_input_map"))
    visitDetectorPairs = set()
    for ref in tqdm(refs):
        inputMap = butler.get(ref)
        keyRoots = [
            key[:5]
            for key in inputMap.metadata
            if key.startswith("B") & key.endswith("CCD")
        ]
        visitDetectorPairs.update(
            {
                (inputMap.metadata[keyRoot + "VIS"], inputMap.metadata[keyRoot + "CCD"])
                for keyRoot in keyRoots
            }
        )
    params = addParameter(params, "ndeepcoaddvisitimages", len(visitDetectorPairs))
    return params


def nTemplateCoaddInputImages(params: DP2Parameters) -> DP2Parameters:
    """Add the number of visit images used as template coadd inputs.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding number of template coadd input images...")
    refs = list(registry.queryDatasets("template_coadd_visit_selection"))
    visits = set()
    for ref in tqdm(refs, desc="Part 1 of 2"):
        inputVisits = butler.get(ref)
        visits.update({key for (key, value) in inputVisits.items() if value})
    nTemplateCoaddInputs = 0
    for visit in tqdm(visits, desc="Part 2 of 2"):
        nTemplateCoaddInputs += len(
            list(
                registry.queryDatasets(
                    "visit_image", visit=visit, instrument="LSSTComCam"
                )
            )
        )
    params = addParameter(params, "ntemplatecoaddvisitimages", nTemplateCoaddInputs)
    return params


def depthEcdfs(params: DP2Parameters) -> DP2Parameters:
    """Add 5-sigma point-source depth per band for the ECDFS field.

    Parameters
    ----------
    params : `DP2Parameters`
        Parameter store to populate.

    Returns
    -------
    params : `DP2Parameters`
        Updated parameter store.
    """
    log.info("Adding ECDFS depths...")
    tracts = []
    with butler.query() as base_query:
        processed_visit_query = base_query.join_dataset_search("visit_summary").where(
            "visit.target_name = 'ECDFS'"
        )
        for row in processed_visit_query.general(["tract"]):
            tracts.append(row["tract"])

    for band in tqdm(bands):
        mags = np.array([])
        for tract in tracts:
            columns = [
                f"{band}_psfFlux",
                f"{band}_psfFluxErr",
                f"{band}_psfFlux_flag",
                f"{band}_extendedness",
            ]
            table = butler.get(
                "object",
                tract=tract,
                skymap="lsst_cells_v1",
                parameters={"columns": columns},
            )
            sn = table[f"{band}_psfFlux"] / table[f"{band}_psfFluxErr"]
            if len(table) > 0:
                starSelection = (
                    (~table[f"{band}_psfFlux_flag"])
                    & (table[f"{band}_extendedness"] <= 0.5)
                    & ~table[f"{band}_extendedness"].mask
                    & (sn > 4.9)
                    & (sn < 5.1)
                )
                flux = table[starSelection][f"{band}_psfFlux"] * u.nJy
                mags = np.append(mags, flux.to_value(u.ABmag))
        params = addParameter(params, f"{band}depth", np.median(mags), sig=4)
    return params


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write output files (default: current directory)",
    )
    parser.add_argument(
        "--static-only",
        action="store_true",
        help="Write only static parameters (no Butler connection required)",
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)

    # The static parameters from yaml
    static_params = DP2Parameters()
    static_params = staticParameters(static_params)
    static_params = campaignNights(static_params)
    static_path = static_params.write(output_dir / "parameters_static.tex")

    # Update to get from lsst.utils
    if not args.static_only:
        from lsst.daf.butler import Butler
        from lsst.rsp import get_tap_service
        from pyvo.dal.exceptions import DALServiceError

        service = get_tap_service("tap")
        try:
            query = "SELECT * FROM tap_schema.tables WHERE tap_schema.tables.schema_name = 'dp2'"
            dp2_available = len(service.search(query)) > 0
        except DALServiceError as e:
            warnings.warn("TAP service unavailable, skipping TAP-dependent steps.")
            dp2_available = False

        bands = ["u", "g", "r", "i", "z", "y"]

        instrument = "LSSTCam"
        skymapName = "lsst_cells_v2"

        butler = Butler(
            "dp2",
            instrument=instrument,
            collections=["LSSTCam/runs/DRP/DP2", "skymaps"],
            skymap=skymapName,
        )
        registry = butler.registry
        skymap = butler.get("skyMap", skymap=skymapName)

        data_params = DP2Parameters()
        # data_params = observingCampaign(data_params)
        # data_params = observingQuality(data_params)
        data_params = imageDatasets(data_params)
        data_params = skymapData(data_params)
        data_params = nRaws(data_params)
        # data_params = coaddSelectionCriteria(data_params)
        # data_params = surveyPropertyMaps(data_params)
        # data_params = nCatalogDatasets(data_params)
        # data_params = tableLengths(data_params)
        # data_params = misc(data_params)

        data_params = nObjects(data_params)
        data_params = nSources(data_params)
        data_params = nDiaObjects(data_params)
        data_params = nDiaSources(data_params)
        data_params = nForced(data_params)
        data_params = nDiaForced(data_params)
        data_params = nIsolatedStars(data_params)
        data_params = nShearObjects(data_params)
        
        # data_params = nSSObjects(data_params)
        # data_params = nStarsGals(data_params)
        # data_params = nDeepCoaddInputImages(data_params)
        # data_params = nTemplateCoaddInputImages(data_params)
        # data_params = depthEcdfs(data_params)

        # Calculating area is slow; include in manual parameters if needed.
        # Needs DP2 update
        # data_params = totalDP2Area(data_params)

        data_path = data_params.write(output_dir / "parameters_data.tex")

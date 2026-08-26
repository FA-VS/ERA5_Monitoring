"""Module to manage ERA5 data downloads.

Contains global variables to set defaults for ERA5 downloads.
Functions:
    era5_request_fullyear
    fetch_recent_year
    fetch_recent
    build_download_argparse
"""


import os
import glob
import argparse
from datetime import date, timedelta

import cdsapi
c = cdsapi.Client()

# GLOBAL VARIABLES

# Western Europe box [N, W, S, E]. Adjust as needed
AREAS = {
        "world": [90,-180,-90,180], #ERA5 default
        "western_europe": [60, -10, 40, 20]
        }
AREA_LABELS = AREAS.keys()

GRIDS = {
        "0.25deg" : [0.25, 0.25], #ERA5 default
        "1deg": [1.0, 1.0]
        }
GRID_LABELS = GRIDS.keys()

PERIODS = {
    "1950s": list(range(1950, 1960)),
    "1960s": list(range(1960, 1970)),
    "1970s": list(range(1970, 1980)),
    "1980s": list(range(1980, 1990)),
    "1990s": list(range(1990, 2000)),
    "2000s": list(range(2000, 2010)),
    "2010s": list(range(2010, 2020)),
    "eval":  list(range(2020, 2025)),
}
PERIOD_LABELS = PERIODS.keys()
PERIOD_LABELS_INREPO = ["1950s", "1980s", "2000s"] # These are expected to be found locally in the repo

TIMESTAMPLISTS = {
        "1h": [f"{h:02d}:00" for h in range(24)], #ERA5 default
        "6h": ["00:00", "06:00", "12:00", "18:00"]
        }
TIMESTAMP_LABELS = TIMESTAMPLISTS.keys()

# ERA5 single-level dataset. MSLP + 2m temperature.
# Note: 1950-1978 lives in the "preliminary back extension"; from 1979 on
# it's the main ERA5 stream. The CDS now serves both under the same
# dataset name, but double-check the current dataset id on the CDS docs.
DATASET = "reanalysis-era5-single-levels"
VARIABLES = ["mean_sea_level_pressure", "2m_temperature"]


# FUNCTIONS

def era5_request_fullyear(year: int, area_label: str, grid_label: str, timestamp_label: str) -> dict[str,str|list[str]]:
    """Return dict to be used in cdsapi.Client().retrieve()."""

    return {
        "product_type": "reanalysis",
        "variable": VARIABLES,
        "year": str(year),
        "month": [f"{m:02d}" for m in range(1, 13)],
        "day": [f"{d:02d}" for d in range(1, 32)],
        # Download just a few times/day, to be averaged daily later.
        "time": TIMESTAMPLISTS[timestamp_label],
        "area": AREAS[area_label],
        "format": "netcdf",
        # Optional: coarsen to save space/time. Native is 0.25.
        "grid": GRIDS[grid_label],
    }

def fetch_recent_year(
        year: int = 2025,
        out_dir: str ="data/recent",
        area_label: str ="western_europe",
        grid_label: str ="1deg",
        timestamp_label: str ="6h"
        ) -> list[str]:
    """Download one full year of ERA5 data

    Args:
        year: full year for which we want to download data
        out_dir: local folder where the files should be downloaded
        area_label: geographic region for which to download data
        grid_label: geographic precision of data to download
        timestamp_label: time resolution of data to download

    Returns:
        List of paths of files downloaded
    """

    os.makedirs(out_dir, exist_ok=True)

    target = f"{out_dir}/recent_{year}.nc"

    cdsapi.Client().retrieve(
        DATASET,
        era5_request_fullyear(year, area_label, grid_label, timestamp_label),
        target)

    return [target]

def fetch_recent(
        months: int =12,
        out_dir: str ="data/recent",
        area_label: str ="western_europe",
        grid_label: str ="1deg",
        timestamp_label: str ="6h"
        ) -> list[str]:
    """Download last n months of ERA5 data

    Args:
        months: number of months of data to download
        out_dir: local folder where the files should be downloaded
        area_label: geographic region for which to download data
        grid_label: geographic precision of data to download
        timestamp_label: time resolution of data to download

    Returns:
        List of paths of files downloaded
    """

    #TODO: This needs A LOT of work, and is thus currently unused
    # - Check what is already present to avoid redownloads (requires new naming convention)
    # - Make as few calls to CDS as possible to download what is missing
    # - Prune old files from data/recent

    os.makedirs(out_dir, exist_ok=True)

    end = date.today() - timedelta(days=6)   # ERA5T latency guard
    # Build the list of (year, month) pairs for the last `months` months,
    # walking backwards from the cutoff month.
    year_month = []
    y, m = end.year, end.month
    for _ in range(months):
        year_month.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    year_month.reverse()   # chronological order

    client = cdsapi.Client()
    for i, (year, month) in enumerate(year_month):
        target = f"{out_dir}/era5_{year}{month:02d}.nc"

        if i == len(year_month) - 1:
            # If it's the most recent (i.e. current) month, fetch data (again), since it has new days.
            # Only request up to the cutoff day so we don't ask CDS for days that don't exist yet.
            days = [f"{d:02d}" for d in range(1, end.day + 1)]
        elif not os.path.exists(target):
            # File is missing, fetch it
            days = [f"{d:02d}" for d in range(1, 32)]   # CDS ignores invalid days
        else:
            # File exists locally and is not most recent, don't download it again
            continue

        request = era5_request_fullyear(year, area_label, grid_label, timestamp_label)
        request["month"] = f"{month:02d}"
        request["day"] = days # Cartesian product between years, months, days - must be careful here
        client.retrieve(
            DATASET,
            request,
            target)

    return sorted(glob.glob(f"{out_dir}/*.nc"))


def build_download_argparse() -> argparse.ArgumentParser:
    """Build CLI parser to download ERA5 data to compute model drift."""

    # TODO: Clean this up and/or factorize (a bit too closely linked to monitor.py at the moment)
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-glob", default="data/reference/*.nc")
    parser.add_argument("--reference-years", default="1950s", choices = PERIOD_LABELS_INREPO)
    #parser.add_argument("--recent-months", type=int, default=3) #In practice, should be 12 months (unless we add code to account for seasonality)
    parser.add_argument("--recent-year", type=int, default=2025)
    parser.add_argument("--area-label", default="western_europe", choices = AREA_LABELS)
    parser.add_argument("--grid-label", default="1deg", choices = GRID_LABELS)
    parser.add_argument("--timestamp-label", default="6h", choices = TIMESTAMP_LABELS)
    parser.add_argument("--drift-threshold", type=float, default=1.0) #This value is a placeholder
    parser.add_argument("--fetch", action="store_true")

    return parser

"""Integration test: download one year of ERA5 data from CDS."""

from pathlib import Path

import pytest
import pytest_check as check
import xarray as xr

from modules.download_era5 import fetch_recent_year

pytestmark = pytest.mark.integration


def test_fetch_recent_year(tmp_path):
    paths = fetch_recent_year(
        year=2020,
        out_dir=str(tmp_path),
        area_label="western_europe",
        grid_label="1deg",
        timestamp_label="6h",
    )
    print("downloaded paths:", paths)

    check.equal(len(paths), 1)
    if not paths:
        return

    path = Path(paths[0])
    check.is_true(path.exists(), f"{path} does not exist")
    check.greater(path.stat().st_size, 0, f"{path} is empty")

    with xr.open_dataset(path, engine="h5netcdf") as ds:
        print("variables:", list(ds.data_vars))
        print("valid_time size:", ds.sizes.get("valid_time"))
        check.is_in("msl", ds.data_vars)
        check.is_in("t2m", ds.data_vars)
        check.greater(ds.sizes.get("valid_time", 0), 0)

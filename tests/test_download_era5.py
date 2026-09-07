"""Integration test: download one year of ERA5 data from CDS."""

from pathlib import Path

import pytest
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

    assert len(paths) == 1
    path = Path(paths[0])
    assert path.exists()
    assert path.stat().st_size > 0

    with xr.open_dataset(path, engine="h5netcdf") as ds:
        assert "msl" in ds
        assert "t2m" in ds
        assert ds.sizes["valid_time"] > 0

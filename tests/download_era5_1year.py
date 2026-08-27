"""Download one year of ERA5 data (Western Europe, low resolution). """

import os

from modules.download_era5 import fetch_recent_year

fetch_recent_year(
        year = 2020,
        out_dir = os.getcwd(),
        area_label = "western_europe",
        grid_label = "1deg",
        timestamp_label = "6h"
        )


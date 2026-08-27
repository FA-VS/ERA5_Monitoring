"""Download one year of ERA5 data (Western Europe, low resolution). """

import cdsapi
c = cdsapi.Client()

from modules.download_era5 import era5_request_fullyear, DATASET, PERIODS

area_label = "western_europe"
grid_label = "1deg"
timestamp_label = "6h"

for period_label, years in PERIODS.items():
    for y in years:
        target = f"era5_{area_label}_{grid_label}_{timestamp_label}_{period_label}_{y}.nc"
        print("requesting", target)
        c.retrieve(DATASET, era5_request_fullyear(y, area_label, grid_label, timestamp_label), target)


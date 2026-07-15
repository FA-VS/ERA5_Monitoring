import cdsapi

c = cdsapi.Client()

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


def era5_request_fullyear(year, area_label, grid_label, timestamp_label):
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

def main():
    area_label = "western_europe"
    grid_label = "1deg"
    timestamp_label = "6h"

    for period_label, years in PERIODS.items():
        for y in years:
            target = f"era5_{area_label}_{grid_label}_{timestamp_label}_{period_label}_{y}.nc"
            print("requesting", target)
            c.retrieve(DATASET, era5_request_fullyear(y, area_label, grid_label, timestamp_label), target)

if __name__ == "__main__":
    main()


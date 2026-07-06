import cdsapi

c = cdsapi.Client()

# Western Europe box [N, W, S, E]. Adjust as needed
AREA = [60, -10, 40, 20]

# Three periods: two training decades + evaluation window
# PERIODS = {
#     "1950s": list(range(1950, 1960)),
#     "2000s": list(range(2000, 2010)),
#     "eval":  list(range(2020, 2025)),
# }
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

# ERA5 single-level dataset. MSLP + 2m temperature.
# Note: 1950-1978 lives in the "preliminary back extension"; from 1979 on
# it's the main ERA5 stream. The CDS now serves both under the same
# dataset name, but double-check the current dataset id on the CDS docs.
DATASET = "reanalysis-era5-single-levels"
VARIABLES = ["mean_sea_level_pressure", "2m_temperature"]

def request(year):
    return {
        "product_type": "reanalysis",
        "variable": VARIABLES,
        "year": str(year),
        "month": [f"{m:02d}" for m in range(1, 13)],
        "day": [f"{d:02d}" for d in range(1, 32)],
        # Download just a few times/day, to be averaged daily later.
        "time": ["00:00", "06:00", "12:00", "18:00"],
        "area": AREA,
        "format": "netcdf",
        # Optional: coarsen to save space/time. Native is 0.25.
        "grid": [1.0, 1.0],
    }

for label, years in PERIODS.items():
    for y in years:
        target = f"era5_{label}_{y}.nc"
        print("requesting", target)
        c.retrieve(DATASET, request(y), target)

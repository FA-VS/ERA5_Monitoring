import argparse, sys, glob, os

import mlflow

from MLflow_Monitoring import monitoring_run
from Compute_Drift import compute_drift

def fetch_recent(months=12, out_dir="data/recent", area=None, grid=None):
    #TODO: This needs A LOT of work
    # - Check what is already present to avoid redownloads (requires new naming convention)
    # - Make as few calls to CDS as possible to download what is missing
    # - Prune old files from data/recent
    import cdsapi, glob, os
    from datetime import date, timedelta

    # ERA5 single-level dataset. MSLP + 2m temperature.
    # Note: 1950-1978 lives in the "preliminary back extension"; from 1979 on
    # it's the main ERA5 stream. The CDS now serves both under the same
    # dataset name, but double-check the current dataset id on the CDS docs.
    DATASET = "reanalysis-era5-single-levels"
    VARIABLES = ["mean_sea_level_pressure", "2m_temperature"]

    # Geographic area and precision
    area = area or [60, -10, 40, 20]     # Western Europe [N, W, S, E]
    grid = grid or [1.0, 1.0] # Default in ERAS is [0.25,0.25], i.e. more precise
    timestamps = ["00:00", "06:00", "12:00", "18:00"] # Will be averaged out daily

    os.makedirs(out_dir, exist_ok=True)

    end = date.today() - timedelta(days=6)   # ERA5T latency guard

    # Build the list of (year, month) pairs for the last `months` months,
    # walking backwards from the cutoff month.
    ym = []
    y, m = end.year, end.month
    for _ in range(months):
        ym.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    ym.reverse()   # chronological order

    client = cdsapi.Client()
    for i, (yy, mm) in enumerate(ym):
        target = f"{out_dir}/era5_{yy}{mm:02d}.nc"

        # Skip fully-downloaded past months (caching). The final (current)
        # month is always re-fetched, since new days keep arriving in it.
        is_last = (i == len(ym) - 1)
        if os.path.exists(target) and not is_last:
            continue

        # For the trailing month, only request up to the cutoff day so we
        # don't ask CDS for days that don't exist yet.
        if is_last:
            days = [f"{d:02d}" for d in range(1, end.day + 1)]
        else:
            days = [f"{d:02d}" for d in range(1, 32)]   # CDS ignores invalid days

        client.retrieve(
            DATASET,
            {"product_type": "reanalysis",
             "variable": VARIABLES,
             "year": f"{yy}", "month": f"{mm:02d}", "day": days, # Cartesian product, must be careful here
             "time": timestamps,
             "area": area, "grid": grid, "format": "netcdf"},
            target)

    return sorted(glob.glob(f"{out_dir}/*.nc"))

def fetch_recent_year(year = 2025, out_dir="data/recent", area=None, grid=None):
    import cdsapi, os
    from datetime import date

    area = area or [60, -10, 40, 20]     # Western Europe [N, W, S, E]
    grid = grid or [1.0, 1.0]
    os.makedirs(out_dir, exist_ok=True)

    target = f"{out_dir}/recent_{year}.nc"

    cdsapi.Client().retrieve(
        "reanalysis-era5-single-levels",
        {"product_type": "reanalysis",
         "variable": ["mean_sea_level_pressure", "2m_temperature"],
         "year": str(year),
         "month": [f"{m:02d}" for m in range(1, 13)],
         "day":   [f"{d:02d}" for d in range(1, 32)],
         "time": ["00:00", "06:00", "12:00", "18:00"],
         "area": area, "grid": grid, "format": "netcdf"},
        target)

    return [target]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reference-glob", default="data/reference/*.nc")
    #p.add_argument("--recent-days", type=int, default=365)
    p.add_argument("--recent-months", type=int, default=3) #TODO: Should be exactly one year!!
    p.add_argument("--drift-threshold", type=float, default=1.0) #TODO: Update!!!
    p.add_argument("--fetch", action="store_true")
    a = p.parse_args()

    ref = sorted(glob.glob(a.reference_glob))
    #recent = fetch_recent(a.recent_days) if a.fetch \
    recent = fetch_recent_year(2025) if a.fetch \
             else sorted(glob.glob("data/recent/*.nc"))

    mlflow.set_experiment("era5_drift_monitor")
    with mlflow.start_run():
        results = compute_drift(ref, recent)
        mlflow.log_params({"reference_glob": a.reference_glob,
                           "recent_months": a.recent_months})
        mlflow.log_metrics({k: v for k, v in results.items()
                            if not k.endswith("_field")})
        drift = results["mean_drift_pct"]
        alert = drift > a.drift_threshold
        mlflow.log_metric("alert_triggered", int(alert))
        print(f"drift={drift:.3f}% threshold={a.drift_threshold} alert={alert}")
        sys.exit(1 if alert else 0)   # non-zero exit = the "raise error" signal


#if __name__ == "__main__":
#    ref = sorted(glob.glob("era5_1950s_*.nc"))     # frozen reference decade
#    recent = sorted(glob.glob("era5_eval_*.nc"))   # rolling recent window
#    monitoring_run(ref, recent)

if __name__ == "__main__":
    main()

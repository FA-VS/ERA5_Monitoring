import argparse, sys, glob, os

from MLflow_Monitoring import monitoring_run
from Compute_Drift import compute_drift

def fetch_recent(days, out_dir="data/recent"):
    #TODO: This needs A LOT of work
    # - Check what is already present to avoid redownloads (requires new naming convention)
    # - Make as few calls to CDS as possible to download what is missing
    # - Prune old files from data/recent

    import cdsapi                      # only import when actually fetching
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

    end = date.today() - timedelta(days=6)   # ERA5T latency guard
    start = end - timedelta(days=days)

    # ERA5 wants explicit year/month/day lists; build the date span
    days_span = [start + timedelta(d) for d in range((end - start).days + 1)]
    years  = sorted({f"{d.year}"       for d in days_span})
    months = sorted({f"{d.month:02d}"  for d in days_span})
    daynums= sorted({f"{d.day:02d}"    for d in days_span})

    import os; os.makedirs(out_dir, exist_ok=True)
    target = f"{out_dir}/recent.nc"

    cdsapi.Client().retrieve(
        DATASET,
        {
            "product_type": "reanalysis",
            "variable": VARIABLES,
            "year": years, "month": months, "day": daynums, #TODO: Cartesian product, doesn't work so well here...
            "time": timestamps,
            "area": area, "grid": grid, "format": "netcdf",
        },
        target,
    )
    return sorted(glob.glob(f"{out_dir}/*.nc"))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reference-glob", default="data/reference/*.nc")
    #p.add_argument("--recent-days", type=int, default=365)
    p.add_argument("--recent-days", type=int, default=90) #TODO: Should be a year!!
    p.add_argument("--drift-threshold", type=float, default=1.0) #TODO: Update!!!
    p.add_argument("--fetch", action="store_true")
    a = p.parse_args()

    ref = sorted(glob.glob(a.reference_glob))
    recent = fetch_recent(a.recent_days) if a.fetch \
             else sorted(glob.glob("data/recent/*.nc"))

    mlflow.set_experiment("era5_drift_monitor")
    with mlflow.start_run():
        results = compute_drift(ref, recent)
        mlflow.log_params({"reference_glob": a.reference_glob,
                           "recent_days": a.recent_days})
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

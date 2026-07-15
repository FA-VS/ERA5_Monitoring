import argparse, sys, glob, os

import mlflow

from Download_ERA5 import era5_request_fullyear, DATASET, AREA_LABELS, GRID_LABELS, TIMESTAMP_LABELS
from MLflow_Monitoring import monitoring_run

PERIOD_LABELS_INREPO = ["1950s", "1980s"]


def fetch_recent(months=12, out_dir="data/recent", area_label="western_europe", grid_label="1deg", timestamp_label="6h"):
    #TODO: This needs A LOT of work
    # - Check what is already present to avoid redownloads (requires new naming convention)
    # - Make as few calls to CDS as possible to download what is missing
    # - Prune old files from data/recent
    import cdsapi, glob, os
    from datetime import date, timedelta

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
    for i, (year, month) in enumerate(ym):
        target = f"{out_dir}/era5_{year}{month:02d}.nc"

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

        request = era5_request_fullyear(year, area_label, grid_label, timestamp_label)
        request["month"] = f"{month:02d}"
        request["day"] = days # Cartesian product between years, months, days - must be careful here
        client.retrieve(
            DATASET,
            request,
            target)

    return sorted(glob.glob(f"{out_dir}/*.nc"))

def fetch_recent_year(year = 2025, out_dir="data/recent", area_label="western_europe", grid_label="1deg", timestamp_label="6h"):
    import cdsapi, os
    from datetime import date

    os.makedirs(out_dir, exist_ok=True)

    target = f"{out_dir}/recent_{year}.nc"

    cdsapi.Client().retrieve(
        DATASET,
        era5_request_fullyear(year, area_label, grid_label, timestamp_label),
        target)

    return [target]

def main():

    # parsing arguments
    p = argparse.ArgumentParser()
    p.add_argument("--reference-glob", default="data/reference/*.nc")
    p.add_argument("--reference-years", default="1950s", choices = PERIOD_LABELS_INREPO)
    #p.add_argument("--recent-months", type=int, default=3) #TODO: Should be exactly one year!!
    p.add_argument("--recent-year", type=int, default=2025)
    p.add_argument("--area-label", default="western_europe", choices = AREA_LABELS)
    p.add_argument("--grid-label", default="1deg", choices = GRID_LABELS)
    p.add_argument("--timestamp-label", default="6h", choices = TIMESTAMP_LABELS)
    p.add_argument("--drift-threshold", type=float, default=1.0) #TODO: Update!!! Have to find a sane number.
    p.add_argument("--fetch", action="store_true")
    args = p.parse_args()

    # "Fetching" files
    ref = sorted(glob.glob(args.reference_glob))
    print("Ref before filtering", ref)
    ref = [ r for r in ref \
            if f"era5_{args.area_label}_{args.grid_label}_{args.timestamp_label}_{args.reference_years}" in r] # Keep only those matching the reference years (TBF)
    print("Ref after filtering", ref) #TEST
    #recent = fetch_recent(args.recent_months) if args.fetch \
    recent = fetch_recent_year(args.recent_year,
                               area_label = args.area_label,
                               grid_label = args.grid_label,
                               timestamp_label = args.timestamp_label
                               ) if args.fetch else sorted(glob.glob(f"data/recent/*.nc")) # TODO: the "else" part is dangerous...

    # Run with MLflow
    run_name =  f"drift_{args.area_label}_{args.grid_label}_{args.reference_years}_to_{args.recent_year}"
    # config -> params. TODO: Make sure all of them actually do something...
    params = {
            #"reference_glob": args.reference_glob,
            "reference_years": args.reference_years,
            #"recent_months": args.recent_months,
            "recent_year": args.recent_year,
            "region": args.area_label,
            "grid": args.grid_label,
            "timestamps": args.timestamp_label,
            "model": "gradient_3x3"}

    results, alert = monitoring_run(ref, recent, run_name, params, args.drift_threshold)
    sys.exit(1 if alert else 0) # Non-zero exit raises an error


if __name__ == "__main__":
    main()

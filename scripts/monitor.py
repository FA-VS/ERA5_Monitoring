"""Script to download ERA5 data, run a linear regression, and test it on new data."""

import sys
import glob

from modules.download_era5 import build_download_argparse, fetch_recent_year
from modules.mlflow_monitoring import monitoring_run

def main(): #pylint: disable=missing-function-docstring

    # parsing arguments
    p = build_download_argparse()
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
                               ) if args.fetch else sorted(glob.glob("data/recent/*.nc")) # TODO: make the "else" traceable / reproducible

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

    _, alert = monitoring_run(ref, recent, run_name, params, args.drift_threshold) # monitoring_run saves results via mlflow
    sys.exit(1 if alert else 0) # Non-zero exit raises an error


if __name__ == "__main__":
    main()

import mlflow
import numpy as np

from Compute_Drift import compute_drift

#TODO: make "region" and "grid" affect the files that get pulled,
# or else make sure the values provided are linked to them in some way
# (as-is, the values are logged without checking their correctness)

def monitoring_run(reference_files, recent_files,
                   region="western_europe", grid="1deg",
                   drift_threshold=1.0, ac_threshold=0.05):
    mlflow.set_experiment("era5_drift_monitor")
    with mlflow.start_run():
        # config -> params
        mlflow.log_params({
            "region": region, "grid": grid, "model": "gradient_3x3",
            "n_reference_files": len(reference_files),
            "n_recent_files": len(recent_files),
        })

        results = compute_drift(reference_files, recent_files)

        # metrics (drop the array fields before logging scalars)
        scalar_metrics = {k: v for k, v in results.items()
                          if not k.endswith("_field")}
        mlflow.log_metrics(scalar_metrics)

        # simple, regime-agnostic alert for the minimal version
        alert = (results["mean_drift_pct"] > drift_threshold
                 or abs(results["mean_ac_change"]) > ac_threshold)
        mlflow.log_metric("alert_triggered", int(alert))

        # optionally persist the drift map as an artifact
        np.save("drift_field.npy", results["drift_field"])
        mlflow.log_artifact("drift_field.npy")

        if alert:
            print(f"ALERT: drift={results['mean_drift_pct']:.3f}% "
                  f"ac_change={results['mean_ac_change']:.4f}")
        return results, alert

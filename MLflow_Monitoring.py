import mlflow
import numpy as np

from Compute_Drift import compute_drift

MLFLOW_EXP_NAME = "era5_drift_monitor_s3"
MLFLOW_ARTIFACT_LOCATION = "s3://eu-noth-1-an-fa-vs-era5-monitor/mlflow-artifacts"

def ensure_experiment(name, artifact_location):
    exp = mlflow.get_experiment_by_name(name)
    if exp is None:
        return mlflow.create_experiment(name=name,
                                        artifact_location=artifact_location)
    return exp.experiment_id


def monitoring_run(reference_files,
                   recent_files,
                   run_name,
                   params,
                   drift_threshold=1.0, ac_threshold=0.05):

    #mlflow.set_experiment("era5_drift_monitor")
    exp_id = ensure_experiment(MLFLOW_EXP_NAME,
                               MLFLOW_ARTIFACT_LOCATION)

    with mlflow.start_run(experiment_id = exp_id, run_name = run_name):
        print("artifact_uri:", mlflow.get_artifact_uri()) # TEST

        results = compute_drift(reference_files, recent_files)

        # config -> params.
        mlflow.log_params(params)

        # metrics (drop the array fields before logging scalars)
        mlflow.log_metrics({k: v for k, v in results.items()
                            if not k.endswith("_field")})

        # drift (and other) maps saved as artifacts
        for k, v in results.items():
            if k.endswith("_field"):
                artifact_filename = k+".npy"
                np.save(artifact_filename, v)
                mlflow.log_artifact(artifact_filename)

        # check alert status
        drift = results["mean_drift_pct"]
        alert = drift > drift_threshold # or abs(results["mean_ac_change"]) > ac_threshold
        mlflow.log_metric("alert_triggered", int(alert))
        print(f"drift={drift:.3f}% threshold={drift_threshold} alert={alert}")

        return results, alert


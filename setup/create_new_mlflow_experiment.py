"""Example script to create a new MLflow experiment."""

import mlflow

# Both point at your existing infrastructure (UPDATE THEM ACCORDINGLY!):
#   MLFLOW_TRACKING_URI  -> your MLflow server (here backed by Neon)
#   artifact_location    -> S3, set explicitly at creation time
mlflow.set_tracking_uri("http://your-mlflow-server:5000")   # or env var

exp_id = mlflow.create_experiment(
    name="era5_drift_monitor_s3",
    artifact_location="s3://your-bucket/mlflow",
)
print("created experiment", exp_id)
print("artifact_location:", mlflow.get_experiment(exp_id).artifact_location)

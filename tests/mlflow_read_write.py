"""Upload a metric and an artifact via MLflow, then read/download them."""

from importlib.resources import files, as_file
import mlflow

from modules.mlflow_monitoring import ensure_experiment

MLFLOW_EXP_NAME = "era5_drift_monitor_tests"
MLFLOW_ARTIFACT_URI = "s3://eu-noth-1-an-fa-vs-era5-monitor/mlflow-tests"


def main(): #pylint: disable=missing-function-docstring

    exp_id = ensure_experiment(MLFLOW_EXP_NAME, MLFLOW_ARTIFACT_URI)
    print("experiment id:", exp_id)

    # Upload
    with mlflow.start_run(experiment_id = exp_id, run_name = "github_test"):
        print("artifact_uri:", mlflow.get_artifact_uri()) # TEST

        mlflow.log_param("input1", 1)
        mlflow.log_metric("output1", 1)
        with as_file(files("tests").joinpath("array_example.npy")) as path:
            mlflow.log_artifact(path)
        print("Upload complete")

    # Download
    with mlflow.set_experiment(experiment_id = exp_id):
        #client = mlflow.MlflowClient()
        #for f in client.list_artifacts(run_id):
        #    print(f.path, f.is_dir, f.file_size)
        #path = mlflow.artifacts.download_artifacts(run_id=run_id, dst_path="./downloaded_artifacts")
        print("Download complete")

    # Clean up

if __name__ == "__main__":
    main()

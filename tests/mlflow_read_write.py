"""Upload a metric and an artifact via MLflow, then read/download them."""

from modules.mlflow_monitoring import ensure_experiment


MLFLOW_EXP_NAME = "era5_drift_monitor_tests"
MLFLOW_ARTIFACT_URI = "s3://eu-noth-1-an-fa-vs-era5-monitor/mlflow-tests"


def main(): #pylint: disable=missing-function-docstring

    exp_id = ensure_experiment(MLFLOW_EXP_NAME,
                               MLFLOW_ARTIFACT_URI)

    with mlflow.start_run(experiment_id = exp_id, run_name = run_name):
        print("artifact_uri:", mlflow.get_artifact_uri()) # TEST

        mlflow.log_param("input1", 1)
	    mlflow.log_metric("output1", 1)

	    artifact_filename = os.path.join("artifacts", k + ".npy")
	    np.save(artifact_filename, v)
	    mlflow.log_artifact(artifact_filename)
	    os.remove(artifact_filename)


if __name__ == "__main__":
    main()

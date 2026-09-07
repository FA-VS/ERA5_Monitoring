"""Integration test: log a metric and an artifact via MLflow, then read them back."""

import os
import tempfile
from pathlib import Path

import mlflow
import pytest

from modules.mlflow_monitoring import ensure_experiment

MLFLOW_EXP_NAME = "era5_drift_monitor_tests"
MLFLOW_ARTIFACT_URI = "s3://eu-noth-1-an-fa-vs-era5-monitor/mlflow-tests"
ARRAY_EXAMPLE = Path(__file__).parent / "array_example.npy"

pytestmark = pytest.mark.integration


def test_mlflow_log_and_fetch():
    exp_id = ensure_experiment(MLFLOW_EXP_NAME, MLFLOW_ARTIFACT_URI)

    with mlflow.start_run(experiment_id=exp_id, run_name="github_test") as run:
        run_id = run.info.run_id
        mlflow.log_param("input1", 1)
        mlflow.log_metric("output1", 1)
        mlflow.log_artifact(str(ARRAY_EXAMPLE))

    try:
        client = mlflow.MlflowClient()
        fetched = client.get_run(run_id)
        assert fetched.data.params["input1"] == "1"
        assert fetched.data.metrics["output1"] == 1.0

        artifact_paths = {f.path for f in client.list_artifacts(run_id)}
        assert "array_example.npy" in artifact_paths

        with tempfile.TemporaryDirectory() as dst:
            local = mlflow.artifacts.download_artifacts(
                run_id=run_id,
                artifact_path="array_example.npy",
                dst_path=dst,
            )
            assert os.path.exists(local)
    finally:
        mlflow.delete_run(run_id)  # best-effort; MLflow doesn't guarantee immediate deletion

"""Fit and evaluate the gradient regression on reference ERA5 data (local, no external services)."""

import numpy as np
import pytest
import pytest_check as check

from modules.download_era5 import DATA_DIR
from modules.compute_drift import _daily, fit_gradient, eval_gradient, lag1_autocorr

REFERENCE_FILES = sorted((DATA_DIR / "reference").glob("*1980s*.nc"))


@pytest.mark.skipif(not REFERENCE_FILES, reason="No 1980s reference data found in data/reference")
def test_fit_and_eval_gradient():
    dataset = _daily(REFERENCE_FILES, "msl")

    coeffs = fit_gradient(dataset)
    rmse = eval_gradient(coeffs, dataset)
    autocorr = lag1_autocorr(dataset)

    rmse_mean = float(np.nanmean(rmse))
    autocorr_mean = float(np.nanmean(autocorr))
    print("rmse_mean:", rmse_mean, "autocorr_mean:", autocorr_mean)

    check.greater_equal(rmse_mean, 0)
    check.is_not_nan(rmse_mean)
    check.between_equal(autocorr_mean, -1.0, 1.0)

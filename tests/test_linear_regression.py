"""Fit and evaluate the gradient regression on reference ERA5 data (local, no external services)."""

import numpy as np
import pytest

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

    assert rmse_mean >= 0
    assert not np.isnan(rmse_mean)
    assert -1.0 <= autocorr_mean <= 1.0

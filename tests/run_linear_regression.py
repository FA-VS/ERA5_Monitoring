"""Run linear regression and evaluate it on reference data"""

from pathlib import Path
import numpy as np

from modules.download_era5 import DATA_DIR
from modules.compute_drift import _daily, fit_gradient, eval_gradient, lag1_autocorr

reference_folder =  DATA_DIR / "reference"
reference_files =  sorted( reference_folder.glob("*1980s") )
#reference_files = [ f for f in reference_files if "1980s" in f ]

def main():

    dataset = _daily(reference_files, "msl")

    coeffs = fit_gradient(dataset)
    rmse = eval_gradient(coeffs, dataset)
    autocorr = lag1_autocorr(dataset)

    rmse_mean = float(np.nanmean(rmse_frozen))
    autocorr_mean = float(np.nanmean(autocorr))
    print(rmse_mean, autocorr_mean)
    return rmse_mean, autocorr_mean

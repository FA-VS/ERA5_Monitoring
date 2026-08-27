"""Run linear regression and evaluate it on reference data"""

import glob
import numpy as np

from modules.compute_drift import _daily, fit_gradient, eval_gradient, lag1_autocorr

reference_folder =  "data/reference/"
reference_files = ref = sorted(glob.glob(reference_folder))
reference_files = [ f for f in reference_files if "1980s" in f ]

def main():

    dataset = _daily(reference_files, "msl")

    coeffs = fit_gradient(dataset)
    rmse = eval_gradient(coeffs, dataset)
    autocorr = lag1_autocorr(dataset)

    rmse_mean = float(np.nanmean(rmse_frozen))
    autocorr_mean = float(np.nanmean(autocorr))
    print(rmse_mean, autocorr_mean)
    return rmse_mean, autocorr_mean

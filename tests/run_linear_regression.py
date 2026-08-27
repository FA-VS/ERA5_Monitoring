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

    return float(np.nanmean(rmse_frozen)), float(np.nanmean(autocorr))

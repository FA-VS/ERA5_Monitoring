"""Module to do linear regressions on ERA5 data.

Functions:
    fit_gradient
    eval_gradient
    lag1_autocorr
    compute_drift
"""


import numpy as np
import xarray as xr

def _daily(files: list[str], short: str) -> xr.Dataset:
    """Concatenate files found locally, then average values on daily basis.

    Args:
        files: list of paths
        short: ERA5 variable short name

    Returns:
        xarray.Dataset with the averaged daily values from those files.
    """
    # Uses dask for lazy reading
    ds = xr.open_mfdataset(files, combine="by_coords",
                           engine="h5netcdf", chunks=None)
    return ds[short].resample(valid_time="1D").mean()

def _grad_features(field: np.ndarray) -> np.ndarray:
    """Compute center value, "Zonal" (E-W) gradient, and "Meridional" (N-S) gradient."""
    c  = field[:, 1:-1, 1:-1]
    dz = field[:, 1:-1, 2:] - field[:, 1:-1, :-2]
    dm = field[:, 2:, 1:-1] - field[:, :-2, 1:-1]
    return c, dz, dm

def fit_gradient(train: xr.Dataset) -> np.ndarray:
    """Do linear regression on data at time t+1 based on data at time t."""
    f = train.values #Note that this loads the whole dataset into memory!!! TODO: Avoid overloading memory
    c, dz, dm = _grad_features(f)
    ct, dzt, dmt = c[:-1], dz[:-1], dm[:-1] # Values at {t} to put into regression formula
    cy = c[1:] # Value at {t+1}, to be predicted
    t, ny, nx = cy.shape
    coeffs = np.full((ny, nx, 4), np.nan)
    # Use np.linalg to solve the linear regression on three features (central and two gradients)
    # Note that we ignore time as a predictor
    for i in range(ny):
        for j in range(nx):
            features = np.column_stack([np.ones(t), ct[:, i, j],
                                 dzt[:, i, j], dmt[:, i, j]])
            coeffs[i, j], *_ = np.linalg.lstsq(features, cy[:, i, j], rcond=None) # Linear regression magic
    return coeffs

def eval_gradient(coeffs: np.ndarray, evald: xr.Dataset) -> np.ndarray:
    """Evaluate RMSE per gridpoint on test data using linear regression coefficients.

    Args:
        coeffs: output of fit_gradient
        evald: ERA5 test data

    Returns:
        numpy ndarray with the time-averaged RMSE value per gridpoint.
    """
    f = evald.values
    c, dz, dm = _grad_features(f)
    ct, dzt, dmt = c[:-1], dz[:-1], dm[:-1] # Values at {t} to put into regression formula
    cy = c[1:] # Value at {t+1}, to be predicted
    # In the following lines, the "None" "tensorizes" the array (kind of like doing coeffs = [coeffs])
    pred = (coeffs[None, :, :, 0]
            + coeffs[None, :, :, 1] * ct
            + coeffs[None, :, :, 2] * dzt
            + coeffs[None, :, :, 3] * dmt)
    return np.sqrt(((pred - cy) ** 2).mean(0))     # per-gridpoint RMSE

def lag1_autocorr(da: xr.Dataset) -> np.ndarray:
    """Compute correlation coefficient between data at time t and t+1.

    Args:
        da: output from "_daily"

    Returns:
        numpy ndarray with the "lag" (t+1 vs t) autocorrelation value per gridpoint,
        a measure of the "persistence" of the measurement at each given location.
     """
    x = da.values
    x0, x1 = x[:-1], x[1:]
    x0m, x1m = x0.mean(0), x1.mean(0)
    num = ((x0 - x0m) * (x1 - x1m)).sum(0) # covariance between today and tomorrow
    den = np.sqrt(((x0 - x0m) ** 2).sum(0) * ((x1 - x1m) ** 2).sum(0)) # product of standard deviations
    return num / den                               # per-gridpoint lag-1 AC

def compute_drift(reference_files: list[str], recent_files: list[str], short: str ="msl") -> dict[str,float|np.ndarray]:
    """Frozen reference model vs freshly-refit recent model, on recent days.

    Args:
        reference_files: list of paths to reference ERA5 files
        recent_files: list of paths to recent ERA5 files
        msl: ERA5 variable short name (default 'msl')

    Returns:
        Dictionary with the results of the drift computation. Includes two kinds of values,
        floats (such as the mean drift percentage or the fraction of points where the drift increased),
        and np.ndarrays, with names ending in "_field" (such as the RMSE from either model on each gridpoint).

        mean_drift_pct:         Average RMSE percentage change, comparing "frozen" model with "recent" model, applied on recent data
        frac_points_positive:   Fraction of grid points where the RMSE is worse for the "frozen" model than for the "recent" one applied on recent data
        mean_rmse_frozen:       Average RMSE for the frozen model applied on recent data
        mean_ac_change:         Average Autocorrelation change between the "frozen" data and the "recent" one
        reg_coeff_ct_field:     Linear regression coefficient on the central value of the "frozen" model (per gridpoint)
        reg_coeff_dzt_field:    Linear regression coefficient on the zonal graidient of the "frozen" model (per gridpoint)
        reg_coeff_dmt_field:    Linear regression coefficient on the meridional gradient of the "frozen" model (per gridpoint)
        ac_ref_field:           Autocorrelation of the "frozen" data (per gridpoint)
        ac_change_field:        Autocorrelation change between the "frozen" data and the "recent" one (per gridpoint)
        rmse_frozen_field:      RMSE of the "frozen" model applied on the recent data (per gridpoint)
        rmse_recent_field:      RMSE of the "recent" model applied on the recent data (per gridpoint)
        drift_field:            RMSE percentage change, comparing "frozen" model with "recent" model, applied on recent data (per gridpoint)
    """
    ref   = _daily(reference_files, short)
    recent = _daily(recent_files, short)

    frozen_coeffs = fit_gradient(ref)       # the "deployed/frozen" model
    recent_coeffs = fit_gradient(recent)    # model derived from "recent" data

    rmse_frozen = eval_gradient(frozen_coeffs, recent)
    rmse_recent = eval_gradient(recent_coeffs, recent)
    drift_pct = 100.0 * (rmse_frozen - rmse_recent) / rmse_recent

    ac_ref = lag1_autocorr(ref)
    ac_recent = lag1_autocorr(recent)
    ac_change = ac_recent - ac_ref

    return {
        "mean_drift_pct":       float(np.nanmean(drift_pct)),
        "frac_points_positive": float(np.mean(drift_pct > 0)),
        "mean_rmse_frozen":     float(np.nanmean(rmse_frozen)),
        "mean_ac_change":       float(np.nanmean(ac_change)),
        "reg_coeff_ct_field":   frozen_coeffs[:, :, 1],
        "reg_coeff_dzt_field":  frozen_coeffs[:, :, 2],
        "reg_coeff_dmt_field":  frozen_coeffs[:, :, 3],
        # persistence-vs-variance contrast, per original paper:
        "ac_ref_field":         ac_ref,
        #"ac_recent_field":    ac_recent,
        "ac_change_field":      ac_change,
        "rmse_frozen_field":    rmse_frozen,
        "rmse_recent_field":    rmse_recent,
        "drift_field":          drift_pct,
    }

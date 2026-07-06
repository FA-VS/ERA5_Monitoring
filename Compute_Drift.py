import numpy as np
import xarray as xr

def _daily(files, short): # List of files, short name of ERAS variable
    # Concatenate files found locally,
    # then average/Collapse values on daily basis
    # Uses dask for lazy reading
    ds = xr.open_mfdataset(files, combine="by_coords",
                           engine="h5netcdf", chunks=None)
    return ds[short].resample(valid_time="1D").mean()

def _grad_features(field):
    # Compute center value, "Zonal" (E-W) gradient, "Meridional" (N-S) gradient
    c  = field[:, 1:-1, 1:-1]
    dz = field[:, 1:-1, 2:] - field[:, 1:-1, :-2]
    dm = field[:, 2:, 1:-1] - field[:, :-2, 1:-1]
    return c, dz, dm

def fit_gradient(train): # training data
    f = train.values #Note that this loads the whole dataset into memory!!!
    c, dz, dm = _grad_features(f)
    ct, dzt, dmt = c[:-1], dz[:-1], dm[:-1] # Values at {t} to put into regression formula
    cy = c[1:] # Value at {t+1}, to be predicted
    t, ny, nx = cy.shape
    coeffs = np.full((ny, nx, 4), np.nan)
    # Use np.linalg to solve the linear regression on three features (central and two gradients)
    # Note that we ignore time
    for i in range(ny):
        for j in range(nx):
            A = np.column_stack([np.ones(t), ct[:, i, j],
                                 dzt[:, i, j], dmt[:, i, j]])
            coeffs[i, j], *_ = np.linalg.lstsq(A, cy[:, i, j], rcond=None)
    return coeffs

def eval_gradient(coeffs, evald): # output of fit_gradient, test data
    f = evald.values
    c, dz, dm = _grad_features(f)
    ct, dzt, dmt = c[:-1], dz[:-1], dm[:-1] # Values at {t} to put into regression formula
    cy = c[1:] # Value at {t+1}, to be predicted
    pred = (coeffs[None, :, :, 0]
            + coeffs[None, :, :, 1] * ct
            + coeffs[None, :, :, 2] * dzt
            + coeffs[None, :, :, 3] * dmt)
    return np.sqrt(((pred - cy) ** 2).mean(0))     # per-gridpoint RMSE

def lag1_autocorr(da): # output from _daily
    # Compute correlation coefficient between today and tomorrow,
    # a measure of the "persistence" of the measurement at a given location.
    x = da.values
    x0, x1 = x[:-1], x[1:]
    x0m, x1m = x0.mean(0), x1.mean(0)
    num = ((x0 - x0m) * (x1 - x1m)).sum(0) # covariance between today and tomorrow
    den = np.sqrt(((x0 - x0m) ** 2).sum(0) * ((x1 - x1m) ** 2).sum(0)) # product of standard deviations
    return num / den                               # per-gridpoint lag-1 AC

def compute_drift(reference_files, recent_files, short="msl"):
    """Frozen reference model vs freshly-refit recent model, on recent days."""
    ref   = _daily(reference_files, short)
    recent = _daily(recent_files, short)

    frozen_coeffs = fit_gradient(ref)              # the "deployed" rule
    recent_coeffs = fit_gradient(recent)           # what recent data implies

    rmse_frozen = eval_gradient(frozen_coeffs, recent)
    rmse_recent = eval_gradient(recent_coeffs, recent)
    drift_pct = 100.0 * (rmse_frozen - rmse_recent) / rmse_recent

    ac_ref = lag1_autocorr(ref)
    ac_recent = lag1_autocorr(recent)
    ac_change = ac_recent - ac_ref

    return {
        "mean_drift_pct":     float(np.nanmean(drift_pct)),
        "frac_points_positive": float(np.mean(drift_pct > 0)),
        "mean_rmse_frozen":   float(np.nanmean(rmse_frozen)),
        "mean_ac_change":     float(np.nanmean(ac_change)),
        # persistence-vs-variance contrast, the paper-correct signal:
        "ac_ref_field":       ac_ref,
        #"ac_recent_field":    ac_recent,
        "ac_change_field":    ac_change,
        "drift_field":        drift_pct,
    }

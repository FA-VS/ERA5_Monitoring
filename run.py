import glob

from MLflow_Monitoring import monitoring_run

if __name__ == "__main__":
    ref = sorted(glob.glob("era5_1950s_*.nc"))     # frozen reference decade
    recent = sorted(glob.glob("era5_eval_*.nc"))   # rolling recent window
    monitoring_run(ref, recent)

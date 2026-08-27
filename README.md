# Introduction

Simple tool to model atmospheric data around Europe, based on ERA5 data (using Mean Sea-Level Pressure and Temperature 2m above ground).

Based on the paper by Haokun Zhou (arXiv:2511.19638, 2025), we model the daily evolution of MSLP with a linear regression on the pressure and its zonal and meridional gradients. The regression is "trained" on historic data, and its performance on recent data is compared based on the slice of data used for training (e.g. 1950s vs 2000s, applied on 2020s data), to see the drift in the "persistence" of pressure.

WIP: The MLflow database and artifact registry are currently private, so the outputs are not visible. I intend to make them public (read-only) in due time.

# Components

- Linear regressions and array management with numpy (TODO: use sklearn for more advanced analysis).
- MLflow is used to track the training artifacts and the evaluation metrics, depending on training and evaluation datasets.
- Neon provides the PostgreSQL database for MLflow to save the training/evaluation metrics.
- AWS S3 is used to save the training artifacts.
- Docker to build images to run the evaluation of a regression on (new) data - the images are saved in Github's Docker Registry.
- Github actions run the training and evaluation automatically, on push and on a schedule, including downloading (new) data from CDS.

There is no always-on mlflow server to track the results. To analyse the resuls, start your own MLflow server locally by connecting to the PostgreSQL URI (you need the account name and password, which are private for now).

For details on how to setup the different elements if you want to use your own database and artifact registry in the github actions, see private_setup.txt

# How to run

To handle authentications more conveniently, all of the workflow is run via github actions. By default, github actions will run at 3AM on the first of the month. They will also run after every push that modifies a python file, the pip requirements, the Dockerfile, or the files in `data/reference`. You may also run them manually from the github website by navigating to Action - ERA5 Drift Monitor, in which case you can specify the reference years to train the regression on (from the list present in the repo, TBC), the year to evaluate the regression on (data fetched automatically from CDS for you), and the drift threshold above which to raise an alert.

The workflow will first build a new Docker image if the repository changed. It uses a slim Python 3.11 installation, installs git and the pip requirements, and saves the files in data/reference, then pushes the resulting image to Github's registry.
Then, it will authenticate with AWS and CDS, download the CDS data for the recent year, train the regression on the existing reference data, and evaluate it on the recent year. MLflow will automatically save the results in the database.

# Results

See the notebooks folder for an example on how to examine the results. As written, they require that you have setup the right environment variables (namely access to the both database and artifact registry) before you can run it.
![Daily pressure front evolution over Western Europe](https://github.com/FA-VS/ERA5_Monitoring/tree/main/images/PressureMovement.png)
![Pressure model drift from the 80s to 2025](https://github.com/FA-VS/ERA5_Monitoring/tree/main/images/PressureModelDrift.png)

Note that I am not a meteorologist, and that the analysis remains very superficial (just a linear regression)! Take the outputs from this analysis with a very large dose of skepticism.

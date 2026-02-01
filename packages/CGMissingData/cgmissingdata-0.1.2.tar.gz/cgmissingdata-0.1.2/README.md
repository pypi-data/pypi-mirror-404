# CGMissingData

CGMissingData is a simple missing-data benchmarking package that runs:

MICE imputation (IterativeImputer)

Random Forest regression

KNN regression

It helps you test model performance under different missing-value rates.


Your CSV must include at least these columns:

LBORRES — glucose value (target)

TimeSeries — time series data

TimeDifferenceMinutes — time difference in minutes

USUBJID — subject ID

How to Run?
- Install python on your device. I am showing all the steps 
- Go to your project folder. e.g., cd C:\XYZ\Downloads\CGMissingData_project
- Create venv (if not already created):
py -m venv .venv
- Activate venv:
.\.venv\Scripts\activate.bat
- Install and Verify
python -m pip install --upgrade pip
pip install -e .
python -c "import CGMissingData; print(CGMissingData.__file__)"

- Go to Powershell and paste the following. Make sure you have replaced the location.
Set-Location "C:\XYZ\\CGMissingData_project\CGMissingData_project"
Get-ChildItem
- Paste it:
.\.venv\Scripts\python.exe -c "from CGMissingData import run_missingness_benchmark; r=run_missingness_benchmark('CGMExampleData.csv', mask_rates=[0.05,0.10,0.20,0.30,0.40]); print(r); r.to_csv('results.csv', index=False)"

Instead of 'CGMExampleData.csv, you can replace with your csv name.
- Done!



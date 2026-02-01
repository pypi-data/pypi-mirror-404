# CGMMissingData

This package runs a missing-data benchmark using:
- MICE (IterativeImputer)
- Random Forest
- KNN

Defaults:
- Target: LBORRES (glucose level)
- Features: TimeSeries, TimeDifferenceMinutes, USUBJID


How to Run?
- Install python on your device. I am showing all the steps 
- Go to your project folder. e.g., cd C:\XYZ\Downloads\CGMMissingData_project
- Create venv (if not already created):
py -m venv .venv
- Activate venv:
.\.venv\Scripts\activate.bat
- Install and Verify
python -m pip install --upgrade pip
pip install -e .
python -c "import CGMMissingData; print(CGMMissingData.__file__)"

- Go to Powershell and paste the following. Make sure you have replaced the location.
Set-Location "C:\XYZ\\CGMMissingData_project\CGMMissingData_project"
Get-ChildItem
- Paste it:
.\.venv\Scripts\python.exe -c "from CGMMissingData import run_missingness_benchmark; r=run_missingness_benchmark('CGMExampleData.csv', mask_rates=[0.05,0.10,0.20,0.30,0.40]); print(r); r.to_csv('results.csv', index=False)"

Instead of 'CGMExampleData.csv, you can replace with your csv name.
- Done!



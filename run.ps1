$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  Write-Host "First run: creating virtual environment and installing dependencies..."
  python -m venv .venv
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}
Write-Host "Job Hunter BD running at http://127.0.0.1:8077  (Ctrl+C to stop)"
Start-Process "http://127.0.0.1:8077"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8077

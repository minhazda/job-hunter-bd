# Job Hunter BD launcher - double-click via the desktop shortcut.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$port = 8077

# Already running? Just open the browser.
try {
  $null = Invoke-WebRequest -Uri "http://127.0.0.1:$port" -UseBasicParsing -TimeoutSec 2
  Start-Process "http://127.0.0.1:$port"
  exit 0
} catch {}

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  Write-Host "First run: creating virtual environment and installing dependencies..." -ForegroundColor Yellow
  $basePy = Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"
  if (-not (Test-Path $basePy)) { $basePy = "python" }
  & $basePy -m venv .venv
  & $py -m pip install -r requirements.txt
}

Write-Host "  Job Hunter BD - starting server (takes ~10s)..." -ForegroundColor Cyan
Start-Process -WindowStyle Hidden -FilePath $py -ArgumentList "-m","uvicorn","app.main:app","--port","$port" -WorkingDirectory $PSScriptRoot

# Wait until the server actually answers, THEN open the browser.
$up = $false
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 2
  try { $null = Invoke-WebRequest -Uri "http://127.0.0.1:$port" -UseBasicParsing -TimeoutSec 2; $up = $true; break } catch {}
}
if ($up) {
  Start-Process "http://127.0.0.1:$port"
  Write-Host "  Running at http://127.0.0.1:$port - this window can be closed." -ForegroundColor Green
  Start-Sleep -Seconds 3
} else {
  Write-Host "  Server did not start within 60s. Tell your assistant." -ForegroundColor Red
  Read-Host "  Press Enter to close"
}

# start.ps1 - Start the Bumblebee dashboard backend (serves API + built frontend)
# Port 8765. Config: dashboard.config.json
# The backend serves the built frontend at http://localhost:8765

$root = Split-Path $PSScriptRoot -Parent
$env:DASHBOARD_CONFIG = Join-Path $root "dashboard.config.json"

Set-Location $root

# Check if frontend is built
$build = Join-Path $root "ui\build"
if (-not (Test-Path $build)) {
    Write-Host "WARNING: No built frontend at $build" -ForegroundColor Yellow
    Write-Host "Run: cd ui && npm run build" -ForegroundColor Yellow
}

Write-Host "Starting dashboard backend on http://localhost:8765 ..." -ForegroundColor Cyan
python -m uvicorn "api.main:app" --host 127.0.0.1 --port 8765

# start.ps1 — Start the Bumblebee dashboard (API + built frontend)
# Usage: .\start.ps1 [-Port 8765] [-ConfigPath dashboard.config.json]

param(
    [int]$Port = 8765,
    [string]$ConfigPath = ""
)

$root = Split-Path $MyInvocation.MyCommand.Path -Parent

# Auto-find or create config
if ($ConfigPath -eq "") {
    $ConfigPath = Join-Path $root "dashboard.config.json"
    if (!(Test-Path $ConfigPath)) {
        $ConfigPath = Join-Path $root "dashboard.config.example.json"
    }
}
$env:DASHBOARD_CONFIG = (Resolve-Path $ConfigPath).Path

# Check frontend build
$build = Join-Path $root "ui\build"
if (!(Test-Path $build)) {
    Write-Host "Building frontend..." -ForegroundColor Yellow
    Set-Location (Join-Path $root "ui")
    npm install
    npm run build
    if (!(Test-Path $build)) {
        Write-Host "Frontend build failed. Run 'cd ui && npm run build' manually." -ForegroundColor Red
        exit 1
    }
}

# Install API deps
Write-Host "Checking API dependencies..." -ForegroundColor Yellow
pip install -q -r (Join-Path $root "api\requirements.txt") 2>&1 | Out-Null

Set-Location $root
Write-Host "Starting dashboard on http://0.0.0.0:$Port ..." -ForegroundColor Cyan
python -m uvicorn api.main:app --host 0.0.0.0 --port $Port

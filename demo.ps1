<#
.SYNOPSIS
    Bumblebee Conference Demo — One-click launcher
.DESCRIPTION
    Resets the demo project DB to a partial state, starts the dashboard,
    and kicks off the executor for a live coding demo.
.PARAMETER Project
    Demo project to run (default: food-cart)
.PARAMETER Reset
    Reset the project DB before starting (default: true)
.PARAMETER Port
    Dashboard port (default: 8765)
.PARAMETER SkipDashboard
    Don't start the dashboard (if already running)
.EXAMPLE
    .\demo.ps1
.EXAMPLE
    .\demo.ps1 -Project food-cart -Port 9000
.EXAMPLE
    .\demo.ps1 -SkipDashboard  # Dashboard already running, just reset + start executor
#>
param(
    [string]$Project = "food-cart",
    [switch]$NoReset,
    [int]$Port = 8765,
    [switch]$SkipDashboard
)

$ErrorActionPreference = "Stop"
$root = Split-Path $MyInvocation.MyCommand.Path -Parent

Write-Host ""
Write-Host "  ====================================" -ForegroundColor Yellow
Write-Host "    Bumblebee — Conference Demo" -ForegroundColor Yellow
Write-Host "  ====================================" -ForegroundColor Yellow
Write-Host ""

# ---------------------------------------------------------------------------
# Step 1: Check Lemonade
# ---------------------------------------------------------------------------
Write-Host "[1/4] Checking Lemonade server..." -ForegroundColor Cyan
$lemonadeOk = $false
try {
    $resp = Invoke-RestMethod -Uri "http://[::1]:13305/api/v1/health" -TimeoutSec 3 -ErrorAction Stop
    $model = $resp.model_loaded
    if ($model) {
        Write-Host "  Lemonade OK — model: $model" -ForegroundColor Green
        $lemonadeOk = $true
    } else {
        Write-Host "  Lemonade running but no model loaded." -ForegroundColor Yellow
        Write-Host "  Load a coding model (e.g. Qwen3-Coder) in Lemonade before running the demo." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Lemonade not reachable at http://[::1]:13305" -ForegroundColor Red
    Write-Host "  Start Lemonade and load a coding model first." -ForegroundColor Red
    Write-Host "  The dashboard will still work, but the executor won't be able to code." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Step 2: Reset demo project (optional)
# ---------------------------------------------------------------------------
# Look in demos/ first, then projects/
$projectDir = Join-Path $root "demos\$Project"
if (!(Test-Path $projectDir)) {
    $projectDir = Join-Path $root "projects\$Project"
}
if (!(Test-Path $projectDir)) {
    Write-Host "  ERROR: Project '$Project' not found in demos/ or projects/" -ForegroundColor Red
    exit 1
}

if (-not $NoReset) {
    Write-Host "[2/4] Resetting demo project '$Project'..." -ForegroundColor Cyan
    
    $resetScript = Join-Path $projectDir "reset_demo.py"
    $seedScript = Join-Path $projectDir "seed_tickets.py"
    
    if (Test-Path $resetScript) {
        python $resetScript
        Write-Host "  Demo reset complete." -ForegroundColor Green
    } elseif (Test-Path $seedScript) {
        python $seedScript
        Write-Host "  DB re-seeded from scratch." -ForegroundColor Green
    } else {
        Write-Host "  No reset or seed script found. Using existing DB." -ForegroundColor Yellow
    }
} else {
    Write-Host "[2/4] Skipping reset (--NoReset)." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Step 3: Start dashboard
# ---------------------------------------------------------------------------
if (-not $SkipDashboard) {
    Write-Host "[3/4] Starting dashboard on port $Port..." -ForegroundColor Cyan
    
    # Kill existing dashboard on this port
    $existing = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
        Where-Object { $_.State -eq 'Listen' }
    if ($existing) {
        Write-Host "  Port $Port already in use — dashboard may be running." -ForegroundColor Yellow
        Write-Host "  Skipping dashboard start. Kill it first if you want a fresh one." -ForegroundColor Yellow
    } else {
        $dashStart = Join-Path $root "dashboard\start.ps1"
        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$dashStart`" -Port $Port" -WindowStyle Minimized
        Write-Host "  Dashboard starting in background..." -ForegroundColor Green
        Start-Sleep -Seconds 3
    }
} else {
    Write-Host "[3/4] Skipping dashboard start." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Step 4: Start executor (live coding)
# ---------------------------------------------------------------------------
if ($lemonadeOk) {
    Write-Host "[4/4] Starting executor for '$Project'..." -ForegroundColor Cyan
    
    $executorScript = Join-Path $projectDir "run_executor.py"
    if (Test-Path $executorScript) {
        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -Command `"cd '$projectDir'; python run_executor.py`"" -WindowStyle Normal
        Write-Host "  Executor running in new window." -ForegroundColor Green
    } else {
        Write-Host "  No run_executor.py found in $projectDir" -ForegroundColor Red
    }
} else {
    Write-Host "[4/4] Skipping executor (Lemonade not available)." -ForegroundColor Yellow
    Write-Host "  Start Lemonade, then run: cd $projectDir && python run_executor.py" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "  ====================================" -ForegroundColor Green
Write-Host "    Demo Ready!" -ForegroundColor Green
Write-Host "  ====================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Dashboard:  http://localhost:$Port" -ForegroundColor Cyan
Write-Host "  Project:    $Project" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Tip: Select '$Project' in the sidebar, then click 'Dashboard'" -ForegroundColor Yellow
Write-Host "  Tip: Click 'Cost Comparison' tab to show cloud vs local savings" -ForegroundColor Yellow
Write-Host ""

# Open browser
Start-Process "http://localhost:$Port"

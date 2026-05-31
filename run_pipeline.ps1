# PowerShell script to run the sales automation pipeline end-to-end automatically.
# Usage:
#   .\run_pipeline.ps1 -Limit 5 -DryRun $true
#

param (
    [int]$Limit = 0,
    [bool]$DryRun = $true
)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Website-Audit Sales Automation Pipeline Initiated" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Activate Virtual Environment
if (Test-Path ".venv\Scripts\activate.ps1") {
    Write-Host "[1/5] Activating Python virtual environment..." -ForegroundColor Yellow
    . .venv\Scripts\activate.ps1
} else {
    Write-Host "[Warning] Virtual environment not found at .venv. Running with system python." -ForegroundColor Red
}

$LimitArg = ""
if ($Limit -gt 0) {
    $LimitArg = "--limit $Limit"
}

# 2. Run Crawler / Scraper
Write-Host "[2/5] Starting Web Scraping (Playwright Crawler)..." -ForegroundColor Yellow
if ($Limit -gt 0) {
    python -m src.main scrape --limit $Limit
} else {
    python -m src.main scrape
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Scraping stage failed. Aborting." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 3. Run Analysis & Evidence Mapping
Write-Host "[3/5] Starting Web Audits and Service Mapping..." -ForegroundColor Yellow
if ($Limit -gt 0) {
    python -m src.main analyze --limit $Limit
} else {
    python -m src.main analyze
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Analysis stage failed. Aborting." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 4. Run LLM Email Draft Generation
Write-Host "[4/5] Starting Cold Email Draft Generation (LLM)..." -ForegroundColor Yellow
if ($Limit -gt 0) {
    python -m src.main generate --limit $Limit
} else {
    python -m src.main generate
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Generation stage failed. Aborting." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 5. Run Email Sending Queue
Write-Host "[5/5] Starting Send Dispatcher..." -ForegroundColor Yellow
$SendArgs = ""
if ($Limit -gt 0) {
    $SendArgs = "--limit $Limit"
}
if ($DryRun) {
    $SendArgs += " --dry-run"
} else {
    $SendArgs += " --real-run"
}

python -m src.main send $SendArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Send dispatcher stage failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "==================================================" -ForegroundColor Green
Write-Host "Pipeline execution completed successfully!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

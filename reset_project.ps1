# PowerShell script to reset the sales automation database and screenshots.
# Usage:
#   .\reset_project.ps1
#

Write-Host "==========================================" -ForegroundColor Red
Write-Host "Resetting Sales Automation Local Storage" -ForegroundColor Red
Write-Host "==========================================" -ForegroundColor Red

# 1. Remove SQLite Database
if (Test-Path "data/leads.db") {
    try {
        Remove-Item "data/leads.db" -Force
        Write-Host "[OK] Database file (data/leads.db) deleted successfully." -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Could not delete data/leads.db. Ensure the Uvicorn server is stopped and try again." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[INFO] No leads.db file found. Database is already clear." -ForegroundColor DarkGray
}

# 2. Clear Crawled Screenshots
if (Test-Path "data/screenshots") {
    $pngs = Get-ChildItem "data/screenshots/*.png" -ErrorAction SilentlyContinue
    if ($pngs) {
        Remove-Item "data/screenshots/*.png" -Force
        Write-Host "[OK] Cleared $($pngs.Count) screenshots from data/screenshots/." -ForegroundColor Green
    } else {
        Write-Host "[INFO] Screenshots directory is already clear." -ForegroundColor DarkGray
    }
} else {
    Write-Host "[INFO] Screenshots directory does not exist." -ForegroundColor DarkGray
}

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Reset Complete! Run the app to start fresh." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

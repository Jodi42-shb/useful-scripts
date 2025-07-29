# Clear-StartMenuPins.ps1
# Clears ONLY the Start Menu pinned apps (not taskbar)
# Works on Windows 10 and 11

Write-Host "Removing Start Menu pinned apps..." -ForegroundColor Cyan

# Paths to Start Menu layout and cache
$startLayoutPath = "$env:LocalAppData\Microsoft\Windows\Shell\LayoutModification.xml"
$startBinPath   = "$env:LocalAppData\Microsoft\Windows\Shell\*start*"

# Step 1: Remove LayoutModification.xml (custom layout)
if (Test-Path $startLayoutPath) {
    Remove-Item $startLayoutPath -Force
    Write-Host "Removed LayoutModification.xml" -ForegroundColor Green
}

# Step 2: Remove start layout cache files
if (Test-Path "$env:LocalAppData\Microsoft\Windows\Shell") {
    Remove-Item $startBinPath -Force -ErrorAction SilentlyContinue
    Write-Host "Cleared Start layout cache files" -ForegroundColor Green
} else {
    Write-Warning "Shell directory not found. User may not have initialized Start yet."
}

# Step 3: Kill and restart Explorer to apply changes
Write-Host "Restarting Windows Explorer..." -ForegroundColor Cyan
try {
    Stop-Process -Name explorer -Force
    Write-Host "Windows Explorer restarted successfully." -ForegroundColor Green
} catch {
    Write-Error "Failed to restart Explorer: $_"
}

Write-Host "✅ Start Menu pins have been cleared." -ForegroundColor Green
Write-Host "Note: New apps may appear over time. This resets the current layout." -ForegroundColor Yellow
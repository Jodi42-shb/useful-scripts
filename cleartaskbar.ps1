# Remove-StartMenuPinnedApps.ps1
# Removes all pinned apps from the Start Menu

# Requires elevated privileges on some systems
# Run in PowerShell as Administrator if needed

$registryPath = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Taskband"
$pinnedAppsKey = "Favorites"

# Check if the key exists
if (Test-Path $registryPath) {
    try {
        # Remove the Favorites (pinned apps) registry value
        Remove-ItemProperty -Path $registryPath -Name $pinnedAppsKey -ErrorAction SilentlyContinue
        
        Write-Host "Pinned apps removed from Start Menu." -ForegroundColor Green
        
        # Prompt user to restart Explorer to apply changes
        $restart = Read-Host "Restart Windows Explorer to apply changes now? (Y/N)"
        if ($restart -match "^[Yy]$") {
            Get-Process explorer | Stop-Process
            Write-Host "Windows Explorer restarted." -ForegroundColor Green
        } else {
            Write-Host "Changes will appear after restarting Explorer manually." -ForegroundColor Yellow
        }
    }
    catch {
        Write-Error "Failed to remove pinned apps: $_"
    }
} else {
    Write-Warning "Registry path not found. Start menu pinning data may be in a different location."
}
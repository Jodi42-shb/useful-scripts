# Windows Full Context Menu Enabler
# Checks Windows version, applies registry changes, and offers revert option

# Check if running on Windows 10 (unsupported)
if ([System.Environment]::OSVersion.Version.Build -lt 22000) {
    Write-Warning "This script is designed for Windows 11 only. Windows 10 detected - no changes needed."
    exit
}

# Determine current state
$regPath = "HKCU:\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"
$isEnabled = Test-Path $regPath

# Display current status
Write-Host "Current Status:" -ForegroundColor Cyan
if ($isEnabled) {
    Write-Host "Full context menu is ENABLED" -ForegroundColor Green
} else {
    Write-Host "Full context menu is DISABLED (using default Windows 11 simplified menu)" -ForegroundColor Yellow
}

# Prompt user for action
Write-Host "`nSelect an option:" -ForegroundColor Cyan
Write-Host "1. Enable full context menu (default)" -ForegroundColor Green
Write-Host "2. Revert to Windows 11 simplified menu" -ForegroundColor Yellow
Write-Host "3. Exit without changes" -ForegroundColor Gray

$choice = Read-Host "`nEnter your choice (1-3)"

switch ($choice) {
    "1" {
        # Enable full context menu
        if (-not $isEnabled) {
            New-Item -Path $regPath -Force | Out-Null
            Set-ItemProperty -Path $regPath -Name "(default)" -Value "" -Force
            Write-Host "`nFull context menu ENABLED successfully!" -ForegroundColor Green
        } else {
            Write-Host "`nFull context menu is already enabled." -ForegroundColor Yellow
        }
    }
    "2" {
        # Revert to simplified menu
        if ($isEnabled) {
            Remove-Item -Path "HKCU:\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}" -Recurse -Force
            Write-Host "`nReverted to Windows 11 simplified menu." -ForegroundColor Yellow
        } else {
            Write-Host "`nAlready using the simplified menu." -ForegroundColor Yellow
        }
    }
    "3" {
        Write-Host "`nNo changes made. Exiting..." -ForegroundColor Gray
        exit
    }
    default {
        Write-Host "`nInvalid choice. Exiting..." -ForegroundColor Red
        exit
    }
}

# Restart Explorer process to apply changes
Write-Host "`nRestarting Windows Explorer to apply changes..." -ForegroundColor Cyan
Stop-Process -Name "explorer" -Force
Start-Sleep -Seconds 2
Start-Process -FilePath "explorer.exe"

Write-Host "Complete! Changes applied." -ForegroundColor Green

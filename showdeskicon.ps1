# Requires elevated privileges (Run as Administrator)
# This script enables common desktop icons: This PC, User's Files, Network, Recycle Bin, Control Panel

Write-Host "Enabling desktop icons via registry..." -ForegroundColor Green

# Define registry path for desktop icon settings
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\HideDesktopIcons\NewStartPanel"

# Create the registry path if it doesn't exist
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force | Out-Null
}

# GUIDs for desktop icons
$icons = @{
    "ThisPC"       = "{20D04FE0-3AEA-1069-A2D8-08002B30309D}"
    "UsersFiles"   = "{59031a47-3f72-44a7-89c5-5595fe6b30ee}"
    "Network"      = "{F02C1A0D-BE21-4350-88B0-7367FC96EF3C}"
    "RecycleBin"   = "{645FF040-5081-101B-9F08-00AA002F954E}"
    "ControlPanel" = "{5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0}"
}

# Set each icon to visible (value = 0)
foreach ($icon in $icons.GetEnumerator()) {
    Set-ItemProperty -Path $regPath -Name $icon.Value -Value 0 -Type DWord
    Write-Host "Enabled: $($icon.Key)" -ForegroundColor Yellow
}

# Restart Explorer to apply changes
Write-Host "Restarting Windows Explorer..." -ForegroundColor Cyan
Stop-Process -Name explorer -Force

Write-Host "Done! Desktop icons should now be visible." -ForegroundColor Green
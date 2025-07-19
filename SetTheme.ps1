# settheme.ps1
# Script to set Windows and App theme modes to Light, Dark, or Custom combinations
# Includes workarounds for taskbar color sync issues in Windows 11

# Function to set Windows and App theme modes
function Set-Theme {
    param (
        [string]$WindowsTheme,
        [string]$AppTheme
    )

    # Define registry path
    $registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"

    # Set Windows theme (SystemUsesLightTheme: 1 = Light, 0 = Dark)
    if ($WindowsTheme -eq "Light") {
        Set-ItemProperty -Path $registryPath -Name "SystemUsesLightTheme" -Value 1
    } elseif ($WindowsTheme -eq "Dark") {
        Set-ItemProperty -Path $registryPath -Name "SystemUsesLightTheme" -Value 0
    }

    # Set App theme (AppsUseLightTheme: 1 = Light, 0 = Dark)
    if ($AppTheme -eq "Light") {
        Set-ItemProperty -Path $registryPath -Name "AppsUseLightTheme" -Value 1
    } elseif ($AppTheme -eq "Dark") {
        Set-ItemProperty -Path $registryPath -Name "AppsUseLightTheme" -Value 0
    }

    # Enable accent color on Start, Taskbar, and Action Center (ColorPrevalence: 1 = Enabled)
    Set-ItemProperty -Path $registryPath -Name "ColorPrevalence" -Value 1

    # Optional: Set a default accent color to ensure taskbar color updates (e.g., dark gray: ff262626)
    $accentPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Accent"
    if (-not (Test-Path $accentPath)) {
        New-Item -Path $accentPath -Force | Out-Null
    }
    Set-ItemProperty -Path $accentPath -Name "AccentColor" -Value 0xff262626
    Set-ItemProperty -Path $accentPath -Name "AccentColorInactive" -Value 0xff262626

    # Restart Windows Explorer to force theme refresh
    Stop-Process -Name "explorer" -Force
    Start-Sleep -Seconds 2
    Start-Process "explorer"
}

# Prompt user for theme choice
Write-Host "Choose a theme mode:"
Write-Host "1. Light (Windows: Light, Apps: Light)"
Write-Host "2. Dark (Windows: Dark, Apps: Dark)"
Write-Host "3. Custom (Choose Windows and App themes separately)"
$choice = Read-Host "Enter 1, 2, or 3"

# Process user choice
switch ($choice) {
    "1" {
        Set-Theme -WindowsTheme "Light" -AppTheme "Light"
        Write-Host "Set to Light mode (Windows: Light, Apps: Light)"
    }
    "2" {
        Set-Theme -WindowsTheme "Dark" -AppTheme "Dark"
        Write-Host "Set to Dark mode (Windows: Dark, Apps: Dark)"
    }
    "3" {
        # Custom mode: prompt for individual settings
        Write-Host "Select Windows theme:"
        Write-Host "1. Light"
        Write-Host "2. Dark"
        $windowsChoice = Read-Host "Enter 1 or 2"
        $windowsTheme = if ($windowsChoice -eq "1") { "Light" } else { "Dark" }

        Write-Host "Select App theme:"
        Write-Host "1. Light"
        Write-Host "2. Dark"
        $appChoice = Read-Host "Enter 1 or 2"
        $appTheme = if ($appChoice -eq "1") { "Light" } else { "Dark" }

        Set-Theme -WindowsTheme $windowsTheme -AppTheme $appTheme
        Write-Host "Set to Custom mode (Windows: $windowsTheme, Apps: $appTheme)"
    }
    default {
        Write-Host "Invalid choice. Please run the script again and select 1, 2, or 3."
        exit
    }
}

# Additional workaround: Disable and re-enable Transparency effects to refresh taskbar
$transparencyPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
Set-ItemProperty -Path $transparencyPath -Name "EnableTransparency" -Value 0
Start-Sleep -Seconds 1
Set-ItemProperty -Path $transparencyPath -Name "EnableTransparency" -Value 1

# Suggest reboot if issues persist
Write-Host "Theme applied. If the taskbar color doesn't update, try rebooting your system."
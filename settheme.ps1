#!/usr/bin/env pwsh

# Windows Theme Switcher Script
# Author: AI Assistant
# Description: Interactive script to switch between light/dark themes for Windows and apps

function Show-Menu {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "       Windows Theme Switcher" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Select a theme option:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Light Mode (Windows + Apps)" -ForegroundColor Green
    Write-Host "2. Dark Mode (Windows + Apps)" -ForegroundColor Blue
    Write-Host "3. Custom: Windows Light + Apps Dark" -ForegroundColor Magenta
    Write-Host "4. Custom: Windows Dark + Apps Light" -ForegroundColor Magenta
    Write-Host "5. Current Theme Status" -ForegroundColor Gray
    Write-Host "6. Exit" -ForegroundColor Red
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
}

function Set-WindowsTheme {
    param (
        [int]$WindowsTheme,
        [int]$AppTheme
    )

    $path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"

    # Check if the registry path exists
    if (-not (Test-Path $path)) {
        Write-Host "Registry path not found. Creating..." -ForegroundColor Yellow
        New-Item -Path $path -Force | Out-Null
    }

    # Set Windows system theme
    Set-ItemProperty -Path $path -Name "SystemUsesLightTheme" -Value $WindowsTheme -ErrorAction Stop

    # Set App theme
    Set-ItemProperty -Path $path -Name "AppsUseLightTheme" -Value $AppTheme -ErrorAction Stop

    Write-Host "✓ Theme applied successfully!" -ForegroundColor Green

    # Show what was set
    $windowsMode = if ($WindowsTheme -eq 1) { "Light" } else { "Dark" }
    $appMode = if ($AppTheme -eq 1) { "Light" } else { "Dark" }
    Write-Host "  Windows Mode: $windowsMode" -ForegroundColor White
    Write-Host "  App Mode: $appMode" -ForegroundColor White
}

function Get-CurrentTheme {
    $path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    
    if (Test-Path $path) {
        $windowsTheme = Get-ItemProperty -Path $path -Name "SystemUsesLightTheme" -ErrorAction SilentlyContinue
        $appTheme = Get-ItemProperty -Path $path -Name "AppsUseLightTheme" -ErrorAction SilentlyContinue
        
        $windowsMode = if ($windowsTheme.SystemUsesLightTheme -eq 1) { "Light" } else { "Dark" }
        $appMode = if ($appTheme.AppsUseLightTheme -eq 1) { "Light" } else { "Dark" }
        
        Write-Host "Current Theme Status:" -ForegroundColor Yellow
        Write-Host "  Windows Mode: $windowsMode" -ForegroundColor White
        Write-Host "  App Mode: $appMode" -ForegroundColor White
    } else {
        Write-Host "Theme registry path not found." -ForegroundColor Red
    }
}

# Main script execution
do {
    Show-Menu
    $choice = Read-Host "Enter your choice (1-6)"
    
    switch ($choice) {
        "1" {
            Write-Host "Setting Light Mode (Windows + Apps)..." -ForegroundColor Green
            Set-WindowsTheme -WindowsTheme 1 -AppTheme 1
            Write-Host "Press any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        "2" {
            Write-Host "Setting Dark Mode (Windows + Apps)..." -ForegroundColor Blue
            Set-WindowsTheme -WindowsTheme 0 -AppTheme 0
            Write-Host "Press any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        "3" {
            Write-Host "Setting Custom: Windows Light + Apps Dark..." -ForegroundColor Magenta
            Set-WindowsTheme -WindowsTheme 1 -AppTheme 0
            Write-Host "Press any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        "4" {
            Write-Host "Setting Custom: Windows Dark + Apps Light..." -ForegroundColor Magenta
            Set-WindowsTheme -WindowsTheme 0 -AppTheme 1
            Write-Host "Press any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        "5" {
            Get-CurrentTheme
            Write-Host "Press any key to continue..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        "6" {
            Write-Host "Goodbye!" -ForegroundColor Green
            break
        }
        default {
            Write-Host "Invalid choice. Please select 1-6." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
} while ($choice -ne "6")

# Clean-PythonAndWindowsTemp.ps1
# Cleans Python cache clutter and common Windows temp files to save space

param(
    [string]$TargetDir = (Get-Location).Path,
    [switch]$NoRecycleBin
)

Write-Host "Cleaning Python cache files and folders in: $TargetDir" -ForegroundColor Cyan

# Remove __pycache__ folders
Get-ChildItem -Path $TargetDir -Recurse -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq '__pycache__' } |
    ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Deleted: $($_.FullName)" -ForegroundColor Yellow
    }

# Remove .pyc and .pyo files
Get-ChildItem -Path $TargetDir -Recurse -Include *.pyc,*.pyo -File -Force -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
        Write-Host "Deleted: $($_.FullName)" -ForegroundColor Yellow
    }

Write-Host "\nCleaning Windows temp files..." -ForegroundColor Cyan

# User temp
$UserTemp = $env:TEMP
if (Test-Path $UserTemp) {
    Get-ChildItem -Path $UserTemp -Recurse -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Cleaned: $UserTemp" -ForegroundColor Yellow
}

# System temp
$SystemTemp = $env:windir + '\\Temp'
if (Test-Path $SystemTemp) {
    Get-ChildItem -Path $SystemTemp -Recurse -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Cleaned: $SystemTemp" -ForegroundColor Yellow
}

# Windows Prefetch
$Prefetch = "$env:windir\Prefetch"
if (Test-Path $Prefetch) {
    Get-ChildItem -Path $Prefetch -Force -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "Cleaned: $Prefetch" -ForegroundColor Yellow
}

# Recent files
$Recent = "$env:APPDATA\Microsoft\Windows\Recent"
if (Test-Path $Recent) {
    Get-ChildItem -Path $Recent -Force -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "Cleaned: $Recent" -ForegroundColor Yellow
}

# Aggressive AppData cleaning
Write-Host "\nAggressively cleaning AppData caches..." -ForegroundColor Cyan

# Define additional AppData cache locations
$AppDataPaths = @(
    "$env:LOCALAPPDATA\Microsoft\Windows\INetCache",
    "$env:LOCALAPPDATA\Microsoft\Windows\INetCookies",
    "$env:LOCALAPPDATA\CrashDumps",
    "$env:LOCALAPPDATA\D3DSCache",
    "$env:LOCALAPPDATA\Microsoft\Windows\WER",
    "$env:LOCALAPPDATA\Packages",
    "$env:LOCALAPPDATA\Temp",
    "$env:APPDATA\Local\Temp"
)

foreach ($path in $AppDataPaths) {
    if (Test-Path $path) {
        try {
            Get-ChildItem -Path $path -Recurse -Force -ErrorAction SilentlyContinue |
                Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "Cleaned: $path" -ForegroundColor Yellow
        } catch {
            Write-Host "Could not clean: $path" -ForegroundColor Red
        }
    }
}

# Clean pip cache specifically
$pipCache = "$env:LOCALAPPDATA\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\Local\pip\cache"
if (Test-Path $pipCache) {
    try {
        Get-ChildItem -Path $pipCache -Recurse -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Cleaned pip cache: $pipCache" -ForegroundColor Yellow
    } catch {
        Write-Host "Could not clean pip cache: $pipCache" -ForegroundColor Red
    }
}

# Empty Recycle Bin (optional)
if (-not $NoRecycleBin) {
    try {
        Write-Host "\nEmptying Recycle Bin..." -ForegroundColor Cyan
        Clear-RecycleBin -Force -ErrorAction SilentlyContinue
        Write-Host "Recycle Bin emptied." -ForegroundColor Yellow
    } catch {
        Write-Host "Could not empty Recycle Bin. Try running as administrator." -ForegroundColor Red
    }
}

Write-Host "\nCleanup complete!" -ForegroundColor Green 
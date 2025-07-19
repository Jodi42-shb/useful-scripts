#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Batch organizes multiple manga series into Mihon local library structure

.DESCRIPTION
    This script processes all folders in a source directory and organizes them into 
    the Mihon local library structure, creating a separate series folder for each.

.PARAMETER SourcePath
    The path containing the manga folders to organize

.PARAMETER DestinationPath
    The destination path where the organized structure will be created

.EXAMPLE
    .\Organize-All-Manga.ps1 -SourcePath "C:\Users\srija\OneDrive - MSFT\Porn\Porn Manga" -DestinationPath "C:\Users\srija\MihonLibrary"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$SourcePath,
    
    [Parameter(Mandatory=$true)]
    [string]$DestinationPath
)

# Import the main organization script
$scriptPath = Join-Path $PSScriptRoot "Organize-MihonLibrary.ps1"
if (-not (Test-Path $scriptPath)) {
    Write-Error "Main organization script not found at: $scriptPath"
    Write-Host "Make sure 'Organize-MihonLibrary.ps1' is in the same directory as this script."
    exit 1
}

Write-Host "Starting batch organization of manga collection..." -ForegroundColor Cyan
Write-Host "Source: $SourcePath" -ForegroundColor White
Write-Host "Destination: $DestinationPath" -ForegroundColor White

# Get all directories in the source path
$mangaFolders = Get-ChildItem -Path $SourcePath -Directory

if ($mangaFolders.Count -eq 0) {
    Write-Warning "No directories found in source path: $SourcePath"
    exit 1
}

Write-Host "Found $($mangaFolders.Count) manga series to organize" -ForegroundColor Green

# Ask user for confirmation
$response = Read-Host "Do you want to proceed with organizing all series? (y/n)"
if ($response -ne 'y' -and $response -ne 'Y') {
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    exit 0
}

# Process each folder
$processed = 0
$failed = 0

foreach ($folder in $mangaFolders) {
    try {
        Write-Host ""
        Write-Host "--- Processing: $($folder.Name) ---" -ForegroundColor Cyan
        
        # Call the main organization script
        & $scriptPath -SourcePath $folder.FullName -DestinationPath $DestinationPath -SeriesTitle $folder.Name
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Successfully organized: $($folder.Name)" -ForegroundColor Green
            $processed++
        } else {
            Write-Host "✗ Failed to organize: $($folder.Name)" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Error "Error processing $($folder.Name): $_"
        $failed++
    }
}

Write-Host ""
Write-Host "=== Batch Organization Complete ===" -ForegroundColor Cyan
Write-Host "Successfully processed: $processed series" -ForegroundColor Green
Write-Host "Failed: $failed series" -ForegroundColor Red
Write-Host "Total series: $($mangaFolders.Count)" -ForegroundColor White

if ($processed -gt 0) {
    $libraryPath = Join-Path $DestinationPath 'local'
    Write-Host ""
    Write-Host "Organized library location: $libraryPath" -ForegroundColor Green
}

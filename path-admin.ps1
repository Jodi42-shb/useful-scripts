# Add-PathsToSystemPath.ps1
# Script to add multiple paths to the System PATH environment variable

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrative privileges. Attempting to relaunch as Administrator..."
    $scriptPath = $PSCommandPath
    $workingDir = Split-Path -Parent $scriptPath
    try {
        Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" -WorkingDirectory $workingDir
        exit
    }
    catch {
        Write-Error "Failed to relaunch script as Administrator: $_"
        exit 1
    }
}

# Function to check if a path already exists in System PATH
function Test-PathInSystemPath {
    param ([string]$PathToCheck)
    $currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine)
    return $currentPath -split ";" -contains $PathToCheck
}

# Function to validate if a path exists on the filesystem
function Test-ValidPath {
    param ([string]$PathToTest)
    return Test-Path $PathToTest
}

# Initialize array to store new paths
$newPaths = @()

# Prompt user to input paths
Write-Host "Enter paths to add to System PATH (one per line). Press Enter without input to finish."
while ($true) {
    $inputPath = Read-Host "Enter path (or press Enter to finish)"
    if ([string]::IsNullOrWhiteSpace($inputPath)) {
        break
    }
    
    # Normalize path (remove trailing backslash and ensure proper format)
    $inputPath = $inputPath.TrimEnd('\')
    
    # Validate path
    if (-not (Test-ValidPath $inputPath)) {
        Write-Warning "Path '$inputPath' does not exist. Skipping."
        continue
    }
    
    # Check for duplicates
    if (Test-PathInSystemPath $inputPath) {
        Write-Warning "Path '$inputPath' is already in System PATH. Skipping."
        continue
    }
    
    $newPaths += $inputPath
}

# If no valid paths were provided, exit
if ($newPaths.Count -eq 0) {
    Write-Host "No new paths to add. Exiting."
    exit
}

# Get current System PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine)

# Append new paths
$newPathString = $currentPath + ";" + ($newPaths -join ";")

# Update System PATH
try {
    [Environment]::SetEnvironmentVariable("Path", $newPathString, [EnvironmentVariableTarget]::Machine)
    Write-Host "Successfully added the following paths to System PATH:"
    $newPaths | ForEach-Object { Write-Host "- $_" }
    Write-Host "Open a new terminal to use the updated PATH."
}
catch {
    Write-Error "Failed to update System PATH: $_"
}
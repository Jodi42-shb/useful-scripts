# Add-PathsToUserPath.ps1
# Script to add multiple paths to the User PATH environment variable

# Function to check if a path already exists in User PATH
function Test-PathInUserPath {
    param ([string]$PathToCheck)
    $currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
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
Write-Host "Enter paths to add to User PATH (one per line). Press Enter without input to finish."
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
    if (Test-PathInUserPath $inputPath) {
        Write-Warning "Path '$inputPath' is already in User PATH. Skipping."
        continue
    }
    
    $newPaths += $inputPath
}

# If no valid paths were provided, exit
if ($newPaths.Count -eq 0) {
    Write-Host "No new paths to add. Exiting."
    exit
}

# Get current User PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)

# Append new paths
$newPathString = $currentPath + ";" + ($newPaths -join ";")

# Update User PATH
try {
    [Environment]::SetEnvironmentVariable("Path", $newPathString, [EnvironmentVariableTarget]::User)
    Write-Host "Successfully added the following paths to User PATH:"
    $newPaths | ForEach-Object { Write-Host "- $_" }
    Write-Host "Open a new terminal to use the updated PATH."
}
catch {
    Write-Error "Failed to update User PATH: $_"
}

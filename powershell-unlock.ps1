<#
This PowerShell script (powershell-unlock.ps1) does the following:

Takes a file path as a required parameter ($Path).
Resolves the full path of the file.
Unblocks the file (removes the "downloaded from the internet" security flag).
Temporarily sets the execution policy to Bypass for the current process, allowing scripts to run regardless of the system policy.
Checks the file extension and:
Runs .ps1 files as PowerShell scripts.
Runs .bat files as batch scripts.
Runs .exe files as executables.
Warns if the file type is unknown.
Restores the original execution policy for the process.
Purpose:
It is designed to safely unblock and execute a script or executable file (PowerShell, batch, or EXE) that may have been downloaded and blocked by Windows, while temporarily relaxing execution policy restrictions for that run.

#>

param (
    [Parameter(Mandatory = $true)]
    [string]$Path
)

# Expand relative path
$fullPath = Resolve-Path -Path $Path

# Unblock the file
Write-Host "Unblocking file: $fullPath"
Unblock-File -Path $fullPath

# Save current policy
$originalPolicy = Get-ExecutionPolicy -Scope Process

# Temporarily bypass execution policy
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Check file extension
$ext = [System.IO.Path]::GetExtension($fullPath)

# Execute based on extension
switch ($ext.ToLower()) {
    ".ps1" {
        Write-Host "Running PowerShell script: $fullPath"
        & powershell -NoProfile -ExecutionPolicy Bypass -File $fullPath
    }
    ".bat" {
        Write-Host "Running batch file: $fullPath"
        & cmd /c "$fullPath"
    }
    ".exe" {
        Write-Host "Running executable: $fullPath"
        & "$fullPath"
    }
    default {
        Write-Warning "Unknown file type: $ext. Skipping execution."
    }
}

# Restore original execution policy (optional)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy $originalPolicy -Force

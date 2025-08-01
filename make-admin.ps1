# RunAsAdmin.ps1
# Script to relaunch the current PowerShell session as Administrator and keep the terminal open

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "This PowerShell session is already running as Administrator."
    Write-Host "You can now use this terminal."
    # Keep the terminal open by starting an interactive session
    Write-Host "Press Ctrl+C to exit or continue using the terminal."
    $host.UI.RawUI.FlushInputBuffer()
    while ($true) {
        # Start an interactive prompt
        $input = Read-Host "PS> "
        if ($input -eq "exit") { break }
        try {
            Invoke-Expression $input
        }
        catch {
            Write-Error "Error executing command: $_"
        }
    }
}
# ...existing code...
else {
    Write-Host "Current session is not running as Administrator. Attempting to relaunch as Administrator..."
    try {
        # Get the current script path or current working directory
        $workingDir = Get-Location | Select-Object -ExpandProperty Path
        # Relaunch PowerShell as Administrator in the same directory using -WindowStyle Hidden to avoid flashing
        Start-Process -FilePath "pwsh.exe" -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -NoExit -Command `"Set-Location -LiteralPath '$workingDir'`""
        exit
    }
    catch {
        Write-Error "Failed to relaunch PowerShell as Administrator: $_"
        exit 1
    }
}
# ...existing code...
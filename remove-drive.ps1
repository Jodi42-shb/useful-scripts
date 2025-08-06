#Requires -RunAsAdministrator

# Function to get processes locking a specific drive
function Get-LockingProcesses {
    param (
        [Parameter(Mandatory=$true)]
        [string]$DriveLetter
    )
    $processes = @()
    $openFiles = & handle.exe -a -u | Select-String "$DriveLetter\:"
    foreach ($line in $openFiles) {
        if ($line -match 'pid:\s+(\d+)\s+type:\s+File\s+.*\s+([^\s]+)$') {
            $pid = $matches[1]
            $processName = $matches[2]
            try {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    $processes += [PSCustomObject]@{
                        PID = $pid
                        ProcessName = $process.Name
                        Path = $process.Path
                    }
                }
            } catch {
                Write-Warning "Could not retrieve details for PID: $pid"
            }
        }
    }
    return $processes
}

# Function to safely eject a drive
function Eject-Drive {
    param (
        [Parameter(Mandatory=$true)]
        [string]$DriveLetter
    )
    $volume = Get-WmiObject -Class Win32_Volume | Where-Object { $_.DriveLetter -eq $DriveLetter }
    if (-not $volume) {
        Write-Error "Drive $DriveLetter not found."
        return $false
    }
    
    $shell = New-Object -ComObject Shell.Application
    $drive = $shell.NameSpace(17).ParseName($DriveLetter + "\")
    if ($drive) {
        try {
            $drive.InvokeVerb("Eject")
            Write-Host "Drive $DriveLetter ejected successfully." -ForegroundColor Green
            return $true
        } catch {
            Write-Error "Failed to eject drive $DriveLetter. Error: $_"
            return $false
        }
    }
    return $false
}

# Main script
Write-Host "Removable Drive Ejection Script" -ForegroundColor Cyan
Write-Host "------------------------------"

# Download handle.exe if not present
$handlePath = "$env:TEMP\handle.exe"
if (-not (Test-Path $handlePath)) {
    Write-Host "Downloading handle.exe from Sysinternals..."
    try {
        Invoke-WebRequest -Uri "https://download.sysinternals.com/files/Handle.zip" -OutFile "$env:TEMP\Handle.zip"
        Expand-Archive -Path "$env:TEMP\Handle.zip" -DestinationPath "$env:TEMP" -Force
    } catch {
        Write-Error "Failed to download handle.exe. Please download it manually from Sysinternals."
        exit 1
    }
}

# Get removable drives
$drives = Get-WmiObject -Class Win32_Volume | Where-Object { $_.DriveType -eq 2 -and $_.DriveLetter } | Select-Object DriveLetter, Label

if (-not $drives) {
    Write-Host "No removable drives detected." -ForegroundColor Yellow
    exit
}

# Display available drives
Write-Host "`nAvailable Removable Drives:"
$driveOptions = @{}
$index = 1
foreach ($drive in $drives) {
    $driveLetter = $drive.DriveLetter
    $label = if ($drive.Label) { $drive.Label } else { "No Label" }
    Write-Host "$index. $driveLetter ($label)"
    $driveOptions[$index] = $driveLetter
    $index++
}

# Prompt user to select a drive
$selection = Read-Host "`nSelect a drive to eject (1-$($drives.Count)) or 'q' to quit"
if ($selection -eq 'q') {
    Write-Host "Exiting script."
    exit
}

if (-not $driveOptions.ContainsKey([int]$selection)) {
    Write-Error "Invalid selection."
    exit
}

$selectedDrive = $driveOptions[[int]$selection]
Write-Host "`nSelected drive: $selectedDrive"

# Check for locking processes
Write-Host "`nChecking for processes using ${selectedDrive}:" -ForegroundColor Yellow
$lockingProcesses = Get-LockingProcesses -DriveLetter $selectedDrive

if ($lockingProcesses.Count -eq 0) {
    Write-Host "No processes are using ${selectedDrive}. Attempting to eject..." -ForegroundColor Green
    if (Eject-Drive -DriveLetter $selectedDrive) {
        exit
    } else {
        Write-Host "Ejection failed. Checking for additional issues..." -ForegroundColor Red
    }
} else {
    Write-Host "`nThe following processes are using ${selectedDrive}:" -ForegroundColor Yellow
    $processOptions = @{}
    $index = 1
    foreach ($proc in $lockingProcesses) {
        Write-Host "$index. $($proc.ProcessName) (PID: $($proc.PID)) - Path: $($proc.Path)"
        $processOptions[$index] = $proc
        $index++
    }

    # Interactive menu for handling locking processes
    while ($true) {
        Write-Host "`nOptions:"
        Write-Host "1. Close selected processes"
        Write-Host "2. Attempt safe ejection"
        Write-Host "3. Force eject (WARNING: May cause data loss)"
        Write-Host "4. Refresh process list"
        Write-Host "5. Exit"
        $choice = Read-Host "Select an option (1-5)"

        switch ($choice) {
            1 {
                # Close selected processes
                $procSelection = Read-Host "Enter process numbers to close (e.g., 1,2,3) or 'all' for all"
                if ($procSelection -eq 'all') {
                    $selectedProcs = $lockingProcesses
                } else {
                    $selectedProcs = $procSelection -split ',' | ForEach-Object { $processOptions[[int]$_ ] }
                }

                foreach ($proc in $selectedProcs) {
                    # Avoid killing critical system processes
                    if ($proc.ProcessName -in @("svchost", "explorer", "System", "csrss", "winlogon")) {
                        Write-Warning "Skipping critical system process: $($proc.ProcessName) (PID: $($proc.PID))"
                        continue
                    }
                    Write-Host "Attempting to close $($proc.ProcessName) (PID: $($proc.PID))..."
                    try {
                        Stop-Process -Id $proc.PID -Force -ErrorAction Stop
                        Write-Host "Closed $($proc.ProcessName)." -ForegroundColor Green
                    } catch {
                        Write-Warning "Failed to close $($proc.ProcessName): $_"
                    }
                }

                # Recheck if drive can be ejected
                Start-Sleep -Seconds 2
                $lockingProcesses = Get-LockingProcesses -DriveLetter $selectedDrive
                if ($lockingProcesses.Count -eq 0) {
                    Write-Host "All locking processes closed. Attempting to eject..." -ForegroundColor Green
                    if (Eject-Drive -DriveLetter $selectedDrive) {
                        exit
                    }
                } else {
                    Write-Host "Some processes still using the drive. Please review updated list." -ForegroundColor Yellow
                }
            }
            2 {
                # Attempt safe ejection
                if (Eject-Drive -DriveLetter $selectedDrive) {
                    exit
                } else {
                    Write-Host "Safe ejection failed. Processes may still be locking the drive." -ForegroundColor Red
                }
            }
            3 {
                # Forceful ejection with confirmation
                $confirm = Read-Host "WARNING: Forceful ejection may cause data loss or corruption. Type 'CONFIRM' to proceed"
                if ($confirm -eq 'CONFIRM') {
                    Write-Host "Attempting forceful ejection..." -ForegroundColor Yellow
                    $volume = Get-WmiObject -Class Win32_Volume | Where-Object { $_.DriveLetter -eq $selectedDrive }
                    if ($volume) {
                        try {
                            $volume.Dismount($true, $false) # Force dismount without permanent removal
                            Write-Host "Drive $selectedDrive forcefully dismounted." -ForegroundColor Green
                            if (Eject-Drive -DriveLetter $selectedDrive) {
                                Write-Host "Drive ejected successfully." -ForegroundColor Green
                                exit
                            } else {
                                Write-Error "Forceful ejection failed."
                            }
                        } catch {
                            Write-Error "Forceful ejection failed: $_"
                        }
                    } else {
                        Write-Error "Drive $selectedDrive not found for dismount."
                    }
                } else {
                    Write-Host "Forceful ejection cancelled." -ForegroundColor Yellow
                }
            }
            4 {
                # Refresh process list
                $lockingProcesses = Get-LockingProcesses -DriveLetter $selectedDrive
                if ($lockingProcesses.Count -eq 0) {
                    Write-Host "No processes are using ${selectedDrive}. Attempting to eject..." -ForegroundColor Green
                    if (Eject-Drive -DriveLetter $selectedDrive) {
                        exit
                    }
                } else {
                    Write-Host "`nUpdated list of processes using ${selectedDrive}:" -ForegroundColor Yellow
                    $processOptions = @{}
                    $index = 1
                    foreach ($proc in $lockingProcesses) {
                        Write-Host "$index. $($proc.ProcessName) (PID: $($proc.PID)) - Path: $($proc.Path)"
                        $processOptions[$index] = $proc
                        $index++
                    }
                }
            }
            5 {
                Write-Host "Exiting script."
                exit
            }
            default {
                Write-Host "Invalid option. Please select 1-5." -ForegroundColor Red
            }
        }
    }
}
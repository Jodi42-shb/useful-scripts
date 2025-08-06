#Requires -RunAsAdministrator

# Function to get processes locking a specific drive
function Get-LockingProcesses {
    param (
        [Parameter(Mandatory=$true)]
        [string]$DriveLetter
    )
    Write-Host "[VERBOSE] Checking for processes locking drive ${DriveLetter}..." -ForegroundColor Cyan
    $processes = @()
    $openFiles = & "$env:TEMP\handle.exe" -a -u | Select-String "$DriveLetter\:"
    Write-Host "[VERBOSE] Found $($openFiles.Count) file handles for ${DriveLetter}." -ForegroundColor Cyan
    foreach ($line in $openFiles) {
        Write-Host "[VERBOSE] Parsing handle: $line" -ForegroundColor Cyan
        if ($line -match 'pid:\s+(\d+)\s+type:\s+File\s+.*\s+([^\s]+)$') {
            $pid = $matches[1]
            $processName = $matches[2]
            Write-Host "[VERBOSE] Found process with PID: $pid, Name: $processName" -ForegroundColor Cyan
            try {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    $processes += [PSCustomObject]@{
                        PID = $pid
                        ProcessName = $process.Name
                        Path = $process.Path
                    }
                    Write-Host "[VERBOSE] Added process $($process.Name) (PID: $pid) to locking processes list." -ForegroundColor Cyan
                } else {
                    Write-Warning "[VERBOSE] Process with PID $pid no longer exists."
                }
            } catch {
                Write-Warning "[VERBOSE] Could not retrieve details for PID: $pid. Error: $_"
            }
        }
    }
    Write-Host "[VERBOSE] Total locking processes found: $($processes.Count)" -ForegroundColor Cyan
    return $processes
}

# Function to safely eject a drive
function Eject-Drive {
    param (
        [Parameter(Mandatory=$true)]
        [string]$DriveLetter
    )
    Write-Host "[VERBOSE] Attempting to eject drive ${DriveLetter}..." -ForegroundColor Cyan
    $volume = Get-CimInstance -ClassName Win32_Volume | Where-Object { $_.DriveLetter -eq $DriveLetter }
    if (-not $volume) {
        Write-Error "[VERBOSE] Drive ${DriveLetter} not found in Win32_Volume."
        return $false
    }
    Write-Host "[VERBOSE] Found volume for ${DriveLetter}: $($volume.Label)" -ForegroundColor Cyan
    
    $shell = New-Object -ComObject Shell.Application
    Write-Host "[VERBOSE] Created Shell.Application COM object." -ForegroundColor Cyan
    $drive = $shell.NameSpace(17).ParseName($DriveLetter + "\")
    if ($drive) {
        Write-Host "[VERBOSE] Invoking 'Eject' verb for drive ${DriveLetter}..." -ForegroundColor Cyan
        try {
            $drive.InvokeVerb("Eject")
            Write-Host "[VERBOSE] Drive ${DriveLetter} ejected successfully." -ForegroundColor Green
            return $true
        } catch {
            Write-Error "[VERBOSE] Failed to eject drive ${DriveLetter}. Error: $_"
            return $false
        }
    } else {
        Write-Error "[VERBOSE] Could not access drive ${DriveLetter} via Shell.Application."
        return $false
    }
}

# Function to check if a drive is USB-connected
function Test-USBDrive {
    param (
        [Parameter(Mandatory=$true)]
        [string]$DriveLetter
    )
    Write-Host "[VERBOSE] Checking if ${DriveLetter} is a USB drive using Win32_DiskDrive..." -ForegroundColor Cyan
    $diskDrives = Get-CimInstance -ClassName Win32_DiskDrive | Where-Object { $_.InterfaceType -eq "USB" }
    foreach ($disk in $diskDrives) {
        Write-Host "[VERBOSE] Evaluating disk: $($disk.Caption), Interface: $($disk.InterfaceType)" -ForegroundColor Cyan
        $partitions = Get-CimInstance -Query "ASSOCIATORS OF {Win32_DiskDrive.DeviceID='$($disk.DeviceID)'} WHERE AssocClass=Win32_DiskDriveToDiskPartition"
        foreach ($partition in $partitions) {
            $logicalDisks = Get-CimInstance -Query "ASSOCIATORS OF {Win32_DiskPartition.DeviceID='$($partition.DeviceID)'} WHERE AssocClass=Win32_LogicalDiskToPartition"
            foreach ($logicalDisk in $logicalDisks) {
                if ($logicalDisk.DeviceID -eq $DriveLetter) {
                    Write-Host "[VERBOSE] ${DriveLetter} is confirmed as a USB drive." -ForegroundColor Cyan
                    return $true
                }
            }
        }
    }
    Write-Host "[VERBOSE] ${DriveLetter} is not a USB drive based on Win32_DiskDrive." -ForegroundColor Cyan
    return $false
}

# Function to get drives from Get-Disk as a fallback
function Get-USBFallbackDrives {
    Write-Host "[VERBOSE] Using Get-Disk as a fallback to detect removable drives..." -ForegroundColor Cyan
    $usbDrives = Get-Disk | Where-Object { $_.BusType -eq "USB" -and $_.IsOffline -eq $false }
    $drives = @()
    foreach ($disk in $usbDrives) {
        Write-Host "[VERBOSE] Found USB disk: $($disk.Number), FriendlyName: $($disk.FriendlyName)" -ForegroundColor Cyan
        $partitions = Get-Partition -DiskNumber $disk.Number
        foreach ($partition in $partitions) {
            $volume = Get-Volume -Partition $partition
            if ($volume -and $volume.DriveLetter) {
                Write-Host "[VERBOSE] Mapped drive letter ${volume.DriveLetter} to USB disk $($disk.Number)" -ForegroundColor Cyan
                $drives += [PSCustomObject]@{
                    DriveLetter = $volume.DriveLetter
                    Label = $volume.FileSystemLabel
                    DriveType = 2 # Treat as removable for consistency
                }
            }
        }
    }
    Write-Host "[VERBOSE] Found $($drives.Count) USB drives via Get-Disk fallback." -ForegroundColor Cyan
    return $drives
}

# Main script
Write-Host "[VERBOSE] Starting Removable Drive Ejection Script" -ForegroundColor Cyan
Write-Host "[VERBOSE] Checking for administrative privileges..." -ForegroundColor Cyan
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "[VERBOSE] Script must be run as Administrator. Exiting."
    exit 1
}
Write-Host "[VERBOSE] Administrative privileges confirmed." -ForegroundColor Cyan

# Download handle.exe if not present
$handlePath = "$env:TEMP\handle.exe"
Write-Host "[VERBOSE] Checking for handle.exe at $handlePath..." -ForegroundColor Cyan
if (-not (Test-Path $handlePath)) {
    Write-Host "[VERBOSE] handle.exe not found. Downloading from Sysinternals..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri "https://download.sysinternals.com/files/Handle.zip" -OutFile "$env:TEMP\Handle.zip"
        Write-Host "[VERBOSE] Downloaded Handle.zip to $env:TEMP\Handle.zip" -ForegroundColor Cyan
        Expand-Archive -Path "$env:TEMP\Handle.zip" -DestinationPath "$env:TEMP" -Force
        Write-Host "[VERBOSE] Extracted handle.exe to $env:TEMP" -ForegroundColor Cyan
    } catch {
        Write-Error "[VERBOSE] Failed to download or extract handle.exe. Error: $_"
        Write-Host "[VERBOSE] Please download handle.exe manually from Sysinternals and place it in $env:TEMP."
        exit 1
    }
} else {
    Write-Host "[VERBOSE] handle.exe already exists at $handlePath." -ForegroundColor Cyan
}

# Get removable and USB-connected drives
Write-Host "[VERBOSE] Querying Win32_Volume for drives using Get-CimInstance..." -ForegroundColor Cyan
$allVolumes = Get-CimInstance -ClassName Win32_Volume | Where-Object { $_.DriveLetter } | Select-Object DriveLetter, Label, DriveType
Write-Host "[VERBOSE] Raw volumes found: $($allVolumes | ForEach-Object { "$($_.DriveLetter) $($_.Label) ($($_.DriveType))" })" -ForegroundColor Cyan
$drives = @()
foreach ($volume in $allVolumes) {
    Write-Host "[VERBOSE] Evaluating drive ${volume.DriveLetter}, Type: ${volume.DriveType}, Label: ${volume.Label}" -ForegroundColor Cyan
    if ($volume.DriveLetter -and ($volume.DriveType -eq 2 -or (Test-USBDrive -DriveLetter $volume.DriveLetter))) {
        $drives += $volume
        Write-Host "[VERBOSE] Added ${volume.DriveLetter} to removable/USB drive list." -ForegroundColor Cyan
    }
}
Write-Host "[VERBOSE] Found $($drives.Count) removable or USB-connected drives via Win32_Volume." -ForegroundColor Cyan

# Fallback to Get-Disk if no drives are found
if (-not $drives) {
    $drives = Get-USBFallbackDrives
    if (-not $drives) {
        Write-Host "[VERBOSE] No removable or USB-connected drives detected. Listing all volumes for debugging..." -ForegroundColor Yellow
        foreach ($volume in $allVolumes) {
            Write-Host "[VERBOSE] Drive: ${volume.DriveLetter}, Label: ${volume.Label}, Type: ${volume.DriveType}" -ForegroundColor Cyan
        }
        Write-Host "[VERBOSE] Listing all disks for debugging..." -ForegroundColor Yellow
        Get-Disk | ForEach-Object {
            Write-Host "[VERBOSE] Disk: $($_.Number), FriendlyName: $($_.FriendlyName), BusType: $($_.BusType), IsOffline: $($_.IsOffline)" -ForegroundColor Cyan
        }
        Write-Host "[VERBOSE] Exiting due to no removable or USB drives." -ForegroundColor Yellow
        exit
    }
}

# Display available drives
Write-Host "`n[VERBOSE] Listing available removable/USB drives:" -ForegroundColor Cyan
$driveOptions = @{}
$index = 1
foreach ($drive in $drives) {
    $driveLetter = $drive.DriveLetter
    $label = if ($drive.Label) { $drive.Label } else { "No Label" }
    $type = if ($drive.DriveType -eq 2) { "Removable" } else { "USB (Fixed)" }
    Write-Host "[VERBOSE] $index. ${driveLetter} ($label, $type)"
    $driveOptions[$index] = $driveLetter
    $index++
}

# Prompt user to select a drive
Write-Host "[VERBOSE] Waiting for user input to select a drive..." -ForegroundColor Cyan
$selection = Read-Host "`nSelect a drive to eject (1-$($drives.Count)) or 'q' to quit"
if ($selection -eq 'q') {
    Write-Host "[VERBOSE] User chose to quit. Exiting script." -ForegroundColor Cyan
    exit
}

if (-not $driveOptions.ContainsKey([int]$selection)) {
    Write-Error "[VERBOSE] Invalid selection: $selection. Must be a number between 1 and $($drives.Count)."
    exit
}

$selectedDrive = $driveOptions[[int]$selection]
Write-Host "[VERBOSE] User selected drive: ${selectedDrive}" -ForegroundColor Cyan

# Check for locking processes
Write-Host "[VERBOSE] Checking for processes locking ${selectedDrive}..." -ForegroundColor Cyan
$lockingProcesses = Get-LockingProcesses -DriveLetter $selectedDrive

if ($lockingProcesses.Count -eq 0) {
    Write-Host "[VERBOSE] No processes are locking ${selectedDrive}. Attempting to eject..." -ForegroundColor Green
    if (Eject-Drive -DriveLetter $selectedDrive) {
        Write-Host "[VERBOSE] Ejection successful. Exiting script." -ForegroundColor Cyan
        exit
    } else {
        Write-Host "[VERBOSE] Ejection failed. Checking for additional issues..." -ForegroundColor Red
    }
} else {
    Write-Host "[VERBOSE] The following processes are locking ${selectedDrive}:" -ForegroundColor Yellow
    $processOptions = @{}
    $index = 1
    foreach ($proc in $lockingProcesses) {
        Write-Host "[VERBOSE] $index. $($proc.ProcessName) (PID: $($proc.PID)) - Path: $($proc.Path)"
        $processOptions[$index] = $proc
        $index++
    }

    # Interactive menu for handling locking processes
    while ($true) {
        Write-Host "`n[VERBOSE] Displaying options menu:" -ForegroundColor Cyan
        Write-Host "1. Close selected processes"
        Write-Host "2. Attempt safe ejection"
        Write-Host "3. Force eject (WARNING: May cause data loss)"
        Write-Host "4. Refresh process list"
        Write-Host "5. Exit"
        Write-Host "[VERBOSE] Waiting for user input..." -ForegroundColor Cyan
        $choice = Read-Host "Select an option (1-5)"

        switch ($choice) {
            1 {
                Write-Host "[VERBOSE] User chose to close selected processes." -ForegroundColor Cyan
                $procSelection = Read-Host "Enter process numbers to close (e.g., 1,2,3) or 'all' for all"
                Write-Host "[VERBOSE] User selected processes: $procSelection" -ForegroundColor Cyan
                if ($procSelection -eq 'all') {
                    $selectedProcs = $lockingProcesses
                    Write-Host "[VERBOSE] User chose to close all processes." -ForegroundColor Cyan
                } else {
                    $selectedProcs = $procSelection -split ',' | ForEach-Object { $processOptions[[int]$_ ] }
                    Write-Host "[VERBOSE] Selected processes: $($selectedProcs.ProcessName -join ', ')" -ForegroundColor Cyan
                }

                foreach ($proc in $selectedProcs) {
                    if ($proc.ProcessName -in @("svchost", "explorer", "System", "csrss", "winlogon")) {
                        Write-Warning "[VERBOSE] Skipping critical system process: $($proc.ProcessName) (PID: $($proc.PID))"
                        continue
                    }
                    Write-Host "[VERBOSE] Attempting to close $($proc.ProcessName) (PID: $($proc.PID))..." -ForegroundColor Cyan
                    try {
                        Stop-Process -Id $proc.PID -Force -ErrorAction Stop
                        Write-Host "[VERBOSE] Closed $($proc.ProcessName) successfully." -ForegroundColor Green
                    } catch {
                        Write-Warning "[VERBOSE] Failed to close $($proc.ProcessName): $_"
                    }
                }

                Write-Host "[VERBOSE] Rechecking for locking processes after closing..." -ForegroundColor Cyan
                Start-Sleep -Seconds 2
                $lockingProcesses = Get-LockingProcesses -DriveLetter $selectedDrive
                if ($lockingProcesses.Count -eq 0) {
                    Write-Host "[VERBOSE] All locking processes closed. Attempting to eject..." -ForegroundColor Green
                    if (Eject-Drive -DriveLetter $selectedDrive) {
                        Write-Host "[VERBOSE] Ejection successful. Exiting script." -ForegroundColor Cyan
                        exit
                    }
                } else {
                    Write-Host "[VERBOSE] Some processes still locking the drive. Updating process list." -ForegroundColor Yellow
                }
            }
            2 {
                Write-Host "[VERBOSE] User chose to attempt safe ejection." -ForegroundColor Cyan
                if (Eject-Drive -DriveLetter $selectedDrive) {
                    Write-Host "[VERBOSE] Safe ejection successful. Exiting script." -ForegroundColor Cyan
                    exit
                } else {
                    Write-Host "[VERBOSE] Safe ejection failed. Processes may still be locking the drive." -ForegroundColor Red
                }
            }
            3 {
                Write-Host "[VERBOSE] User chose forceful ejection." -ForegroundColor Cyan
                $confirm = Read-Host "WARNING: Forceful ejection may cause data loss or corruption. Type 'CONFIRM' to proceed"
                if ($confirm -eq 'CONFIRM') {
                    Write-Host "[VERBOSE] User confirmed forceful ejection. Proceeding..." -ForegroundColor Yellow
                    $volume = Get-CimInstance -ClassName Win32_Volume | Where-Object { $_.DriveLetter -eq $selectedDrive }
                    if ($volume) {
                        Write-Host "[VERBOSE] Found volume for forceful dismount: ${selectedDrive}" -ForegroundColor Cyan
                        try {
                            $volume.Dismount($true, $false) # Force dismount without permanent removal
                            Write-Host "[VERBOSE] Drive ${selectedDrive} forcefully dismounted." -ForegroundColor Green
                            if (Eject-Drive -DriveLetter $selectedDrive) {
                                Write-Host "[VERBOSE] Drive ejected successfully. Exiting script." -ForegroundColor Green
                                exit
                            } else {
                                Write-Error "[VERBOSE] Forceful ejection failed."
                            }
                        } catch {
                            Write-Error "[VERBOSE] Forceful ejection failed: $_"
                        }
                    } else {
                        Write-Error "[VERBOSE] Drive ${selectedDrive} not found for dismount."
                    }
                } else {
                    Write-Host "[VERBOSE] Forceful ejection cancelled by user." -ForegroundColor Yellow
                }
            }
            4 {
                Write-Host "[VERBOSE] User chose to refresh process list." -ForegroundColor Cyan
                $lockingProcesses = Get-LockingProcesses -DriveLetter $selectedDrive
                if ($lockingProcesses.Count -eq 0) {
                    Write-Host "[VERBOSE] No processes are locking ${selectedDrive}. Attempting to eject..." -ForegroundColor Green
                    if (Eject-Drive -DriveLetter $selectedDrive) {
                        Write-Host "[VERBOSE] Ejection successful. Exiting script." -ForegroundColor Cyan
                        exit
                    }
                } else {
                    Write-Host "[VERBOSE] Updated list of processes locking ${selectedDrive}:" -ForegroundColor Yellow
                    $processOptions = @{}
                    $index = 1
                    foreach ($proc in $lockingProcesses) {
                        Write-Host "[VERBOSE] $index. $($proc.ProcessName) (PID: $($proc.PID)) - Path: $($proc.Path)"
                        $processOptions[$index] = $proc
                        $index++
                    }
                }
            }
            5 {
                Write-Host "[VERBOSE] User chose to exit script." -ForegroundColor Cyan
                exit
            }
            default {
                Write-Host "[VERBOSE] Invalid option selected: $choice. Please select 1-5." -ForegroundColor Red
            }
        }
    }
}
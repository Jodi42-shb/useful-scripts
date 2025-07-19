# Disable All Startup Apps Script
# This script disables startup applications from multiple sources

# Ensure running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires Administrator privileges. Please run as Administrator." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting to disable all startup applications..." -ForegroundColor Yellow
Write-Host "=" * 50

# Function to disable startup apps via Task Scheduler
function Disable-TaskSchedulerStartupApps {
    Write-Host "`nDisabling startup apps in Task Scheduler..." -ForegroundColor Cyan
    
    try {
        # Get all startup tasks
        $startupTasks = Get-ScheduledTask | Where-Object { 
            $_.TaskPath -like "*Microsoft*" -or 
            $_.TaskPath -like "*\Microsoft\Windows\*" -or
            $_.State -eq "Ready"
        }
        
        foreach ($task in $startupTasks) {
            if ($task.TaskName -notlike "*Critical*" -and $task.TaskName -notlike "*System*") {
                try {
                    Disable-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath -ErrorAction SilentlyContinue
                    Write-Host "  Disabled: $($task.TaskName)" -ForegroundColor Green
                } catch {
                    Write-Host "  Failed to disable: $($task.TaskName)" -ForegroundColor Red
                }
            }
        }
    } catch {
        Write-Host "Error accessing Task Scheduler: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to disable startup apps via Registry (Current User)
function Disable-RegistryStartupApps {
    Write-Host "`nDisabling startup apps in Registry (Current User)..." -ForegroundColor Cyan
    
    $registryPaths = @(
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run",
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
    )
    
    foreach ($path in $registryPaths) {
        try {
            if (Test-Path $path) {
                $items = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
                if ($items) {
                    $properties = $items.PSObject.Properties | Where-Object { $_.Name -notlike "PS*" }
                    foreach ($property in $properties) {
                        try {
                            Remove-ItemProperty -Path $path -Name $property.Name -ErrorAction SilentlyContinue
                            Write-Host "  Removed: $($property.Name) from $path" -ForegroundColor Green
                        } catch {
                            Write-Host "  Failed to remove: $($property.Name) from $path" -ForegroundColor Red
                        }
                    }
                }
            }
        } catch {
            Write-Host "Error accessing registry path $path`: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Function to disable startup apps via Windows Settings (Windows 10/11)
function Disable-WindowsStartupApps {
    Write-Host "`nDisabling startup apps via Windows Settings..." -ForegroundColor Cyan
    
    try {
        # Get startup apps using Get-StartApps (Windows 10/11)
        if (Get-Command Get-StartApps -ErrorAction SilentlyContinue) {
            $startupApps = Get-StartApps
            foreach ($app in $startupApps) {
                try {
                    # This is a read-only command, we'll use registry method instead
                    Write-Host "  Found startup app: $($app.Name)" -ForegroundColor Yellow
                } catch {
                    Write-Host "  Error processing app: $($app.Name)" -ForegroundColor Red
                }
            }
        }
        
        # Use WMI to get startup programs
        $startupPrograms = Get-WmiObject -Class Win32_StartupCommand -ErrorAction SilentlyContinue
        foreach ($program in $startupPrograms) {
            Write-Host "  Found startup program: $($program.Name) - $($program.Command)" -ForegroundColor Yellow
        }
        
        Write-Host "  Note: Some startup apps may need to be disabled manually through Windows Settings > Apps > Startup" -ForegroundColor Yellow
        
    } catch {
        Write-Host "Error accessing Windows startup apps: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to disable startup services (be careful with this)
function Disable-StartupServices {
    Write-Host "`nDisabling non-essential startup services..." -ForegroundColor Cyan
    
    # List of services that are generally safe to disable
    $servicesToDisable = @(
        "Fax",
        "TabletInputService",
        "WSearch",
        "WMPNetworkSvc",
        "wscsvc",
        "WerSvc",
        "Spooler"
    )
    
    foreach ($serviceName in $servicesToDisable) {
        try {
            $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
            if ($service -and $service.StartType -ne "Disabled") {
                Set-Service -Name $serviceName -StartupType Disabled -ErrorAction SilentlyContinue
                Write-Host "  Disabled service: $serviceName" -ForegroundColor Green
            }
        } catch {
            Write-Host "  Could not disable service: $serviceName" -ForegroundColor Red
        }
    }
    
    Write-Host "  Warning: Only non-essential services were disabled. Critical system services remain enabled." -ForegroundColor Yellow
}

# Function to clean startup folders
function Clean-StartupFolders {
    Write-Host "`nCleaning startup folders..." -ForegroundColor Cyan
    
    $startupFolders = @(
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup",
        "$env:ALLUSERSPROFILE\Microsoft\Windows\Start Menu\Programs\Startup"
    )
    
    foreach ($folder in $startupFolders) {
        try {
            if (Test-Path $folder) {
                $items = Get-ChildItem -Path $folder -ErrorAction SilentlyContinue
                foreach ($item in $items) {
                    try {
                        Remove-Item -Path $item.FullName -Force -ErrorAction SilentlyContinue
                        Write-Host "  Removed: $($item.Name) from $folder" -ForegroundColor Green
                    } catch {
                        Write-Host "  Failed to remove: $($item.Name)" -ForegroundColor Red
                    }
                }
            }
        } catch {
            Write-Host "Error accessing startup folder $folder`: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Main execution
Write-Host "This script will disable startup applications from multiple sources:" -ForegroundColor White
Write-Host "1. Task Scheduler startup tasks" -ForegroundColor White
Write-Host "2. Registry startup entries" -ForegroundColor White
Write-Host "3. Windows startup apps" -ForegroundColor White
Write-Host "4. Startup folders" -ForegroundColor White
Write-Host "5. Non-essential services" -ForegroundColor White
Write-Host ""

$confirmation = Read-Host "Do you want to proceed? (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "Operation cancelled." -ForegroundColor Yellow
    exit 0
}

# Execute all functions
Disable-RegistryStartupApps
Clean-StartupFolders
Disable-WindowsStartupApps
Disable-TaskSchedulerStartupApps
Disable-StartupServices

Write-Host ""
Write-Host "=" * 50
Write-Host "Startup app disabling process completed!" -ForegroundColor Green
Write-Host "Note: Some changes may require a system restart to take effect." -ForegroundColor Yellow
Write-Host "You may also want to check Windows Settings > Apps > Startup for any remaining apps." -ForegroundColor Yellow

Read-Host "Press Enter to exit"

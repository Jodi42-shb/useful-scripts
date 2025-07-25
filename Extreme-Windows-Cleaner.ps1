# Extreme-Windows-Cleaner.ps1
# WARNING: This script performs EXTREMELY AGGRESSIVE cleaning of Windows clutter, caches, logs, and temp files.
# Use at your own risk! You may lose troubleshooting data, app logins, and some system restore points.
# Run as Administrator for best results.

param(
    [switch]$NoRecycleBin
)

function Safe-Remove {
    param([string]$Path)
    if (Test-Path $Path) {
        try {
            Get-ChildItem -Path $Path -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "Cleaned: $Path" -ForegroundColor Yellow
        } catch {
            Write-Host "Could not clean: $Path" -ForegroundColor Red
        }
    }
}

Write-Host "\n==== EXTREME WINDOWS CLEANER ====" -ForegroundColor Magenta
Write-Host "This script will aggressively clean system and user clutter. Proceed with caution!" -ForegroundColor Red

# 1. Python cache
Write-Host "\nCleaning Python cache..." -ForegroundColor Cyan
Get-ChildItem -Path (Get-Location).Path -Recurse -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq '__pycache__' } |
    ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue; Write-Host "Deleted: $($_.FullName)" -ForegroundColor Yellow }
Get-ChildItem -Path (Get-Location).Path -Recurse -Include *.pyc,*.pyo -File -Force -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue; Write-Host "Deleted: $($_.FullName)" -ForegroundColor Yellow }

# 2. System temp and user temp
Write-Host "\nCleaning temp folders..." -ForegroundColor Cyan
Safe-Remove $env:TEMP
Safe-Remove "$env:windir\Temp"
Safe-Remove "$env:LOCALAPPDATA\Temp"
Safe-Remove "$env:APPDATA\Local\Temp"

# 3. Windows Update cache
Write-Host "\nCleaning Windows Update cache..." -ForegroundColor Cyan
Safe-Remove "$env:windir\SoftwareDistribution\Download"

# 4. Windows Event Logs
Write-Host "\nClearing Windows Event Logs..." -ForegroundColor Cyan
Get-EventLog -LogName * -ErrorAction SilentlyContinue | ForEach-Object { try { Clear-EventLog $_.Log } catch {} }

# 5. Windows Error Reporting
Write-Host "\nCleaning Windows Error Reporting..." -ForegroundColor Cyan
Safe-Remove "$env:ProgramData\Microsoft\Windows\WER"

# 6. Crash dumps
Write-Host "\nCleaning crash dumps..." -ForegroundColor Cyan
Safe-Remove "$env:windir\Minidump"
Safe-Remove "$env:windir\MEMORY.DMP"
Safe-Remove "$env:LOCALAPPDATA\CrashDumps"

# 7. Prefetch
Write-Host "\nCleaning Prefetch..." -ForegroundColor Cyan
Safe-Remove "$env:windir\Prefetch"

# 8. Recent files
Write-Host "\nCleaning Recent files..." -ForegroundColor Cyan
Safe-Remove "$env:APPDATA\Microsoft\Windows\Recent"

# 9. BranchCache
Write-Host "\nFlushing BranchCache..." -ForegroundColor Cyan
try { netsh branchcache flush | Out-Null; Write-Host "BranchCache flushed." -ForegroundColor Yellow } catch {}

# 10. DirectX shader cache
Write-Host "\nCleaning DirectX shader cache..." -ForegroundColor Cyan
Safe-Remove "$env:LOCALAPPDATA\D3DSCache"

# 11. System log files
Write-Host "\nCleaning system log files..." -ForegroundColor Cyan
Safe-Remove "$env:windir\Logs"

# 12. Device driver cache
Write-Host "\nCleaning device driver cache..." -ForegroundColor Cyan
Safe-Remove "$env:windir\System32\DriverStore\FileRepository"

# 13. OneDrive cache
Write-Host "\nCleaning OneDrive cache..." -ForegroundColor Cyan
Safe-Remove "$env:LOCALAPPDATA\Microsoft\OneDrive\settings\Business1"

# 14. Windows Store cache
Write-Host "\nCleaning Windows Store cache..." -ForegroundColor Cyan
Safe-Remove "$env:LOCALAPPDATA\Packages"

# 15. Orphaned MSI installers
Write-Host "\nCleaning orphaned MSI installers..." -ForegroundColor Cyan
Safe-Remove "$env:windir\Installer"

# 16. Old Windows installations
Write-Host "\nCleaning old Windows installations..." -ForegroundColor Cyan
Safe-Remove "$env:SystemDrive\Windows.old"

# 17. Browser caches
Write-Host "\nCleaning browser caches..." -ForegroundColor Cyan
# Edge
Safe-Remove "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"
# Chrome
Safe-Remove "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
# Firefox
Safe-Remove "$env:APPDATA\Mozilla\Firefox\Profiles"

# 18. Duplicate files in Downloads (by name pattern)
Write-Host "\nCleaning duplicate files in Downloads..." -ForegroundColor Cyan
$downloads = "$env:USERPROFILE\Downloads"
if (Test-Path $downloads) {
    Get-ChildItem -Path $downloads -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "\([0-9]+\)" } |
        ForEach-Object {
            $file = $_.FullName
            $response = Read-Host "Send duplicate to Recycle Bin? $file [Y/N]"
            if ($response -match '^(Y|y)') {
                try {
                    # Use Shell.Application to send to Recycle Bin
                    $shell = New-Object -ComObject Shell.Application
                    $folder = Split-Path $file
                    $item = $shell.Namespace($folder).ParseName((Split-Path $file -Leaf))
                    $item.InvokeVerb('delete')
                    Write-Host "Sent to Recycle Bin: $file" -ForegroundColor Yellow
                } catch {
                    Write-Host "Could not send to Recycle Bin: $file" -ForegroundColor Red
                }
            } else {
                Write-Host "Skipped: $file" -ForegroundColor Gray
            }
        }
}

# 18b. Hash-based duplicate detection in Downloads
Write-Host "\nHash-based duplicate detection in Downloads..." -ForegroundColor Cyan
if (Test-Path $downloads) {
    $hashTable = @{}
    Get-ChildItem -Path $downloads -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
            if ($hashTable.ContainsKey($hash)) {
                $hashTable[$hash] += $_.FullName
            } else {
                $hashTable[$hash] = @($_.FullName)
            }
        } catch {}
    }
    foreach ($hash in $hashTable.Keys) {
        $files = $hashTable[$hash]
        if ($files.Count -gt 1) {
            # Keep the first file, prompt for the rest
            $keep = $files[0]
            Write-Host "Keeping: $keep" -ForegroundColor Green
            foreach ($dup in $files[1..($files.Count-1)]) {
                $response = Read-Host "Hash duplicate found. Send to Recycle Bin? $dup [Y/N]"
                if ($response -match '^(Y|y)') {
                    try {
                        $shell = New-Object -ComObject Shell.Application
                        $folder = Split-Path $dup
                        $item = $shell.Namespace($folder).ParseName((Split-Path $dup -Leaf))
                        $item.InvokeVerb('delete')
                        Write-Host "Sent to Recycle Bin: $dup" -ForegroundColor Yellow
                    } catch {
                        Write-Host "Could not send to Recycle Bin: $dup" -ForegroundColor Red
                    }
                } else {
                    Write-Host "Skipped: $dup" -ForegroundColor Gray
                }
            }
        }
    }
}

# 19. CryptNet SSL cache
Write-Host "\nClearing CryptNet SSL cache..." -ForegroundColor Cyan
try { certutil -URLcache * delete | Out-Null; Write-Host "CryptNet SSL cache cleared." -ForegroundColor Yellow } catch {}

# 20. Flush DNS
Write-Host "\nFlushing DNS cache..." -ForegroundColor Cyan
try { ipconfig /flushdns | Out-Null; Write-Host "DNS cache flushed." -ForegroundColor Yellow } catch {}

# 21. Clear clipboard
Write-Host "\nClearing clipboard..." -ForegroundColor Cyan
try { cmd /c "echo off | clip" | Out-Null; Write-Host "Clipboard cleared." -ForegroundColor Yellow } catch {}

# 22. Clean pip cache (Python Store install)
Write-Host "\nCleaning pip cache..." -ForegroundColor Cyan
$pipCache = "$env:LOCALAPPDATA\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\Local\pip\cache"
Safe-Remove $pipCache

# 23. Empty Recycle Bin (optional)
if (-not $NoRecycleBin) {
    Write-Host "\nEmptying Recycle Bin..." -ForegroundColor Cyan
    try {
        Clear-RecycleBin -Force -ErrorAction SilentlyContinue
        Write-Host "Recycle Bin emptied." -ForegroundColor Yellow
    } catch {
        Write-Host "Could not empty Recycle Bin. Try running as administrator." -ForegroundColor Red
    }
}

Write-Host "\n==== EXTREME CLEANUP COMPLETE! ====" -ForegroundColor Green 
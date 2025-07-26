# Find-Duplicates.ps1
# Interactively find duplicate files by hash and/or filename in a specified folder.

# Prompt for folder
$folder = Read-Host "Enter the full path of the folder to scan for duplicates"
if (-not (Test-Path $folder)) {
    Write-Host "Folder does not exist. Exiting." -ForegroundColor Red
    exit
}

# Prompt for method
Write-Host "Choose duplicate detection method:" -ForegroundColor Cyan
Write-Host "1. Hash (file content)" -ForegroundColor Yellow
Write-Host "2. Filename (name only)" -ForegroundColor Yellow
Write-Host "3. Both" -ForegroundColor Yellow
$method = Read-Host "Enter 1, 2, or 3"

$results = @()

# Ask for post-processing options
Write-Host "`nWhat do you want to do with found duplicates?" -ForegroundColor Cyan
Write-Host "1. Just report (no action)" -ForegroundColor Yellow
Write-Host "2. Move selected duplicates to a directory" -ForegroundColor Yellow
Write-Host "3. Delete selected duplicates (choose Recycle Bin or permanent)" -ForegroundColor Yellow
$postAction = Read-Host "Enter 1, 2, or 3"

$moveDir = $null
$deleteMode = $null
if ($postAction -eq '2') {
    $moveDir = Read-Host "Enter the full path of the directory to move duplicates to"
    if (-not (Test-Path $moveDir)) {
        try {
            New-Item -Path $moveDir -ItemType Directory -Force | Out-Null
            Write-Host "Created directory: $moveDir" -ForegroundColor Green
        } catch {
            Write-Host "Could not create move directory. Exiting." -ForegroundColor Red
            exit
        }
    }
}
if ($postAction -eq '3') {
    Write-Host "Delete mode:" -ForegroundColor Cyan
    Write-Host "1. Send to Recycle Bin" -ForegroundColor Yellow
    Write-Host "2. Permanently delete" -ForegroundColor Yellow
    $deleteMode = Read-Host "Enter 1 or 2"
}

function Move-FileSafe($file, $destDir) {
    try {
        $fileName = Split-Path $file -Leaf
        $dest = Join-Path $destDir $fileName
        
        # Handle filename conflicts
        $counter = 1
        while (Test-Path $dest) {
            $baseName = [System.IO.Path]::GetFileNameWithoutExtension($fileName)
            $extension = [System.IO.Path]::GetExtension($fileName)
            $dest = Join-Path $destDir "$baseName($counter)$extension"
            $counter++
        }
        
        Move-Item -Path $file -Destination $dest -Force
        Write-Host "Moved: $file -> $dest" -ForegroundColor Yellow
    } catch {
        Write-Host "Could not move: $file - $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Delete-FileSafe($file, $toRecycleBin) {
    try {
        if ($toRecycleBin) {
            # Use Shell.Application COM object for Recycle Bin
            $shell = New-Object -ComObject Shell.Application
            $folder = $shell.Namespace((Split-Path $file))
            $item = $folder.ParseName((Split-Path $file -Leaf))
            if ($item) {
                $item.InvokeVerb('delete')
                Write-Host "Sent to Recycle Bin: $file" -ForegroundColor Yellow
            } else {
                Write-Host "Could not find file in shell namespace: $file" -ForegroundColor Red
            }
        } else {
            Remove-Item $file -Force
            Write-Host "Permanently deleted: $file" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Could not delete: $file - $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Handle-DuplicateGroup($files, $groupType, $groupKey) {
    Write-Host "`n$groupType duplicate group ($groupKey):" -ForegroundColor Green
    for ($i = 0; $i -lt $files.Count; $i++) {
        $fileInfo = Get-Item $files[$i] -ErrorAction SilentlyContinue
        if ($fileInfo) {
            $size = if ($fileInfo.Length -gt 1MB) { "{0:N2} MB" -f ($fileInfo.Length / 1MB) } else { "{0:N0} KB" -f ($fileInfo.Length / 1KB) }
            Write-Host ("[{0}] {1} ({2})" -f $i, $files[$i], $size) -ForegroundColor Yellow
        } else {
            Write-Host ("[{0}] {1} (file not accessible)" -f $i, $files[$i]) -ForegroundColor DarkYellow
        }
    }
    
    if ($postAction -eq '1') { return }
    
    $toAct = Read-Host "Enter comma-separated numbers of files to act on (leave blank to skip)"
    if ([string]::IsNullOrWhiteSpace($toAct)) { return }
    
    try {
        $indices = $toAct -split ',' | ForEach-Object { 
            $trimmed = $_.Trim()
            if ($trimmed -match '^\d+$') {
                [int]$trimmed
            }
        } | Where-Object { $_ -ne $null }
        
        foreach ($idx in $indices) {
            if ($idx -ge 0 -and $idx -lt $files.Count) {
                $file = $files[$idx]
                if (Test-Path $file) {
                    if ($postAction -eq '2') {
                        Move-FileSafe $file $moveDir
                    } elseif ($postAction -eq '3') {
                        Delete-FileSafe $file ($deleteMode -eq '1')
                    }
                } else {
                    Write-Host "File no longer exists: $file" -ForegroundColor Red
                }
            } else {
                Write-Host "Invalid index: $idx" -ForegroundColor Red
            }
        }
    } catch {
        Write-Host "Error processing selection: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($method -eq '1' -or $method -eq '3') {
    Write-Host "`n[Hash-based duplicate search]" -ForegroundColor Cyan
    $hashTable = @{}
    $fileCount = 0
    
    Get-ChildItem -Path $folder -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $filePath = $_.FullName
        $fileCount++
        
        if ($fileCount % 100 -eq 0) {
            Write-Host "Processed $fileCount files..." -ForegroundColor DarkGray
        }
        
        try {
            # Skip empty files or files that can't be accessed
            if ($_.Length -eq 0) {
                Write-Host "[INFO] Skipping empty file: $filePath" -ForegroundColor DarkGray
                return
            }
            
            $hashObj = Get-FileHash -Path $filePath -Algorithm SHA256 -ErrorAction Stop
            $hash = $hashObj.Hash
            
            if ([string]::IsNullOrEmpty($hash)) {
                Write-Host "[WARNING] Empty hash returned for: $filePath" -ForegroundColor Red
                return
            }
            
            if ($hashTable.ContainsKey($hash)) {
                # Convert to array if it's not already
                if ($hashTable[$hash] -is [string]) {
                    $hashTable[$hash] = @($hashTable[$hash])
                }
                $hashTable[$hash] += $filePath
            } else {
                $hashTable[$hash] = @($filePath)
            }
            
        } catch [System.UnauthorizedAccessException] {
            Write-Host "[WARNING] Access denied: $filePath" -ForegroundColor Red
        } catch [System.IO.IOException] {
            Write-Host "[WARNING] IO error reading: $filePath - $($_.Exception.Message)" -ForegroundColor Red
        } catch {
            Write-Host "[WARNING] Could not hash: $filePath - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "Hash analysis complete. Found $($hashTable.Keys.Count) unique hashes." -ForegroundColor Green
    
    foreach ($hash in $hashTable.Keys) {
        $files = $hashTable[$hash]
        # Ensure $files is always an array
        if ($files -is [string]) {
            $files = @($files)
        }
        
        if ($files.Count -gt 1) {
            Handle-DuplicateGroup $files 'Hash' $hash.Substring(0, 16)
            $results += [PSCustomObject]@{
                Type = 'Hash'
                Hash = $hash
                Files = ($files -join '; ')
                Count = $files.Count
            }
        }
    }
}

if ($method -eq '2' -or $method -eq '3') {
    Write-Host "`n[Filename-based duplicate search]" -ForegroundColor Cyan
    $nameTable = @{}
    
    Get-ChildItem -Path $folder -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $name = $_.Name.ToLower()  # Case-insensitive comparison
        
        if ($nameTable.ContainsKey($name)) {
            # Convert to array if it's not already
            if ($nameTable[$name] -is [string]) {
                $nameTable[$name] = @($nameTable[$name])
            }
            $nameTable[$name] += $_.FullName
        } else {
            $nameTable[$name] = @($_.FullName)
        }
    }
    
    Write-Host "Filename analysis complete. Found $($nameTable.Keys.Count) unique filenames." -ForegroundColor Green
    
    foreach ($name in $nameTable.Keys) {
        $files = $nameTable[$name]
        # Ensure $files is always an array
        if ($files -is [string]) {
            $files = @($files)
        }
        
        if ($files.Count -gt 1) {
            Handle-DuplicateGroup $files 'Name' $name
            $results += [PSCustomObject]@{
                Type = 'Name'
                Hash = $name
                Files = ($files -join '; ')
                Count = $files.Count
            }
        }
    }
}

# Save results
if ($results.Count -gt 0) {
    $outFile = Join-Path $folder "duplicate_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
    try {
        $results | Export-Csv -Path $outFile -NoTypeInformation -Encoding UTF8
        Write-Host "`nDuplicate report saved to: $outFile" -ForegroundColor Cyan
        Write-Host "Total duplicate groups found: $($results.Count)" -ForegroundColor Green
    } catch {
        Write-Host "`nCould not save report: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "`nNo duplicates found." -ForegroundColor Green
}

Write-Host "`nScript completed." -ForegroundColor Cyan
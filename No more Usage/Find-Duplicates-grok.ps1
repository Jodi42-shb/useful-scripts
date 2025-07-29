# Find-Duplicates.ps1
# Interactively find duplicate files by hash and/or filename in a specified folder.

# Prompt for folder
$folder = Read-Host "Enter the full path of the folder to scan for duplicates"
if (-not (Test-Path $folder -PathType Container)) {
    Write-Host "Folder does not exist or is not a directory. Exiting." -ForegroundColor Red
    exit
}

# Prompt for method, with validation
Write-Host "Choose duplicate detection method:" -ForegroundColor Cyan
Write-Host "1. Hash (file content)" -ForegroundColor Yellow
Write-Host "2. Filename (name only)" -ForegroundColor Yellow
Write-Host "3. Both" -ForegroundColor Yellow
$method = $null
while ($null -eq $method) {
    $inputMethod = Read-Host "Enter 1, 2, or 3"
    if ($inputMethod -in @('1','2','3')) {
        $method = $inputMethod
    } else {
        Write-Host "Invalid input. Please enter 1, 2, or 3." -ForegroundColor Red
    }
}

$results = @()

# Ask for post-processing options, with validation
Write-Host "`nWhat do you want to do with found duplicates?" -ForegroundColor Cyan
Write-Host "1. Just report (no action)" -ForegroundColor Yellow
Write-Host "2. Move selected duplicates to a directory" -ForegroundColor Yellow
Write-Host "3. Delete selected duplicates (choose Recycle Bin or permanent)" -ForegroundColor Yellow
$postAction = $null
while ($null -eq $postAction) {
    $inputAction = Read-Host "Enter 1, 2, or 3"
    if ($inputAction -in @('1','2','3')) {
        $postAction = $inputAction
    } else {
        Write-Host "Invalid input. Please enter 1, 2, or 3." -ForegroundColor Red
    }
}

$moveDir = $null
$deleteMode = $null
if ($postAction -eq '2') {
    $moveDir = Read-Host "Enter the full path of the directory to move duplicates to"
    if (-not (Test-Path $moveDir -PathType Container)) {
        Write-Host "Move directory does not exist or is not a directory. Exiting." -ForegroundColor Red
        exit
    }
    # Verify write permissions
    try {
        $testFile = Join-Path $moveDir "test_$(Get-Date -Format 'yyyyMMdd_HHmmss').tmp"
        New-Item -Path $testFile -ItemType File -ErrorAction Stop | Out-Null
        Remove-Item -Path $testFile -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "Move directory is not writable. Exiting." -ForegroundColor Red
        exit
    }
}
if ($postAction -eq '3') {
    Write-Host "Delete mode:" -ForegroundColor Cyan
    Write-Host "1. Send to Recycle Bin" -ForegroundColor Yellow
    Write-Host "2. Permanently delete" -ForegroundColor Yellow
    $deleteMode = $null
    while ($null -eq $deleteMode) {
        $inputDelete = Read-Host "Enter 1 or 2"
        if ($inputDelete -in @('1','2')) {
            $deleteMode = $inputDelete
        } else {
            Write-Host "Invalid input. Please enter 1 or 2." -ForegroundColor Red
        }
    }
}

function Move-FileSafe($file, $destDir) {
    try {
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file)
        $ext = [System.IO.Path]::GetExtension($file)
        $dest = Join-Path $destDir (Split-Path $file -Leaf)
        $counter = 1
        while (Test-Path $dest) {
            $newName = "{0}_{1:D4}{2}" -f $baseName, $counter, $ext
            $dest = Join-Path $destDir $newName
            $counter++
        }
        Move-Item -LiteralPath $file -Destination $dest -Force -ErrorAction Stop
        Write-Host "Moved: $file -> $dest" -ForegroundColor Yellow
    } catch {
        Write-Host "Could not move: $file ($($_.Exception.Message))" -ForegroundColor Red
    }
}

function Delete-FileSafe($file, $toRecycleBin) {
    try {
        if ($toRecycleBin) {
            $shell = New-Object -ComObject Shell.Application
            $folderPath = Split-Path $file -Parent
            $fileName = Split-Path $file -Leaf
            $folder = $shell.Namespace($folderPath)
            if ($null -eq $folder) {
                Write-Host "[WARNING] Could not access folder: $folderPath" -ForegroundColor Red
                return
            }
            $item = $folder.ParseName($fileName)
            if ($null -eq $item) {
                Write-Host "[WARNING] Could not find file in shell: $file" -ForegroundColor Red
                return
            }
            $item.InvokeVerb('delete')
            Write-Host "Sent to Recycle Bin: $file" -ForegroundColor Yellow
        } else {
            Remove-Item -LiteralPath $file -Force -ErrorAction Stop
            Write-Host "Permanently deleted: $file" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Could not delete: $file ($($_.Exception.Message))" -ForegroundColor Red
    }
}

function Handle-DuplicateGroup($files, $groupType, $groupKey) {
    Write-Host "`n$groupType duplicate group ($groupKey):" -ForegroundColor Green
    for ($i=0; $i -lt $files.Count; $i++) {
        Write-Host ("[{0}] {1}" -f $i, $files[$i]) -ForegroundColor Yellow
    }
    if ($postAction -eq '1') { return }
    $toAct = Read-Host "Enter comma-separated numbers of files to act on (leave blank to skip)"
    if ([string]::IsNullOrWhiteSpace($toAct)) { return }
    $indices = $toAct -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -match '^[0-9]+$' } | ForEach-Object { [int]$_ }
    foreach ($idx in $indices) {
        if ($idx -ge 0 -and $idx -lt $files.Count) {
            $file = $files[$idx]
            if ($postAction -eq '2') {
                Move-FileSafe $file $moveDir
            } elseif ($postAction -eq '3') {
                Delete-FileSafe $file ($deleteMode -eq '1')
            }
        }
    }
}

if ($method -eq '1' -or $method -eq '3') {
    Write-Host "\n[Hash-based duplicate search]" -ForegroundColor Cyan
    $hashTable = @{}
    $files = Get-ChildItem -Path $folder -Recurse -File -ErrorAction SilentlyContinue
    $fileCount = $files.Count
    $current = 0
    foreach ($file in $files) {
        $current++
        Write-Progress -Activity "Computing file hashes" -Status "Processing $current of $fileCount" -PercentComplete (($current / $fileCount) * 100)
        $filePath = $file.FullName
        try {
            # Check if file is accessible and not empty
            if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
                Write-Host "[WARNING] File is inaccessible: $filePath" -ForegroundColor Red
                continue
            }
            if ($file.Length -eq 0) {
                Write-Host "[WARNING] Skipping empty file: $filePath" -ForegroundColor Red
                continue
            }
            # Attempt to open file to ensure it's not locked
            $fileStream = [System.IO.File]::Open($filePath, 'Open', 'Read', 'Read')
            $fileStream.Close()
            $hashObj = Get-FileHash -LiteralPath $filePath -Algorithm SHA256 -ErrorAction Stop
            $hash = $hashObj.Hash
            if ($hashTable.ContainsKey($hash)) {
                $hashTable[$hash] += $filePath
            } else {
                $hashTable[$hash] = @($filePath)
            }
        } catch {
            $errorReason = switch ($_.Exception.HResult) {
                0x80070005 { "Access denied" }
                0x80070020 { "File is locked or in use" }
                default { $_.Exception.Message }
            }
            Write-Host "[WARNING] Could not hash: $filePath - $errorReason" -ForegroundColor Red
        }
    }
    Write-Progress -Activity "Computing file hashes" -Completed
    foreach ($hash in $hashTable.Keys) {
        $files = $hashTable[$hash]
        if ($files.Count -gt 1) {
            Handle-DuplicateGroup $files 'Hash' $hash
            $results += [PSCustomObject]@{Type='Hash'; Key=$hash; Files=($files -join '; ')}
        }
    }
}

if ($method -eq '2' -or $method -eq '3') {
    Write-Host "\n[Filename-based duplicate search]" -ForegroundColor Cyan
    $nameTable = @{}
    Get-ChildItem -Path $folder -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $name = $_.Name
        if ($nameTable.ContainsKey($name)) {
            $nameTable[$name] += $_.FullName
        } else {
            $nameTable[$name] = @($_.FullName)
        }
    }
    foreach ($name in $nameTable.Keys) {
        $files = $nameTable[$name]
        if ($files.Count -gt 1) {
            Handle-DuplicateGroup $files 'Name' $name
            $results += [PSCustomObject]@{Type='Name'; Key=$name; Files=($files -join '; ')}
        }
    }
}

# Save results
if ($results.Count -gt 0) {
    $outFile = Join-Path $folder "duplicate_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
    $results | Export-Csv -Path $outFile -NoTypeInformation -Encoding UTF8NoBOM
    Write-Host "\nDuplicate report saved to: $outFile" -ForegroundColor Cyan
} else {
    Write-Host "\nNo duplicates found." -ForegroundColor Green
}
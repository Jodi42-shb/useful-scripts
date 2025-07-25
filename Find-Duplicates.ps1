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
Write-Host "\nWhat do you want to do with found duplicates?" -ForegroundColor Cyan
Write-Host "1. Just report (no action)" -ForegroundColor Yellow
Write-Host "2. Move selected duplicates to a directory" -ForegroundColor Yellow
Write-Host "3. Delete selected duplicates (choose Recycle Bin or permanent)" -ForegroundColor Yellow
$postAction = Read-Host "Enter 1, 2, or 3"

$moveDir = $null
$deleteMode = $null
if ($postAction -eq '2') {
    $moveDir = Read-Host "Enter the full path of the directory to move duplicates to"
    if (-not (Test-Path $moveDir)) {
        Write-Host "Move directory does not exist. Exiting." -ForegroundColor Red
        exit
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
        $dest = Join-Path $destDir (Split-Path $file -Leaf)
        Move-Item -Path $file -Destination $dest -Force
        Write-Host "Moved: $file -> $dest" -ForegroundColor Yellow
    } catch {
        Write-Host "Could not move: $file" -ForegroundColor Red
    }
}

function Delete-FileSafe($file, $toRecycleBin) {
    try {
        if ($toRecycleBin) {
            $shell = New-Object -ComObject Shell.Application
            $folder = Split-Path $file
            $item = $shell.Namespace($folder).ParseName((Split-Path $file -Leaf))
            $item.InvokeVerb('delete')
            Write-Host "Sent to Recycle Bin: $file" -ForegroundColor Yellow
        } else {
            Remove-Item $file -Force
            Write-Host "Permanently deleted: $file" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Could not delete: $file" -ForegroundColor Red
    }
}

if ($method -eq '1' -or $method -eq '3') {
    Write-Host "\n[Hash-based duplicate search]" -ForegroundColor Cyan
    $hashTable = @{}
    Get-ChildItem -Path $folder -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
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
            Handle-DuplicateGroup $files 'Hash' $hash
            $results += [PSCustomObject]@{Type='Hash'; Hash=$hash; Files=($files -join '; ')}
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
            $results += [PSCustomObject]@{Type='Name'; Hash=$name; Files=($files -join '; ')}
        }
    }
}

# Save results
if ($results.Count -gt 0) {
    $outFile = Join-Path $folder "duplicate_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
    $results | Export-Csv -Path $outFile -NoTypeInformation -Encoding UTF8
    Write-Host "\nDuplicate report saved to: $outFile" -ForegroundColor Cyan
} else {
    Write-Host "\nNo duplicates found." -ForegroundColor Green
} 
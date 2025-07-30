# File Organizer PowerShell Script

function Get-FileTypes {
    @{
        Videos = @(
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.mpeg', '.mpg', '.webm', '.3gp', '.m4v',
            '.ts', '.mts', '.m2ts', '.vob', '.rm', '.rmvb', '.ogv', '.divx', '.xvid', '.f4v', '.mxf',
            '.asf', '.amv', '.drc', '.mng', '.yuv', '.roq', '.nsv', '.bik', '.wtv', '.trp', '.mp2',
            '.mpv', '.mpe', '.mpg4', '.m1v', '.m2v', '.m2p', '.m2t', '.m4p', '.m4b', '.m4r', '.m4u',
            '.m4e', '.mod', '.tod', '.dat', '.dv', '.h264', '.h265', '.hevc', '.avchd', '.vp6', '.vp7',
            '.vp8', '.vp9', '.ogm', '.ogx', '.qt', '.fli', '.flc', '.mve', '.ivf', '.skm', '.evo'
        )
        Audio = @(
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.alac', '.aiff', '.ape', '.amr',
            '.opus', '.ra', '.mid', '.midi', '.mpa', '.mpc', '.wv', '.tta', '.ac3', '.dts', '.au', '.snd',
            '.oga', '.spx', '.caf', '.voc', '.mka', '.m3u', '.pls'
        )
        Images = @(
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg', '.webp', '.avif', '.heic',
            '.heif', '.raw', '.cr2', '.nef', '.orf', '.sr2', '.arw', '.dng', '.ico', '.jfif', '.jpe',
            '.jp2', '.j2k', '.jpf', '.jpx', '.jpm', '.mj2', '.psd', '.ai', '.eps', '.indd', '.cdr'
        )
        Documents = @(
            '.doc', '.docx', '.txt', '.pdf', '.rtf', '.odt', '.xlsx', '.xls', '.xlsm', '.xlsb', '.xltx',
            '.ppt', '.pptx', '.pps', '.ppsx', '.csv', '.tsv', '.tex', '.wpd', '.md', '.log', '.pages',
            '.numbers', '.key', '.odp', '.ods', '.odg', '.odf', '.epub', '.djvu', '.fb2', '.xps'
        )
        Applications = @(
            '.exe', '.msi', '.app', '.bat', '.sh', '.jar', '.apk', '.apkm', '.apks', '.deb', '.rpm',
            '.bin', '.cmd', '.com', '.gadget', '.wsf', '.msu', '.dmg', '.pkg', '.run'
        )
        Archives = @(
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', '.cab', '.arj', '.lzh', '.ace',
            '.uue', '.bz', '.z', '.001', '.jar', '.tgz', '.tbz2', '.lzma', '.lz', '.zst', '.cpio'
        )
        Code = @(
            '.py', '.java', '.c', '.cpp', '.cs', '.js', '.ts', '.html', '.htm', '.css', '.php', '.rb',
            '.dart', '.go', '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.conf', '.log', '.md',
            '.sh', '.bat', '.pl', '.swift', '.kt', '.kts', '.scala', '.rs', '.asm', '.sql', '.db',
            '.sqlite', '.db3', '.db4', '.db5', '.db6', '.db7', '.db8', '.db9', '.db10', '.r', '.m',
            '.mat', '.ipynb', '.jsp', '.asp', '.aspx', '.vue', '.jsx', '.tsx', '.h', '.hpp', '.hxx',
            '.sln', '.vb', '.vbs', '.ps1', '.psm1', '.psd1', '.clj', '.cljs', '.groovy', '.erl', '.ex',
            '.exs', '.lua', '.f90', '.f95', '.for', '.f', '.fs', '.fsi', '.fsx', '.fsscript'
        )
        Ebooks = @(
            '.epub', '.mobi', '.azw', '.azw3', '.cbz', '.cbr', '.pdf', '.fb2', '.djvu', '.lit', '.prc',
            '.ibooks', '.pdb'
        )
        Fonts = @(
            '.ttf', '.otf', '.woff', '.woff2', '.eot', '.fon', '.pfa', '.pfb', '.afm', '.bdf', '.sfd'
        )
    }
}

function Create-Backup {
    param(
        [string]$FolderPath,
        [string]$BackupDir
    )
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = Join-Path $BackupDir "backup_$timestamp.json"
    $fileStructure = @{}

    Get-ChildItem -Path $FolderPath -Recurse -File | ForEach-Object {
        $relPath = $_.FullName.Substring($FolderPath.Length).TrimStart('\','/')
        $fileStructure[$relPath] = $_.FullName
    }

    $fileStructure | ConvertTo-Json -Depth 5 | Set-Content -Path $backupPath -Encoding UTF8
    Write-Host "Backup created at $backupPath"
    return $backupPath
}

function Restore-Backup {
    param(
        [string]$FolderPath,
        [string]$BackupFile
    )
    $fileStructure = Get-Content $BackupFile | ConvertFrom-Json
    foreach ($relPath in $fileStructure.PSObject.Properties.Name) {
        $originalPath = $fileStructure.$relPath
        $destPath = Join-Path $FolderPath $relPath
        $destDir = Split-Path $destPath -Parent
        if (!(Test-Path $destDir)) {
            New-Item -Path $destDir -ItemType Directory -Force | Out-Null
        }
        if (Test-Path $originalPath) {
            Move-Item -Path $originalPath -Destination $destPath -Force
            Write-Host "Restored $relPath"
        } else {
            Write-Warning "Original file not found - $originalPath"
        }
    }
    $fileTypes = Get-FileTypes
    foreach ($category in $fileTypes.Keys) {
        $categoryPath = Join-Path $FolderPath $category
        if (Test-Path $categoryPath -and (Get-Item $categoryPath).PSIsContainer) {
            try {
                Remove-Item $categoryPath -Recurse -Force
                Write-Host "Removed category folder: $category"
            } catch {
                Write-Warning "Could not remove $category: $_"
            }
        }
    }
    Write-Host "Restoration completed!"
}

function Get-FilesToOrganize {
    param(
        [string]$FolderPath,
        [bool]$Recursive
    )
    if ($Recursive) {
        Get-ChildItem -Path $FolderPath -Recurse -File
    } else {
        Get-ChildItem -Path $FolderPath -File
    }
}

function Organize-Folder {
    param(
        [string]$FolderPath,
        [bool]$Recursive,
        [string]$BackupDir,
        [bool]$CreateBackupFlag
    )
    $fileTypes = Get-FileTypes
    $folder = $FolderPath

    if ($CreateBackupFlag) {
        $backupPath = Create-Backup -FolderPath $FolderPath -BackupDir $BackupDir
        Write-Host "Backup created: $backupPath"
    } else {
        Write-Host "Skipping backup creation as requested."
    }

    $filesToProcess = Get-FilesToOrganize -FolderPath $FolderPath -Recursive $Recursive

    $neededCategories = @{}
    foreach ($file in $filesToProcess) {
        if ($file.DirectoryName -match "\\($($fileTypes.Keys -join '|'))(\\|$)") { continue }
        $ext = $file.Extension.ToLower()
        foreach ($category in $fileTypes.Keys) {
            if ($fileTypes[$category] -contains $ext) {
                $neededCategories[$category] = $true
                break
            }
        }
    }

    foreach ($category in $neededCategories.Keys) {
        $categoryPath = Join-Path $folder $category
        if (!(Test-Path $categoryPath)) {
            New-Item -Path $categoryPath -ItemType Directory | Out-Null
            Write-Host "Created category folder: $category"
        }
    }

    $filesMoved = 0
    foreach ($file in $filesToProcess) {
        if ($file.DirectoryName -match "\\($($fileTypes.Keys -join '|'))(\\|$)") { continue }
        $ext = $file.Extension.ToLower()
        foreach ($category in $fileTypes.Keys) {
            if ($fileTypes[$category] -contains $ext) {
                $destination = Join-Path $folder $category
                $destFile = Join-Path $destination $file.Name
                try {
                    Move-Item -Path $file.FullName -Destination $destFile -Force
                    Write-Host "Moved $($file.Name) to $category"
                    $filesMoved++
                } catch {
                    Write-Warning "Error moving $($file.Name): $_"
                }
                break
            }
        }
    }

    if ($Recursive) {
        Get-ChildItem -Path $FolderPath -Recurse -Directory | Sort-Object FullName -Descending | ForEach-Object {
            if ($fileTypes.Keys -notcontains $_.Name) {
                try {
                    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
                    Write-Host "Deleted empty directory: $($_.FullName)"
                } catch {}
            }
        }
    }

    Write-Host "`nOrganization completed! $filesMoved files moved."
}

function Main {
    Write-Host "File Organizer Script"
    Write-Host ("=" * 30)

    $folderPath = Read-Host "Enter the folder path to organize (leave blank for current directory)"
    if (-not $folderPath) { $folderPath = (Get-Location).Path }
    if (-not (Test-Path $folderPath)) {
        Write-Host "Error: The folder '$folderPath' does not exist."
        return
    }

    $backupDir = Read-Host "Enter the backup directory path (leave blank for current directory)"
    if (-not $backupDir) { $backupDir = (Get-Location).Path }
    if (-not (Test-Path $backupDir)) { New-Item -Path $backupDir -ItemType Directory | Out-Null }

    $recursiveInput = Read-Host "Process files recursively (including subfolders)? (y/N)"
    $recursive = $recursiveInput -eq 'y'

    $createBackupInput = Read-Host "Create a backup before organizing? (y/N)"
    $createBackupFlag = $createBackupInput -eq 'y'

    $action = Read-Host "Choose action - 'organize' or 'restore' (leave blank for organize)"
    if ($action -eq 'restore') {
        $backupFile = Read-Host "Enter the path to the backup JSON file"
        if (-not (Test-Path $backupFile)) {
            Write-Host "Error: The backup file '$backupFile' does not exist."
            return
        }
        Write-Host "Restoring files in $folderPath..."
        Restore-Backup -FolderPath $folderPath -BackupFile $backupFile
    } else {
        Write-Host "Organizing files in $folderPath..."
        Write-Host "Recursive processing: $(if ($recursive) {'Yes'} else {'No'})"
        Write-Host "Backup creation: $(if ($createBackupFlag) {'Yes'} else {'No'})"
        Organize-Folder -FolderPath $folderPath -Recursive $recursive -BackupDir $backupDir -CreateBackupFlag $createBackupFlag
    }

    Write-Host "Operation completed!"
}

Main
function Move-SubfolderContents {
    param (
        [string]$SourceFolder
    )

    if (-not (Test-Path $SourceFolder -PathType Container)) {
        Write-Host "Error: Source folder '$SourceFolder' does not exist." -ForegroundColor Red
        return
    }

    $destinationFolder = Get-Location

    Write-Host "Moving contents from subfolders of '$SourceFolder' to '$destinationFolder'..." -ForegroundColor Cyan

    Get-ChildItem -Path $SourceFolder -Directory | ForEach-Object {
        $subfolder = $_
        Write-Host "Processing subfolder: $($subfolder.FullName)" -ForegroundColor Green
        Get-ChildItem -Path $subfolder.FullName | ForEach-Object {
            $item = $_
            try {
                Move-Item -Path $item.FullName -Destination $destinationFolder -Force -ErrorAction Stop
                Write-Host "Moved: $($item.Name)" -ForegroundColor DarkGreen
            }
            catch {
                Write-Host "Error moving $($item.Name): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }

    Write-Host "Operation complete." -ForegroundColor Cyan
}

# Main script execution
Write-Host "This script will move all contents from subfolders into the current directory." -ForegroundColor Yellow

$initialDirectory = Get-Location
$selectedFolder = Read-Host "Enter the path to the folder (e.g., C:\MyFolder) or press Enter for current directory: "

# If no path provided, use current directory
if ([string]::IsNullOrWhiteSpace($selectedFolder)) {
    $sourceFolder = $initialDirectory.Path
    Write-Host "No path provided. Using current directory: '$sourceFolder'" -ForegroundColor Yellow
} else {
    $sourceFolder = $selectedFolder
}

if (-not (Test-Path $sourceFolder -PathType Container)) {
    Write-Host "Error: The specified folder '$sourceFolder' does not exist. Exiting." -ForegroundColor Red
    exit
}

Write-Host "`nSelected folder for operation: '$sourceFolder'" -ForegroundColor Cyan
$confirm = Read-Host "Are you sure you want to proceed? This will move all files/folders from subdirectories of '$sourceFolder' to '$($initialDirectory.Path)' (Y/N): "

if ($confirm -eq 'Y' -or $confirm -eq 'y') {
    Move-SubfolderContents -SourceFolder $sourceFolder
    
    # Ask if user wants to delete empty folders
    Write-Host "`n" -NoNewline
    $deleteEmpty = Read-Host "Do you want to delete empty subfolders now? (Y/N): "
    
    if ($deleteEmpty -eq 'Y' -or $deleteEmpty -eq 'y') {
        Write-Host "Deleting empty subfolders..." -ForegroundColor Cyan
        
        Get-ChildItem -Path $sourceFolder -Directory | ForEach-Object {
            $subfolder = $_
            # Check if folder is empty
            $items = Get-ChildItem -Path $subfolder.FullName -Force
            if ($items.Count -eq 0) {
                try {
                    Remove-Item -Path $subfolder.FullName -Force -ErrorAction Stop
                    Write-Host "Deleted empty folder: $($subfolder.Name)" -ForegroundColor DarkGreen
                }
                catch {
                    Write-Host "Error deleting folder $($subfolder.Name): $($_.Exception.Message)" -ForegroundColor Red
                }
            } else {
                Write-Host "Skipped non-empty folder: $($subfolder.Name) ($($items.Count) items remaining)" -ForegroundColor Gray
            }
        }
        
        Write-Host "Empty folder cleanup complete." -ForegroundColor Cyan
    } else {
        Write-Host "Skipping empty folder deletion." -ForegroundColor Yellow
    }
}

Write-Host "Script execution completed." -ForegroundColor Green
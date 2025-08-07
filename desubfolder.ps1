function Move-SubfolderContents {
    param (
        [string]$SourceFolder,
        [string[]]$ExceptionFolders = @()
    )

    if (-not (Test-Path $SourceFolder -PathType Container)) {
        Write-Host "Error: Source folder '$SourceFolder' does not exist." -ForegroundColor Red
        return
    }

    $destinationFolder = Get-Location

    Write-Host "Moving contents from subfolders of '$SourceFolder' to '$destinationFolder'..." -ForegroundColor Cyan
    
    # Get all subfolders and filter out exceptions
    $subfolders = Get-ChildItem -Path $SourceFolder -Directory
    
    # Convert exception folder names to hashtable for faster lookup
    $exceptionLookup = @{}
    foreach ($exception in $ExceptionFolders) {
        $exceptionLookup[$exception.ToLower()] = $true
    }

    $subfolders | ForEach-Object {
        $subfolder = $_
        $subfolderName = $subfolder.Name
        
        # Check if this folder is in the exception list
        if ($exceptionLookup.ContainsKey($subfolderName.ToLower())) {
            Write-Host "Skipping exception folder: $($subfolder.FullName)" -ForegroundColor Yellow
            return
        }
        
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
Write-Host "Exception folders will be skipped during the operation." -ForegroundColor Yellow

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

# Get exception folders
$exceptionFolders = @()
Write-Host "`nEnter exception folder names (one per line). Press Enter twice when done:" -ForegroundColor Cyan
while ($true) {
    $exceptionFolder = Read-Host "Exception folder name"
    if ([string]::IsNullOrWhiteSpace($exceptionFolder)) {
        break
    }
    $exceptionFolders += $exceptionFolder.Trim()
}

if ($exceptionFolders.Count -gt 0) {
    Write-Host "`nException folders to skip:" -ForegroundColor Yellow
    $exceptionFolders | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
} else {
    Write-Host "`nNo exception folders specified." -ForegroundColor Gray
}

Write-Host "`nSelected folder for operation: '$sourceFolder'" -ForegroundColor Cyan
$confirm = Read-Host "Are you sure you want to proceed? This will move all files/folders from subdirectories of '$sourceFolder' to '$($initialDirectory.Path)' (Y/N): "

if ($confirm -eq 'Y' -or $confirm -eq 'y') {
    Move-SubfolderContents -SourceFolder $sourceFolder -ExceptionFolders $exceptionFolders
    
    # Ask if user wants to delete empty folders
    Write-Host "`n" -NoNewline
    $deleteEmpty = Read-Host "Do you want to delete empty subfolders now? (Y/N): "
    
    if ($deleteEmpty -eq 'Y' -or $deleteEmpty -eq 'y') {
        Write-Host "Deleting empty subfolders..." -ForegroundColor Cyan
        
        # Get all subfolders again, excluding exceptions
        $subfolders = Get-ChildItem -Path $sourceFolder -Directory
        $exceptionLookup = @{}
        foreach ($exception in $exceptionFolders) {
            $exceptionLookup[$exception.ToLower()] = $true
        }
        
        $subfolders | ForEach-Object {
            $subfolder = $_
            $subfolderName = $subfolder.Name
            
            # Skip exception folders
            if ($exceptionLookup.ContainsKey($subfolderName.ToLower())) {
                Write-Host "Skipping exception folder from deletion: $($subfolder.Name)" -ForegroundColor Yellow
                return
            }
            
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
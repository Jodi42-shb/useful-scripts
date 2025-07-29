# Organize Photos and Videos by Year and Month
# This script organizes photos and videos into folders based on their creation date or last modified date

param(
    [Parameter(Mandatory=$false)]
    [string]$SourcePath,
    
    [Parameter(Mandatory=$false)]
    [string]$DestinationPath,
    
    [switch]$WhatIf = $false,
    
    [switch]$Recursive = $false,
    
    [ValidateSet("Year", "Month", "Both")]
    [string]$FolderStructure = "Both",
    
    [ValidateSet("Photos", "Videos", "Both")]
    [string]$MediaType = "Both",
    
    [switch]$DeleteEmptyFolders = $false
)

# Define common photo file extensions
$PhotoExtensions = @('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.heic', '.raw', '.cr2', '.nef', '.arw', '.dng','.avif')

# Define common video file extensions
$VideoExtensions = @('.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg', '.mts', '.m2ts', '.vob', '.asf', '.rm', '.rmvb', '.divx', '.xvid')

# Combine all media extensions
$MediaExtensions = $PhotoExtensions + $VideoExtensions

function Remove-EmptyFolders {
    param(
        [string]$Path,
        [bool]$DryRun = $false
    )
    
    Write-Host "`nChecking for empty folders..." -ForegroundColor Yellow
    $emptyFoldersExist = $true
    
    while ($emptyFoldersExist) {
        $emptyFoldersExist = $false
        # Get all directories recursively, starting from deepest level
        $allFolders = Get-ChildItem -Path $Path -Recurse -Directory | Sort-Object FullName -Descending
        
        foreach ($folder in $allFolders) {
            # Check if folder is empty (no files and no subdirectories)
            $items = Get-ChildItem -Path $folder.FullName -Force
            if ($items.Count -eq 0) {
                $emptyFoldersExist = $true
                if ($DryRun) {
                    Write-Host "Would remove empty folder: $($folder.FullName)" -ForegroundColor Cyan
                } else {
                    try {
                        Remove-Item -Path $folder.FullName -Force
                        Write-Host "Removed empty folder: $($folder.FullName)" -ForegroundColor Green
                    }
                    catch {
                        Write-Warning "Failed to remove folder: $($folder.FullName) - $($_.Exception.Message)"
                    }
                }
            }
        }
    }
    Write-Host "Process complete. No more empty folders found." -ForegroundColor Green
}

function Get-MediaCreationDate {
    param([string]$FilePath)
    
    $fileExtension = (Get-Item $FilePath).Extension.ToLower()
    
    try {
        # Try to get the creation date from metadata first
        $shell = New-Object -ComObject Shell.Application
        $folder = $shell.Namespace((Get-Item $FilePath).DirectoryName)
        $file = $folder.ParseName((Get-Item $FilePath).Name)
        
        # Property 12 is usually the date taken for photos
        # Property 208 is media created date for videos
        $dateTaken = $folder.GetDetailsOf($file, 12)  # Date taken (photos)
        $mediaCreated = $folder.GetDetailsOf($file, 208)  # Media created (videos)
        
        # Try photo date first
        if ($dateTaken -and $dateTaken -ne "") {
            try {
                $parsedDate = [DateTime]::ParseExact($dateTaken.Substring(0, 10), "dd/MM/yyyy", $null)
                return $parsedDate
            }
            catch {
                # Try different date format
                try {
                    $parsedDate = [DateTime]::Parse($dateTaken)
                    return $parsedDate
                }
                catch {
                    # Continue to next method
                }
            }
        }
        
        # Try video media created date
        if ($mediaCreated -and $mediaCreated -ne "") {
            try {
                $parsedDate = [DateTime]::Parse($mediaCreated)
                return $parsedDate
            }
            catch {
                # Continue to next method
            }
        }
    }
    catch {
        # If metadata reading fails, fall back to file dates
    }
    
    # Fall back to file creation date or last write time
    $fileInfo = Get-Item $FilePath
    $creationDate = $fileInfo.CreationTime
    $lastWriteDate = $fileInfo.LastWriteTime
    
    # Use the earlier of creation date or last write date
    if ($creationDate -lt $lastWriteDate) {
        return $creationDate
    } else {
        return $lastWriteDate
    }
}

function Organize-Media {
    param(
        [string]$Source,
        [string]$Destination,
        [bool]$DryRun = $false,
        [bool]$ProcessSubfolders = $false,
        [string]$Structure = "Both",
        [string]$MediaFilter = "Both"
    )
    
    Write-Host "Starting photo and video organization..." -ForegroundColor Green
    Write-Host "Source: $Source" -ForegroundColor Yellow
    Write-Host "Destination: $Destination" -ForegroundColor Yellow
    Write-Host "Folder Structure: $Structure" -ForegroundColor Yellow
    Write-Host "Process Subfolders: $ProcessSubfolders" -ForegroundColor Yellow
    
    if ($DryRun) {
        Write-Host "Running in DRY RUN mode - no files will be moved" -ForegroundColor Cyan
    }
    
    # Validate source path
    if (-not (Test-Path $Source)) {
        Write-Error "Source path does not exist: $Source"
        return
    }
    
    # Create destination directory if it doesn't exist
    if (-not (Test-Path $Destination)) {
        if (-not $DryRun) {
            New-Item -ItemType Directory -Path $Destination -Force | Out-Null
        }
        Write-Host "Created destination directory: $Destination" -ForegroundColor Green
    }
    
    # Determine which extensions to use based on MediaFilter
    $targetExtensions = switch ($MediaFilter) {
        "Photos" { $PhotoExtensions }
        "Videos" { $VideoExtensions }
        "Both" { $MediaExtensions }
        default { $MediaExtensions }
    }
    
    # Get all media files (recursively or not based on parameter)
    if ($ProcessSubfolders) {
        $mediaFiles = Get-ChildItem -Path $Source -Recurse -File | Where-Object {
            $targetExtensions -contains $_.Extension.ToLower()
        }
    } else {
        $mediaFiles = Get-ChildItem -Path $Source -File | Where-Object {
            $targetExtensions -contains $_.Extension.ToLower()
        }
    }
    
    # Separate photos and videos for reporting
    $photoFiles = $mediaFiles | Where-Object { $PhotoExtensions -contains $_.Extension.ToLower() }
    $videoFiles = $mediaFiles | Where-Object { $VideoExtensions -contains $_.Extension.ToLower() }
    
    Write-Host "Found $($photoFiles.Count) photo files and $($videoFiles.Count) video files" -ForegroundColor Green
    
    $processedCount = 0
    $errorCount = 0
    
    foreach ($mediaFile in $mediaFiles) {
        try {
            # Get media file date
            $mediaDate = Get-MediaCreationDate -FilePath $mediaFile.FullName
            
            # Determine file type for subfolder organization
            $fileExtension = $mediaFile.Extension.ToLower()
            $isPhoto = $PhotoExtensions -contains $fileExtension
            $isVideo = $VideoExtensions -contains $fileExtension
            
            # Create folder structure based on user choice
            $year = $mediaDate.Year
            $month = $mediaDate.ToString("MM-MMMM")  # e.g., "01-January"
            
            $targetFolder = $Destination
            
            switch ($Structure) {
                "Year" {
                    $targetFolder = Join-Path $Destination $year
                }
                "Month" {
                    $targetFolder = Join-Path $Destination $month
                }
                "Both" {
                    $yearFolder = Join-Path $Destination $year
                    $targetFolder = Join-Path $yearFolder $month
                }
            }
            
            # Create directories if they don't exist
            if (-not $DryRun) {
                if ($Structure -eq "Both") {
                    $yearFolder = Join-Path $Destination $year
                    if (-not (Test-Path $yearFolder)) {
                        New-Item -ItemType Directory -Path $yearFolder -Force | Out-Null
                    }
                }
                if (-not (Test-Path $targetFolder)) {
                    New-Item -ItemType Directory -Path $targetFolder -Force | Out-Null
                }
            }
            
            # Determine destination file path
            $destinationFile = Join-Path $targetFolder $mediaFile.Name
            
            # Handle duplicate file names
            $counter = 1
            $originalName = $mediaFile.BaseName
            $extension = $mediaFile.Extension
            
            while (Test-Path $destinationFile) {
                $newName = "$originalName($counter)$extension"
                $destinationFile = Join-Path $targetFolder $newName
                $counter++
            }
            
            # Move or copy the file
            $fileType = if ($isPhoto) { "Photo" } elseif ($isVideo) { "Video" } else { "Media" }
            
            # Display appropriate folder structure in output
            $displayPath = switch ($Structure) {
                "Year" { $year }
                "Month" { $month }
                "Both" { "$year\$month" }
            }
            
            if ($DryRun) {
                Write-Host "Would move $fileType`: $($mediaFile.FullName) -> $destinationFile" -ForegroundColor Cyan
            } else {
                Move-Item -Path $mediaFile.FullName -Destination $destinationFile -Force
                Write-Host "Moved $fileType`: $($mediaFile.Name) -> $displayPath" -ForegroundColor Green
            }
            
            $processedCount++
            
            # Show progress every 10 files
            if ($processedCount % 10 -eq 0) {
                Write-Progress -Activity "Organizing Photos and Videos" -Status "Processed $processedCount of $($mediaFiles.Count) files" -PercentComplete (($processedCount / $mediaFiles.Count) * 100)
            }
        }
        catch {
            Write-Warning "Error processing file $($mediaFile.FullName): $($_.Exception.Message)"
            $errorCount++
        }
    }
    
    Write-Progress -Activity "Organizing Photos and Videos" -Completed
    
    Write-Host "`nOrganization complete!" -ForegroundColor Green
    Write-Host "Successfully processed: $processedCount files" -ForegroundColor Green
    if ($errorCount -gt 0) {
        Write-Host "Errors encountered: $errorCount files" -ForegroundColor Red
    }
}

# Interactive mode if no parameters provided or if running without switches
if (-not $SourcePath -or -not $DestinationPath -or (-not $PSBoundParameters.ContainsKey('Recursive') -and -not $PSBoundParameters.ContainsKey('FolderStructure'))) {
    Write-Host "Photo and Video Organizer" -ForegroundColor Green
    Write-Host "========================" -ForegroundColor Green
    Write-Host ""
    
    if (-not $SourcePath) {
        $SourcePath = Read-Host "Enter source folder path"
    }
    
    if (-not $DestinationPath) {
        $DestinationPath = Read-Host "Enter destination folder path"
    }
    
    # Validate paths
    if (-not (Test-Path $SourcePath)) {
        Write-Host "Error: Source path does not exist: $SourcePath" -ForegroundColor Red
        return
    }
    
    Write-Host ""
    Write-Host "Configuration Options:" -ForegroundColor Yellow
    Write-Host "=====================" -ForegroundColor Yellow
    
    # Always ask about recursive processing if not explicitly set
    if (-not $PSBoundParameters.ContainsKey('Recursive')) {
        $recursiveChoice = Read-Host "Process subfolders recursively? (y/N)"
        $Recursive = $recursiveChoice -eq 'y' -or $recursiveChoice -eq 'Y'
    }
    
    # Always ask about media type if not explicitly set
    if (-not $PSBoundParameters.ContainsKey('MediaType')) {
        Write-Host ""
        Write-Host "Choose media type to process:"
        Write-Host "1. Photos only"
        Write-Host "2. Videos only"
        Write-Host "3. Both Photos and Videos"
        
        $mediaChoice = Read-Host "Enter choice (1/2/3) [default: 3]"
        
        switch ($mediaChoice) {
            "1" { $MediaType = "Photos" }
            "2" { $MediaType = "Videos" }
            default { $MediaType = "Both" }
        }
    }
    
    # Always ask about folder structure if not explicitly set
    if (-not $PSBoundParameters.ContainsKey('FolderStructure')) {
        Write-Host ""
        Write-Host "Choose folder structure:"
        Write-Host "1. Year only (e.g., 2024)"
        Write-Host "2. Month only (e.g., 01-January)"
        Write-Host "3. Both Year and Month (e.g., 2024\01-January)"
        
        $structureChoice = Read-Host "Enter choice (1/2/3) [default: 3]"
        
        switch ($structureChoice) {
            "1" { $FolderStructure = "Year" }
            "2" { $FolderStructure = "Month" }
            default { $FolderStructure = "Both" }
        }
    }
    
    # Always ask about dry run if not explicitly set
    if (-not $PSBoundParameters.ContainsKey('WhatIf')) {
        Write-Host ""
        $dryRunChoice = Read-Host "Run in preview mode (no files moved)? (y/N)"
        $WhatIf = $dryRunChoice -eq 'y' -or $dryRunChoice -eq 'Y'
    }
    
    # Always ask about deleting empty folders if not explicitly set
    if (-not $PSBoundParameters.ContainsKey('DeleteEmptyFolders')) {
        Write-Host ""
        $deleteEmptyChoice = Read-Host "Delete empty folders after organizing? (y/N)"
        $DeleteEmptyFolders = $deleteEmptyChoice -eq 'y' -or $deleteEmptyChoice -eq 'Y'
    }
    
    Write-Host ""
    Write-Host "Summary of Settings:" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    Write-Host "Source Path: $SourcePath" -ForegroundColor White
    Write-Host "Destination Path: $DestinationPath" -ForegroundColor White
    Write-Host "Process Subfolders: $Recursive" -ForegroundColor White
    Write-Host "Media Type: $MediaType" -ForegroundColor White
    Write-Host "Folder Structure: $FolderStructure" -ForegroundColor White
    Write-Host "Preview Mode: $WhatIf" -ForegroundColor White
    Write-Host "Delete Empty Folders: $DeleteEmptyFolders" -ForegroundColor White
    Write-Host ""
    
    $continueChoice = Read-Host "Continue with these settings? (Y/n)"
    if ($continueChoice -eq 'n' -or $continueChoice -eq 'N') {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        return
    }
}

# Main execution
if ($PSCmdlet.ShouldProcess("Photos and Videos", "Organize")) {
    try {
        Organize-Media -Source $SourcePath -Destination $DestinationPath -DryRun $WhatIf -ProcessSubfolders $Recursive -Structure $FolderStructure -MediaFilter $MediaType
        
        # Delete empty folders in source path if requested and not in dry run mode
        if ($DeleteEmptyFolders -and -not $WhatIf) {
            Remove-EmptyFolders -Path $SourcePath -DryRun $false
        }
    }
    catch {
        Write-Error "An error occurred: $($_.Exception.Message)"
    }
}

# Example usage:
# .\Organize-Photos.ps1 -SourcePath "C:\Users\YourName\Pictures" -DestinationPath "C:\Users\YourName\Organized Media"
# .\Organize-Photos.ps1 -SourcePath "C:\Users\YourName\Pictures" -DestinationPath "C:\Users\YourName\Organized Media" -WhatIf
# .\Organize-Photos.ps1 -SourcePath "C:\Users\YourName\Videos" -DestinationPath "C:\Users\YourName\Organized Media" -Recursive
# .\Organize-Photos.ps1 -SourcePath "C:\Users\YourName\Pictures" -DestinationPath "C:\Users\YourName\Organized Media" -FolderStructure "Year"
# .\Organize-Photos.ps1 -SourcePath "C:\Users\YourName\Pictures" -DestinationPath "C:\Users\YourName\Organized Media" -FolderStructure "Month" -Recursive
# .\Organize-Photos.ps1 -SourcePath "C:\Users\YourName\Pictures" -DestinationPath "C:\Users\YourName\Organized Media" -DeleteEmptyFolders
# 
# Interactive mode (run without parameters):
# .\Organize-Photos.ps1
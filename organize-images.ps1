# PowerShell script to organize images into a 'chapter 1' subfolder
# Usage: .\organize-images.ps1 -FolderPath "C:\path\to\your\folder"

param(
    [Parameter(Mandatory=$true)]
    [string]$FolderPath
)

# Common image file extensions
$imageExtensions = @('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.ico', '.svg','.avif','.heic')

# Check if the source folder exists
if (-not (Test-Path -Path $FolderPath)) {
    Write-Error "The specified folder does not exist: $FolderPath"
    exit 1
}

# Create the "chapter 1" subfolder if it doesn't exist
$chapterFolder = Join-Path -Path $FolderPath -ChildPath "chapter 1"
if (-not (Test-Path -Path $chapterFolder)) {
    New-Item -ItemType Directory -Path $chapterFolder -Force
    Write-Host "Created folder: $chapterFolder" -ForegroundColor Green
} else {
    Write-Host "Folder already exists: $chapterFolder" -ForegroundColor Yellow
}

# Get all image files in the source folder (not including subfolders)
$imageFiles = Get-ChildItem -Path $FolderPath -File | Where-Object {
    $imageExtensions -contains $_.Extension.ToLower()
}

if ($imageFiles.Count -eq 0) {
    Write-Host "No image files found in the specified folder." -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($imageFiles.Count) image file(s) to move..." -ForegroundColor Cyan

# Move each image file to the chapter 1 folder
$movedCount = 0
foreach ($file in $imageFiles) {
    try {
        $destinationPath = Join-Path -Path $chapterFolder -ChildPath $file.Name
        
        # Check if file already exists in destination
        if (Test-Path -Path $destinationPath) {
            Write-Warning "File already exists in destination, skipping: $($file.Name)"
            continue
        }
        
        Move-Item -Path $file.FullName -Destination $destinationPath -Force
        Write-Host "Moved: $($file.Name)" -ForegroundColor Green
        $movedCount++
    }
    catch {
        Write-Error "Failed to move $($file.Name): $($_.Exception.Message)"
    }
}

Write-Host "`nOperation completed. Moved $movedCount out of $($imageFiles.Count) image file(s)." -ForegroundColor Cyan

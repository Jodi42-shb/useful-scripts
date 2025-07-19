#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Organizes files into Mihon local library structure

.DESCRIPTION
    This script organizes manga/comic files into the Mihon local library structure:
    [storage_location]/local/[series_title]/cover.jpg + chapter_n folders with images

.PARAMETER SourcePath
    The path containing the files to organize

.PARAMETER DestinationPath
    The destination path where the organized structure will be created

.PARAMETER SeriesTitle
    The title of the series (will be used as folder name)

.PARAMETER CoverImage
    Optional path to cover image file

.EXAMPLE
    .\Organize-MihonLibrary.ps1 -SourcePath "C:\Downloads\Manga" -DestinationPath "C:\MihonLibrary" -SeriesTitle "My Manga Series"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$SourcePath,
    
    [Parameter(Mandatory=$true)]
    [string]$DestinationPath,
    
    [Parameter(Mandatory=$true)]
    [string]$SeriesTitle,
    
    [Parameter(Mandatory=$false)]
    [string]$CoverImage
)

# Function to create the base directory structure
function New-MihonStructure {
    param(
        [string]$BasePath,
        [string]$Title
    )
    
    $localPath = Join-Path $BasePath "local"
    $seriesPath = Join-Path $localPath $Title
    
    # Create directories if they don't exist
    if (-not (Test-Path $localPath)) {
        New-Item -Path $localPath -ItemType Directory -Force
        Write-Host "Created directory: $localPath" -ForegroundColor Green
    }
    
    if (-not (Test-Path $seriesPath)) {
        New-Item -Path $seriesPath -ItemType Directory -Force
        Write-Host "Created directory: $seriesPath" -ForegroundColor Green
    }
    
    return $seriesPath
}

# Function to organize images into chapter folders
function Set-ChapterStructure {
    param(
        [string]$SeriesPath,
        [string]$SourcePath
    )
    
    # Get all image files from source
    $imageExtensions = @("*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.webp")
    $imageFiles = Get-ChildItem -Path $SourcePath -Include $imageExtensions -Recurse | Sort-Object Name
    
    if ($imageFiles.Count -eq 0) {
        Write-Warning "No image files found in source path: $SourcePath"
        return
    }
    
    Write-Host "Found $($imageFiles.Count) image files to organize" -ForegroundColor Cyan
    
    # Group images by assumed chapter (you might want to modify this logic)
    $chapterNumber = 1
    $imagesPerChapter = 20  # Adjust this based on your needs
    
    # Ask user for images per chapter
    $userInput = Read-Host "How many images per chapter? (default: 20, 'auto' for automatic detection)"
    if ($userInput -eq "auto") {
        $imagesPerChapter = [Math]::Ceiling($imageFiles.Count / 10)  # Assume 10 chapters max
    } elseif ($userInput -match '^\d+$') {
        $imagesPerChapter = [int]$userInput
    }
    
    for ($i = 0; $i -lt $imageFiles.Count; $i += $imagesPerChapter) {
        $chapterPath = Join-Path $SeriesPath "chapter_$chapterNumber"
        
        if (-not (Test-Path $chapterPath)) {
            New-Item -Path $chapterPath -ItemType Directory -Force
            Write-Host "Created chapter folder: chapter_$chapterNumber" -ForegroundColor Green
        }
        
        # Copy images to chapter folder
        $endIndex = [Math]::Min($i + $imagesPerChapter - 1, $imageFiles.Count - 1)
        $chapterImages = $imageFiles[$i..$endIndex]
        
        $imageNumber = 1
        foreach ($image in $chapterImages) {
            $extension = $image.Extension
            $newImageName = "image_$imageNumber$extension"
            $destinationPath = Join-Path $chapterPath $newImageName
            
            try {
                Copy-Item -Path $image.FullName -Destination $destinationPath -Force
                Write-Host "  Copied: $($image.Name) -> $newImageName" -ForegroundColor Gray
                $imageNumber++
            } catch {
                Write-Error "Failed to copy $($image.Name): $_"
            }
        }
        
        $chapterNumber++
    }
}

# Function to handle cover image
function Set-CoverImage {
    param(
        [string]$SeriesPath,
        [string]$CoverImagePath
    )
    
    if ([string]::IsNullOrEmpty($CoverImagePath)) {
        Write-Host "No cover image specified. Looking for cover in source..." -ForegroundColor Yellow
        
        # Try to find a cover image in the source
        $possibleCovers = Get-ChildItem -Path $SourcePath -Include @("*cover*", "*Cover*", "*COVER*") -Recurse
        if ($possibleCovers.Count -gt 0) {
            $CoverImagePath = $possibleCovers[0].FullName
            Write-Host "Found potential cover: $($possibleCovers[0].Name)" -ForegroundColor Green
        } else {
            Write-Host "No cover image found. You can add cover.jpg manually later." -ForegroundColor Yellow
            return
        }
    }
    
    if (Test-Path $CoverImagePath) {
        $coverDestination = Join-Path $SeriesPath "cover.jpg"
        try {
            Copy-Item -Path $CoverImagePath -Destination $coverDestination -Force
            Write-Host "Cover image copied successfully" -ForegroundColor Green
        } catch {
            Write-Error "Failed to copy cover image: $_"
        }
    } else {
        Write-Warning "Cover image not found at: $CoverImagePath"
    }
}

# Main execution
try {
    Write-Host "Starting Mihon Library Organization..." -ForegroundColor Cyan
    Write-Host "Source: $SourcePath" -ForegroundColor White
    Write-Host "Destination: $DestinationPath" -ForegroundColor White
    Write-Host "Series: $SeriesTitle" -ForegroundColor White
    
    # Validate source path
    if (-not (Test-Path $SourcePath)) {
        throw "Source path does not exist: $SourcePath"
    }
    
    # Create the base structure
    $seriesPath = New-MihonStructure -BasePath $DestinationPath -Title $SeriesTitle
    
    # Handle cover image
    Set-CoverImage -SeriesPath $seriesPath -CoverImagePath $CoverImage
    
    # Organize chapters
    Set-ChapterStructure -SeriesPath $seriesPath -SourcePath $SourcePath
    
    Write-Host "`nOrganization complete!" -ForegroundColor Green
    Write-Host "Series location: $seriesPath" -ForegroundColor Green
    
    # Show the created structure
    Write-Host "`nCreated structure:" -ForegroundColor Cyan
    if (Get-Command tree -ErrorAction SilentlyContinue) {
        tree $seriesPath /F
    } else {
        Get-ChildItem -Path $seriesPath -Recurse | Format-Table Name, Length, LastWriteTime
    }
    
} catch {
    Write-Error "An error occurred: $_"
    exit 1
}

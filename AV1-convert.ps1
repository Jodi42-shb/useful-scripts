function Test-FFmpeg {
    # Check if FFmpeg is installed and supports AV1
    try {
        $encoders = ffmpeg -encoders 2>&1 | Out-String
        if ($encoders -match "libsvtav1") {
            return "libsvtav1"
        }
        elseif ($encoders -match "libaom-av1") {
            return "libaom-av1"
        }
        else {
            Write-Host "Error: No AV1 encoder (libsvtav1 or libaom-av1) found in FFmpeg." -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "Error: FFmpeg not installed or AV1 not supported. Install FFmpeg with AV1 support (e.g., choco install ffmpeg)." -ForegroundColor Red
        exit 1
    }
}

function Get-CropDimensions {
    param (
        [string]$InputFile
    )
    # Detect black bars using cropdetect
    try {
        $output = ffmpeg -i "`"$InputFile`"" -vf cropdetect=0 -f null - 2>&1 | Out-String
        $cropLine = ($output -split "`n" | Select-String "crop=" | Select-Object -Last 1).Line
        if ($cropLine -match "crop=(\d+:\d+:\d+:\d+)") {
            return $Matches[1]
        }
        else {
            Write-Host "Warning: Could not detect crop for $InputFile. Skipping crop." -ForegroundColor Yellow
            return $null
        }
    }
    catch {
        Write-Host "Warning: Could not detect crop for $InputFile. $_" -ForegroundColor Yellow
        return $null
    }
}

function Convert-Video {
    param (
        [string]$InputFile,
        [string]$OutputFile,
        [string]$Encoder,
        [int]$Preset,
        [int]$Crf,
        [bool]$Crop
    )
    # Convert a single video to AV1
    try {
        $cmd = "ffmpeg -i `"$InputFile`""
        if ($Crop) {
            $cropFilter = Get-CropDimensions -InputFile $InputFile
            if ($cropFilter) {
                $cmd += " -vf crop=$cropFilter"
            }
        }
        $cmd += " -c:v $Encoder -preset $Preset -crf $Crf -c:a copy -f matroska `"$OutputFile`" -y"
        Invoke-Expression $cmd
        Write-Host "Successfully converted $InputFile to $OutputFile" -ForegroundColor Green
    }
    catch {
        Write-Host "Error converting $InputFile : $_" -ForegroundColor Red
    }
}

function Clean-Path {
    param (
        [string]$Path
    )
    # Strip surrounding quotes from paths copied via "Copy as path"
    if ($Path -match '^"(.*)"$') {
        return $Matches[1]
    }
    return $Path
}

function Validate-Directory {
    param (
        [string]$Path
    )
    # Validate that the path is a directory, not a file
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $true  # Empty path is allowed (defaults to input directory)
    }
    $cleanPath = Clean-Path -Path $Path
    if (Test-Path $cleanPath -PathType Leaf -ErrorAction SilentlyContinue) {
        Write-Host "Error: Output path '$cleanPath' is a file, not a directory." -ForegroundColor Red
        return $false
    }
    return $true
}

function Main {
    Write-Host "AV1 Video Converter" -ForegroundColor Cyan
    $encoder = Test-FFmpeg
    Write-Host "Using encoder: $encoder" -ForegroundColor Cyan

    # Choose encoding mode
    $mode = Read-Host "Choose mode: (1) Single file, (2) Batch folder"
    while ($mode -notin @("1", "2")) {
        Write-Host "Invalid choice. Enter 1 or 2." -ForegroundColor Red
        $mode = Read-Host "Choose mode: (1) Single file, (2) Batch folder"
    }

    # Get quality settings
    if ($encoder -eq "libsvtav1") {
        $presetRange = 1..13
        $defaultPreset = 8
        $presetPrompt = "Enter preset (1-13, higher is faster, e.g., 8 for speed, press Enter for default $defaultPreset)"
    }
    else {
        $presetRange = 0..8
        $defaultPreset = 6
        $presetPrompt = "Enter preset (0-8, higher is faster, e.g., 6 for speed, press Enter for default $defaultPreset)"
    }

    $presetInput = Read-Host $presetPrompt
    if ([string]::IsNullOrWhiteSpace($presetInput)) {
        $preset = $defaultPreset
        Write-Host "Using default preset: $defaultPreset" -ForegroundColor Cyan
    }
    else {
        $preset = $presetInput
        while (-not [int]::TryParse($preset, [ref]$null) -or $preset -notin $presetRange) {
            Write-Host "Invalid preset. Choose $(${presetRange}[0])-$(${presetRange}[-1])." -ForegroundColor Red
            $preset = Read-Host $presetPrompt
            if ([string]::IsNullOrWhiteSpace($preset)) {
                $preset = $defaultPreset
                Write-Host "Using default preset: $defaultPreset" -ForegroundColor Cyan
                break
            }
        }
        $preset = [int]$preset
    }

    $crf = Read-Host "Enter CRF (0-63, higher is faster/lower quality, e.g., 30)"
    while (-not [int]::TryParse($crf, [ref]$null) -or $crf -lt 0 -or $crf -gt 63) {
        Write-Host "Invalid CRF. Choose 0-63." -ForegroundColor Red
        $crf = Read-Host "Enter CRF (0-63, higher is faster/lower quality, e.g., 30)"
    }
    $crf = [int]$crf

    $crop = (Read-Host "Enable automatic black bar cropping? (y/n)").ToLower() -eq 'y'

    # Get output directory
    $outputDir = Read-Host "Enter output directory path (e.g., 'C:\Videos\Output', leave blank for same as input, use 'Copy as path' in Explorer)"
    $outputDir = Clean-Path -Path $outputDir
    while (-not (Validate-Directory -Path $outputDir)) {
        Write-Host "Please enter a valid directory path or leave blank. Use 'Copy as path' in Explorer." -ForegroundColor Red
        $outputDir = Read-Host "Enter output directory path (e.g., 'C:\Videos\Output', leave blank for same as input)"
        $outputDir = Clean-Path -Path $outputDir
    }
    if ($outputDir -and -not (Test-Path $outputDir -PathType Container -ErrorAction SilentlyContinue)) {
        Write-Host "Output directory not found. Creating directory: $outputDir" -ForegroundColor Yellow
        try {
            New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        }
        catch {
            Write-Host "Error: Could not create output directory $outputDir. $_" -ForegroundColor Red
            exit 1
        }
    }

    # Process input
    if ($mode -eq "1") {
        $inputFile = Read-Host "Enter input video file path (e.g., 'C:\Path\To File.mp4', use 'Copy as path' in Explorer)"
        $inputFile = Clean-Path -Path $inputFile
        while (-not (Test-Path $inputFile -PathType Leaf -ErrorAction SilentlyContinue)) {
            Write-Host "File not found or invalid path. Use 'Copy as path' in Explorer or double quotes for spaces (e.g., 'C:\Path\To File.mp4')." -ForegroundColor Red
            $inputFile = Read-Host "Enter input video file path (e.g., 'C:\Path\To File.mp4', use 'Copy as path' in Explorer)"
            $inputFile = Clean-Path -Path $inputFile
        }
        $fileName = [System.IO.Path]::GetFileNameWithoutExtension($inputFile)
        $outputFile = if ($outputDir) {
            Join-Path $outputDir "$fileName`_av1.mkv"
        } else {
            [System.IO.Path]::ChangeExtension($inputFile, "_av1.mkv")
        }
        Convert-Video -InputFile $inputFile -OutputFile $outputFile -Encoder $encoder -Preset $preset -Crf $crf -Crop $crop
    }
    else {
        $folder = Read-Host "Enter folder path containing videos (e.g., 'C:\Videos', use 'Copy as path' in Explorer)"
        $folder = Clean-Path -Path $folder
        while (-not (Test-Path $folder -PathType Container -ErrorAction SilentlyContinue)) {
            Write-Host "Folder not found. Use 'Copy as path' in Explorer or double quotes for spaces (e.g., 'C:\Path\To Folder')." -ForegroundColor Red
            $folder = Read-Host "Enter folder path containing videos (e.g., 'C:\Videos', use 'Copy as path' in Explorer)"
            $folder = Clean-Path -Path $folder
        }

        $videoExtensions = @("*.mp4", "*.mkv", "*.avi", "*.mov", "*.wmv")
        $files = @()
        foreach ($ext in $videoExtensions) {
            $files += Get-ChildItem -Path $folder -Filter $ext -File -ErrorAction SilentlyContinue
        }

        if ($files.Count -eq 0) {
            Write-Host "No video files found in folder." -ForegroundColor Red
            return
        }

        Write-Host "Found $($files.Count) video(s) to convert." -ForegroundColor Cyan
        $progress = 0
        foreach ($file in $files) {
            $progress++
            Write-Progress -Activity "Converting videos" -Status "Processing $progress of $($files.Count)" -PercentComplete (($progress / $files.Count) * 100)
            $fileName = [System.IO.Path]::GetFileNameWithoutExtension($file.FullName)
            $outputFile = if ($outputDir) {
                Join-Path $outputDir "$fileName`_av1.mkv"
            } else {
                [System.IO.Path]::ChangeExtension($file.FullName, "_av1.mkv")
            }
            Convert-Video -InputFile $file.FullName -OutputFile $outputFile -Encoder $encoder -Preset $preset -Crf $crf -Crop $crop
        }
        Write-Progress -Activity "Converting videos" -Completed
    }
}

# Run the script
Main
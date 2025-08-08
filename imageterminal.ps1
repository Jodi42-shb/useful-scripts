<#
.SYNOPSIS
    Convert an image to ASCII art and print it in the console – with or without color.

.DESCRIPTION
    The script takes a file path to an image, optionally resizes it, and renders it
    line‑by‑line.  It uses a simple brightness‑to‑glyph mapping that mimics what
    tools like neofetch or FIGlet do.  For colour support it emits ANSI escape
    sequences that the Windows 10 console (or any ANSI‑aware terminal) understands.

.PARAMETER Path
    Path to the image file (PNG, JPG, GIF, BMP, …).

.PARAMETER Width
    Desired output width in console columns.  If omitted, the script uses the
    current console width (minus a few columns for safety).

.PARAMETER NoColor
    Switch.  If set, only monochrome ASCII art will be printed.

.EXAMPLE
    .\Show-ImageInConsole.ps1 -Path 'logo.png' -Width 80

.EXAMPLE
    .\Show-ImageInConsole.ps1 -Path 'logo.png' -NoColor
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Path,

    [int]$Width,

    [switch]$NoColor
)

# If path is wrapped in quotes, remove them.
if (($Path.StartsWith('"') -and $Path.EndsWith('"')) -or ($Path.StartsWith("'") -and $Path.EndsWith("'"))) {
    $Path = $Path.Substring(1, $Path.Length - 2)
}

# ------------------ Helper Functions ------------------
function Get-ConsoleWidth {
    try { return (Get-Host).UI.RawUI.WindowSize.Width } catch { return 80 }
}

# Map brightness (0-255) to one of the glyphs.
$Glyphs = @(' ', '.', ':', '-', '=', '+', '*', '#', '%', '@')   # 10 levels
function BrightnessToGlyph([byte]$b) {
    $index = [int]( ($b / 255) * ($Glyphs.Length-1) )
    return $Glyphs[$index]
}

# Create ANSI escape code for setting foreground colour
function AnsiColor([int]$r, [int]$g, [int]$b) {
    return "`e[38;2;${r};${g};${b}m"
}
function ResetAnsi() { return "`e[0m" }

# ------------------ Load & Resize Image ------------------
try {
    $bitmap = [System.Drawing.Bitmap]::FromFile($Path)
} catch {
    Write-Error "Cannot load image: $_"
    exit 1
}

# Determine target width if not provided
if (-not $Width) { $Width = (Get-ConsoleWidth) - 5 }

# Preserve aspect ratio; 1 console char ~ 2 pixels tall (approx)
$ratio = $bitmap.Width / $bitmap.Height
$targetHeight = [int]($Width / $ratio * 0.5)  # 0.5 for aspect ratio

# Create a resized bitmap
$small = New-Object System.Drawing.Bitmap($Width, $targetHeight)
$g = [System.Drawing.Graphics]::FromImage($small)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.DrawImage($bitmap, 0, 0, $Width, $targetHeight)
$g.Dispose()
$bitmap.Dispose()

# ------------------ Render ------------------
for ($y=0; $y -lt $targetHeight; $y++) {
    $line = ""
    for ($x=0; $x -lt $Width; $x++) {
        $pixel = $small.GetPixel($x,$y)

        if ($NoColor) {
            $g = [int]( ($pixel.R + $pixel.G + $pixel.B) / 3 )
            $line += BrightnessToGlyph($g)
        }
        else {
            # Use the pixel's own colour; map to nearest ASCII glyph
            $g = [int]( ($pixel.R + $pixel.G + $pixel.B) / 3 )
            $glyph = BrightnessToGlyph($g)
            $line += (AnsiColor $pixel.R $pixel.G $pixel.B) + $glyph + (ResetAnsi)
        }
    }
    Write-Host $line
}

$small.Dispose()
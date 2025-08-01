# PowerShell Script to Scan for Outdated Software and Prompt for Upgrades

# Function to get list of outdated packages using winget
function Get-OutdatedPackages {
    $upgradeOutput = winget upgrade --include-unknown
    $packages = @()
    $lines = $upgradeOutput -split "`n"
    $startIndex = $lines | Select-String -Pattern "Name\s+Id\s+Version\s+Available" | Select-Object -First 1 -ExpandProperty LineNumber
    if ($startIndex) {
        for ($i = $startIndex; $i -lt $lines.Length; $i++) {
            $line = $lines[$i].Trim()
            if ($line -match "^(.*?)\s+([\w\.]+)\s+(\S+)\s+(\S+)") {
                $packages += [PSCustomObject]@{
                    Name = $Matches[1].Trim()
                    Id = $Matches[2].Trim()
                    CurrentVersion = $Matches[3].Trim()
                    AvailableVersion = $Matches[4].Trim()
                }
            }
        }
    }
    return $packages
}

# Main script logic
Write-Host "Scanning for outdated software..." -ForegroundColor Green
$outdated = Get-OutdatedPackages

if ($outdated.Count -eq 0) {
    Write-Host "No outdated software found." -ForegroundColor Yellow
    exit
}

# Display list of outdated software
Write-Host "Outdated software found:" -ForegroundColor Cyan
for ($i = 0; $i -lt $outdated.Count; $i++) {
    Write-Host "$($i + 1). $($outdated[$i].Name) (Current: $($outdated[$i].CurrentVersion) -> Available: $($outdated[$i].AvailableVersion))"
}

# Prompt user for selection
$selection = Read-Host "Enter the numbers of the software to upgrade (comma-separated, e.g., 1,3) or 'all' to upgrade everything"
if ($selection -eq "all") {
    $toUpgrade = $outdated
} else {
    $indices = $selection -split "," | ForEach-Object { [int]$_ - 1 }
    $toUpgrade = $outdated | Select-Object -Index $indices
}

# Perform upgrades
foreach ($pkg in $toUpgrade) {
    Write-Host "Upgrading $($pkg.Name)..." -ForegroundColor Green
    winget upgrade --id $pkg.Id --silent --force --accept-package-agreements --accept-source-agreements
}

Write-Host "Upgrade process completed." -ForegroundColor Green

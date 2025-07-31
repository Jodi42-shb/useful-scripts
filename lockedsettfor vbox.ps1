# Windows 11 Personalization GUI Script (Updated)
# Save this code as a .ps1 file (e.g., PersonalizeWin11.ps1) and run it in PowerShell (preferably as Admin)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create the main form
$form = New-Object System.Windows.Forms.Form
$form.Text = "Windows 11 Personalization (Unactivated)"
$form.Size = New-Object System.Drawing.Size(500, 750) # Increased height slightly
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.BackColor = [System.Drawing.Color]::WhiteSmoke

# Function to create standard buttons
function Create-Button {
    param (
        [string]$Text,
        [System.Management.Automation.ScriptBlock]$OnClick,
        [int]$Top,
        [int]$Width = 460,
        [int]$Height = 40
    )

    $button = New-Object System.Windows.Forms.Button
    $button.Text = $Text
    $button.Size = New-Object System.Drawing.Size($Width, $Height)
    $button.Location = New-Object System.Drawing.Point(15, $Top)
    $button.BackColor = [System.Drawing.Color]::LightBlue
    $button.Font = New-Object System.Drawing.Font("Segoe UI", 10)
    $button.Add_Click($OnClick)
    $form.Controls.Add($button)
}

# Function to create labels
function Create-Label {
    param (
        [string]$Text,
        [int]$Top,
        [int]$Width = 460,
        [int]$Height = 20
    )

    $label = New-Object System.Windows.Forms.Label
    $label.Text = $Text
    $label.Size = New-Object System.Drawing.Size($Width, $Height)
    $label.Location = New-Object System.Drawing.Point(15, $Top)
    $label.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    $form.Controls.Add($label)
}

# --- Define Button Actions ---

# Change Theme (Opens Theme Settings)
$changeTheme_Click = {
    Start-Process -FilePath "rundll32.exe" -ArgumentList "themecpl.dll,OpenThemeDialog"
}

# Set Background Color (Registry)
$setBgColor_Click = {
    $colorDialog = New-Object System.Windows.Forms.ColorDialog
    $colorDialog.FullOpen = $true
    $result = $colorDialog.ShowDialog()

    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        $color = $colorDialog.Color
        try {
            $keyPath = "HKCU:\Control Panel\Colors"
            Set-ItemProperty -Path $keyPath -Name "Background" -Value "$($color.R) $($color.G) $($color.B)" -Type String
            $accentKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"
            if (-not (Test-Path $accentKey)) {
                New-Item -Path $accentKey -Force | Out-Null
            }
            Set-ItemProperty -Path $accentKey -Name "AccentColorMenu" -Value ("0xFF" + ("{0:X2}{1:X2}{2:X2}" -f $color.R, $color.G, $color.B)) -Type DWord -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $accentKey -Name "StartColorMenu" -Value ("0xFF" + ("{0:X2}{1:X2}{2:X2}" -f $color.R, $color.G, $color.B)) -Type DWord -ErrorAction SilentlyContinue

            $immersiveColorsKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"
            Set-ItemProperty -Path $immersiveColorsKey -Name "AccentPalette" -Value ([byte[]](0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)) -Type Binary -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $immersiveColorsKey -Name "AccentColor" -Value ("0xFF" + ("{0:X2}{1:X2}{2:X2}" -f $color.R, $color.G, $color.B)) -Type DWord -ErrorAction SilentlyContinue

            [System.Windows.Forms.MessageBox]::Show("Background/Accent color set. Changes might require logging off/back on or restarting Explorer.", "Color Set", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        } catch {
            [System.Windows.Forms.MessageBox]::Show("Failed to set color: $($_.Exception.Message)", "Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        }
    }
}

# Toggle Dark Mode (Registry)
$toggleDarkMode_Click = {
    try {
        $appsUseLightTheme = Get-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "AppsUseLightTheme" -ErrorAction Stop
        $currentValue = $appsUseLightTheme.AppsUseLightTheme

        if ($currentValue -eq 1) {
            Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "AppsUseLightTheme" -Value 0
            Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "SystemUsesLightTheme" -Value 0
            [System.Windows.Forms.MessageBox]::Show("Switched to Dark Mode for Apps and System.", "Dark Mode", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        } else {
            Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "AppsUseLightTheme" -Value 1
            Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize" -Name "SystemUsesLightTheme" -Value 1
            [System.Windows.Forms.MessageBox]::Show("Switched to Light Mode for Apps and System.", "Light Mode", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        }
    } catch {
        [System.Windows.Forms.MessageBox]::Show("Failed to toggle dark mode: $($_.Exception.Message)", "Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
    }
}

# Set Lock Screen Image (Registry)
$setLockScreen_Click = {
    $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
    $openFileDialog.Filter = "Image Files|*.jpg;*.jpeg;*.png;*.bmp"
    $openFileDialog.Title = "Select Lock Screen Image"

    $result = $openFileDialog.ShowDialog()

    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        $imagePath = $openFileDialog.FileName
        try {
            $lockScreenKey = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization"
             if (-not (Test-Path $lockScreenKey)) {
                New-Item -Path $lockScreenKey -Force | Out-Null
            }
            Set-ItemProperty -Path $lockScreenKey -Name "LockScreenImage" -Value $imagePath -Type String

            $currentUserLockScreenKey = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Lock Screen"
            if (-not (Test-Path $currentUserLockScreenKey)) {
                New-Item -Path $currentUserLockScreenKey -Force | Out-Null
            }
            Set-ItemProperty -Path $currentUserLockScreenKey -Name "SlideshowEnabled" -Value 0 -Type DWord -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $currentUserLockScreenKey -Name "PicturePath" -Value $imagePath -Type String -ErrorAction SilentlyContinue

            [System.Windows.Forms.MessageBox]::Show("Lock screen image set. A system restart might be required.", "Lock Screen Set", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        } catch {
            [System.Windows.Forms.MessageBox]::Show("Failed to set lock screen image: $($_.Exception.Message)", "Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        }
    }
}

# Set Desktop Background Image (Registry)
$setDesktopBg_Click = {
    $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
    $openFileDialog.Filter = "Image Files|*.jpg;*.jpeg;*.png;*.bmp"
    $openFileDialog.Title = "Select Desktop Background Image"

    $result = $openFileDialog.ShowDialog()

    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        $imagePath = $openFileDialog.FileName
        try {
            $wallpaperKey = "HKCU:\Control Panel\Desktop"
            Set-ItemProperty -Path $wallpaperKey -Name "Wallpaper" -Value $imagePath -Type String
            Set-ItemProperty -Path $wallpaperKey -Name "WallpaperStyle" -Value "6" -Type String # Fit
            Set-ItemProperty -Path $wallpaperKey -Name "TileWallpaper" -Value "0" -Type String

            Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Wallpaper {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool SystemParametersInfo(uint uiAction, uint uiParam, string pvParam, uint fWinIni);
}
"@
            [Wallpaper]::SystemParametersInfo(0x0014, 0, $imagePath, 0x0001 -bor 0x0002)

            [System.Windows.Forms.MessageBox]::Show("Desktop background set.", "Background Set", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        } catch {
            [System.Windows.Forms.MessageBox]::Show("Failed to set desktop background: $($_.Exception.Message)", "Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        }
    }
}

# Apply Color Theme (Registry)
$applyColorTheme_Click = {
    try {
        $personalizeKey = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"

        $appsUseLightTheme = Get-ItemProperty -Path $personalizeKey -Name "AppsUseLightTheme" -ErrorAction SilentlyContinue
        $systemUsesLightTheme = Get-ItemProperty -Path $personalizeKey -Name "SystemUsesLightTheme" -ErrorAction SilentlyContinue

        $currentAppValue = if ($appsUseLightTheme) { $appsUseLightTheme.AppsUseLightTheme } else { 1 }
        $currentSystemValue = if ($systemUsesLightTheme) { $systemUsesLightTheme.SystemUsesLightTheme } else { 1 }

        if ($currentAppValue -eq 1 -and $currentSystemValue -eq 1) {
            Set-ItemProperty -Path $personalizeKey -Name "AppsUseLightTheme" -Value 0
            Set-ItemProperty -Path $personalizeKey -Name "SystemUsesLightTheme" -Value 0
            [System.Windows.Forms.MessageBox]::Show("Applied Dark Color Theme.", "Theme Applied", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        } else {
            Set-ItemProperty -Path $personalizeKey -Name "AppsUseLightTheme" -Value 1
            Set-ItemProperty -Path $personalizeKey -Name "SystemUsesLightTheme" -Value 1
            [System.Windows.Forms.MessageBox]::Show("Applied Light Color Theme.", "Theme Applied", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        }
    } catch {
         [System.Windows.Forms.MessageBox]::Show("Failed to apply color theme: $($_.Exception.Message)", "Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
    }
}

# Toggle Desktop Icons (Registry)
$toggleDesktopIcons_Click = {
    try {
        $desktopKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
        $hideIconsValue = Get-ItemProperty -Path $desktopKey -Name "HideIcons" -ErrorAction SilentlyContinue

        # Determine current state (default is 0/False = Icons Shown)
        $currentHideValue = if ($hideIconsValue) { $hideIconsValue.HideIcons } else { 0 }

        if ($currentHideValue -eq 1) {
            # Icons are currently hidden, show them
            Set-ItemProperty -Path $desktopKey -Name "HideIcons" -Value 0
            $message = "Desktop icons are now SHOWN."
        } else {
            # Icons are currently shown, hide them
            Set-ItemProperty -Path $desktopKey -Name "HideIcons" -Value 1
            $message = "Desktop icons are now HIDDEN."
        }

        # Refresh the desktop to apply the change
        # This sends a broadcast message to all windows to refresh (similar to F5)
        Add-Type -TypeDefinition @"
            using System;
            using System.Runtime.InteropServices;
            public class ExplorerHelper {
                [DllImport("shell32.dll", CharSet = CharSet.Auto)]
                public static extern int SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);

                public static void RefreshDesktop() {
                    SHChangeNotify(0x8000000, 0x1000, IntPtr.Zero, IntPtr.Zero); // SHCNE_ASSOCCHANGED, SHCNF_IDLIST
                }
            }
"@
        [ExplorerHelper]::RefreshDesktop()

        [System.Windows.Forms.MessageBox]::Show($message, "Desktop Icons", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)

    } catch {
        [System.Windows.Forms.MessageBox]::Show("Failed to toggle desktop icons: $($_.Exception.Message)", "Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
    }
}


# --- Create UI Elements ---

$topPosition = 10
Create-Label -Text "Themes & Modes" -Top $topPosition
$topPosition += 30
Create-Button -Text "Change Theme (.theme/.deskthemepack)" -OnClick $changeTheme_Click -Top $topPosition
$topPosition += 50
Create-Button -Text "Toggle Dark/Light Mode" -OnClick $toggleDarkMode_Click -Top $topPosition
$topPosition += 50
Create-Button -Text "Apply Color Theme (Apps & System)" -OnClick $applyColorTheme_Click -Top $topPosition
$topPosition += 70

Create-Label -Text "Colors" -Top $topPosition
$topPosition += 30
Create-Button -Text "Set Background/Accent Color" -OnClick $setBgColor_Click -Top $topPosition
$topPosition += 70

Create-Label -Text "Images" -Top $topPosition
$topPosition += 30
Create-Button -Text "Set Lock Screen Image" -OnClick $setLockScreen_Click -Top $topPosition
$topPosition += 50
Create-Button -Text "Set Desktop Background Image" -OnClick $setDesktopBg_Click -Top $topPosition
$topPosition += 70 # Add space before new section

Create-Label -Text "Desktop" -Top $topPosition
$topPosition += 30
Create-Button -Text "Toggle Desktop Icons (Show/Hide)" -OnClick $toggleDesktopIcons_Click -Top $topPosition


# Show the form
$form.ShowDialog() | Out-Null
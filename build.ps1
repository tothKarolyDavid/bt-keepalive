# Build BTKeepAlive.exe (run from project root with venv activated)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$iconArg = @()
if (Test-Path "assets\icon.ico") {
    $iconArg = @("--icon", "assets\icon.ico")
}

python -m PyInstaller `
    --onefile `
    --windowed `
    --name BTKeepAlive `
    @iconArg `
    --hidden-import=pystray._win32 `
    --hidden-import=btkeepalive.win_tray `
    --collect-submodules btkeepalive `
    launcher.py

Write-Host "`nBuilt: $root\dist\BTKeepAlive.exe"

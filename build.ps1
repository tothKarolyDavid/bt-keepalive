# Build BTKeepAlive.exe (run from project root with venv activated)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

python scripts/generate_icon.py

python -m PyInstaller --noconfirm BTKeepAlive.spec

Write-Host "`nBuilt: $root\dist\BTKeepAlive.exe"

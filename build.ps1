# build.ps1 — Build BionicReader.exe
# Usage: .\build.ps1
# Output: dist\BionicReader.exe

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = $PSScriptRoot
$SRC  = Join-Path $ROOT "src"
$DIST = Join-Path $ROOT "dist"
$BUILD = Join-Path $ROOT "build"

Write-Host ""
Write-Host "  BIONIC READER -- build" -ForegroundColor Yellow
Write-Host "  ----------------------" -ForegroundColor DarkYellow

# 1. Check Python
Write-Host ""
Write-Host "  [1/3] Python version..." -ForegroundColor Cyan
$pyver = python --version 2>&1
Write-Host "        $pyver"

# 2. Install deps
Write-Host ""
Write-Host "  [2/3] Installing dependencies..." -ForegroundColor Cyan
pip install -r "$ROOT\requirements.txt" --upgrade -q

# 3. Run PyInstaller via python -m (avoids PATH issues)
Write-Host ""
Write-Host "  [3/3] Running PyInstaller..." -ForegroundColor Cyan

$cmd = "python -m PyInstaller"
$cmd += " --onefile"
$cmd += " --windowed"
$cmd += " --name=BionicReader"
$cmd += " --distpath=`"$DIST`""
$cmd += " --workpath=`"$BUILD`""
$cmd += " --specpath=`"$ROOT`""
$cmd += " --collect-all=PyQt6"
$cmd += " --collect-all=fitz"
$cmd += " --hidden-import=PyQt6.QtCore"
$cmd += " --hidden-import=PyQt6.QtGui"
$cmd += " --hidden-import=PyQt6.QtWidgets"
$cmd += " --hidden-import=fitz"
$cmd += " --paths=`"$SRC`""
$cmd += " `"$SRC\main.py`""

Write-Host "  Running: $cmd" -ForegroundColor DarkGray
Invoke-Expression $cmd

# Report
$exe = Join-Path $DIST "BionicReader.exe"
if (Test-Path $exe) {
    $sizeMB = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "  Build succeeded!" -ForegroundColor Green
    Write-Host "  Output : $exe" -ForegroundColor White
    Write-Host "  Size   : $sizeMB MB" -ForegroundColor DarkGray
    Write-Host "  Run    : .\dist\BionicReader.exe" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "  Build FAILED -- BionicReader.exe not found in dist/" -ForegroundColor Red
    exit 1
}

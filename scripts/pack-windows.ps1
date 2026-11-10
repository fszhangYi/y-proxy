# Build Y-Proxy Windows onefile exe with official CPython packvenv (never conda).
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root 'build\packvenv\Scripts\python.exe'
if (-not (Test-Path $Py)) {
    throw "Missing $Py — create packvenv with official CPython first."
}

& $Py -c @"
import sys
p = sys.base_prefix.lower().replace('/', '\\\\')
assert not any(x in p for x in ('\\\\miniconda', '\\\\anaconda', '\\\\conda\\\\')), sys.base_prefix
print('ok', sys.version.split()[0], sys.base_prefix)
"@

& $Py (Join-Path $Root 'packaging\make_icon.py')
Push-Location $Root
try {
    & $Py -m PyInstaller --noconfirm --clean (Join-Path $Root 'packaging\y_proxy_win.spec')
} finally {
    Pop-Location
}

$exe = Get-ChildItem (Join-Path $Root 'dist') -Filter 'Y-Proxy-*.exe' |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $exe) { throw 'No Y-Proxy-*.exe in dist/' }
Write-Host "Built: $($exe.FullName) ($([math]::Round($exe.Length/1MB,1)) MB)"

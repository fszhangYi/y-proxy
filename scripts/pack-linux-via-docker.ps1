# Build Y-Proxy Linux x86_64 AppImage inside Ubuntu 20.04 (Docker Desktop).
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

docker version | Out-Null
$env:DOCKER_BUILDKIT = '1'

$out = Join-Path $Root 'dist-release'
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
New-Item -ItemType Directory -Force -Path $out | Out-Null

Write-Host 'Building AppImage via ubuntu:20.04 ...'
docker build `
  -f docker/Dockerfile.pack `
  --target export `
  -o "type=local,dest=$out" `
  .

Write-Host '--- artifacts ---'
Get-ChildItem -Recurse $out | Select-Object FullName, Length

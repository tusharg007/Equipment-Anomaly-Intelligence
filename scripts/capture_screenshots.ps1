$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = "$projectRoot"

Push-Location $projectRoot
try {
    python scripts/capture_screenshots.py
}
finally {
    Pop-Location
}

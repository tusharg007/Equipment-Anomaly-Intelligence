$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = "$projectRoot;$projectRoot\src"
Push-Location $projectRoot
try {
    python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
}
finally {
    Pop-Location
}

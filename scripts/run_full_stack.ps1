$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = "$projectRoot;$projectRoot\src"

Push-Location $projectRoot
try {
    Write-Host "`n==> Starting Docker services" -ForegroundColor Cyan
    docker compose up -d

    Write-Host "`n==> Loading CSV outputs into PostgreSQL" -ForegroundColor Cyan
    python -m src.load_to_postgres

    Push-Location (Join-Path $projectRoot 'dbt_mfg')
    try {
        Write-Host "`n==> Running dbt debug" -ForegroundColor Cyan
        dbt debug --profiles-dir .
        Write-Host "`n==> Running dbt models" -ForegroundColor Cyan
        dbt run --profiles-dir .
        Write-Host "`n==> Running dbt tests" -ForegroundColor Cyan
        dbt test --profiles-dir .
    }
    finally {
        Pop-Location
    }

    Write-Host "`nFastAPI:  http://localhost:8000" -ForegroundColor Green
    Write-Host "Metabase: http://localhost:3000" -ForegroundColor Green
}
finally {
    Pop-Location
}

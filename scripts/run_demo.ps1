$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = "$projectRoot;$projectRoot\src"

function Invoke-Step {
    param(
        [string]$Label,
        [scriptblock]$Action
    )
    Write-Host "`n==> $Label" -ForegroundColor Cyan
    & $Action
}

Push-Location $projectRoot
try {
    foreach ($dir in @('data\raw','data\processed','data\predictions','models\defect_model','models\anomaly_model','reports')) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }

    Invoke-Step 'Generate synthetic data' { python -m src.generate_synthetic_data }

    if (Test-Path 'src\data_quality_checks.py') {
        Invoke-Step 'Run data quality checks' { python -m src.data_quality_checks }
    }

    Invoke-Step 'Train defect model' { python -m src.train_defect_model }
    Invoke-Step 'Detect anomalies' { python -m src.detect_anomalies }
    Invoke-Step 'Score downtime risk' { python -m src.downtime_risk_scoring }

    if (Test-Path 'src\model_monitoring.py') {
        Invoke-Step 'Run model monitoring' { python -m src.model_monitoring }
    }

    if (Test-Path 'src\smoke_test.py') {
        Invoke-Step 'Run smoke test' { python -m src.smoke_test }
    }

    Invoke-Step 'Run pytest' { python -m pytest tests -q }
    Write-Host "`nDemo pipeline completed successfully." -ForegroundColor Green
}
finally {
    Pop-Location
}

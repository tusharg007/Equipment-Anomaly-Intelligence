$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$required = @(
    'data\raw\machines.csv',
    'data\raw\sensor_readings.csv',
    'data\processed\ml_training_dataset.csv',
    'data\predictions\defect_predictions.csv',
    'data\predictions\anomaly_scores.csv',
    'data\predictions\downtime_risk_scores.csv',
    'reports\model_evaluation.md'
)

$missing = @()
foreach ($relativePath in $required) {
    $fullPath = Join-Path $projectRoot $relativePath
    if (Test-Path $fullPath) {
        Write-Host "OK  $relativePath" -ForegroundColor Green
    }
    else {
        Write-Host "MISS $relativePath" -ForegroundColor Yellow
        $missing += $relativePath
    }
}

if ($missing.Count -gt 0) {
    throw "Missing required outputs: $($missing -join ', ')"
}

Write-Host "`nAll required outputs are present." -ForegroundColor Green

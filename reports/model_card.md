# Model Card

## Model Purpose
This production-oriented prototype estimates defect risk at the machine-batch level to support quality prediction and earlier manufacturing investigation.

## Target Variable
`defect_flag` indicates whether a synthetic machine-batch quality check contained a defect.

## Features
- Sensor behavior: temperature, vibration, pressure, cycle time, energy consumption
- Stability indicators: pressure instability, anomaly signal, cycle time drift, pressure deviation
- Operating context: shift, line, maintenance recency
- Asset context: machine age, baseline health, and previous downtime

## Modeling Approach
- Logistic Regression baseline
- RandomForest
- Optional XGBoost when installed
- Isolation Forest is used separately for equipment anomaly detection rather than the supervised quality model

## Metrics
Metrics are written to:
- `reports/model_evaluation.md`
- `reports/metrics.json`
- `reports/classification_report.json`
- `reports/confusion_matrix.csv`

## Limitations
- The dataset is synthetic and designed for workflow realism rather than plant validation
- Labels are generated from modeled relationships plus randomness
- Performance should be described as prototype validation, not operational accuracy

## Responsible Use
Use outputs as human-in-the-loop decision support for quality review, not for autonomous scrap or shutdown decisions.

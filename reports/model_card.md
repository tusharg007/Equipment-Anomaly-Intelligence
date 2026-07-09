# Model Card

## Model Purpose
This manufacturing analytics prototype estimates defect risk at the machine-batch level so manufacturing, quality, and maintenance teams can prioritize investigation earlier.

## Target Variable
`defect_flag` indicates whether the synthetic quality check for a machine and batch included a defect.

## Features
- Sensor behavior: temperature, vibration, pressure, cycle time, energy consumption
- Stability indicators: pressure instability, anomaly signal, cycle time drift
- Operating context: shift, line, maintenance recency
- Asset context: machine age and previous downtime minutes
- Preprocessing and engineered features are derived from synthetic machine, batch, downtime, and maintenance data

## Metrics
Metrics are generated in `reports/model_evaluation.md` after training and include ROC-AUC, precision, recall, F1, and confusion matrix counts.

## Modeling Approach
- Baseline model: Logistic Regression
- Tree-based model: RandomForest
- Optional model: XGBoost if installed
- Supporting method: Isolation Forest for separate anomaly detection workflow

## Limitations
- The dataset is synthetic and calibrated for interview-defensible realism, not for plant deployment.
- Labels are generated from simulated rules plus randomness, so performance should not be interpreted as plant-validated accuracy.
- Feature drift, sensor outages, and operator behavior are simplified.
- This model is best positioned as a prototype for experimentation, analytics discussion, and workflow demonstration.

## Responsible Use
Use predictions to flag higher-risk conditions for human review, not to automate scrap, shutdown, or operator performance decisions.

## Human-In-The-Loop Recommendation
Require manufacturing or quality engineers to review predicted high-risk batches alongside raw sensor context, maintenance notes, and recent downtime events before action.

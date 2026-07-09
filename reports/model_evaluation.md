# Defect Model Evaluation

This production-oriented prototype compares baseline and tree-based quality prediction models on synthetic manufacturing data.

## Model Comparison

| model | roc_auc | precision | recall | f1 | composite_score |
| --- | --- | --- | --- | --- | --- |
| LogisticRegression | 0.7562 | 0.2832 | 0.6729 | 0.3986 | 0.6132 |
| RandomForest | 0.7473 | 0.3031 | 0.6212 | 0.4074 | 0.6113 |

## Selected Model

`LogisticRegression` was selected using a blend of ROC-AUC and F1 to balance ranking quality and actionable classification performance.

## Confusion Matrix

| index | predicted_0 | predicted_1 |
| --- | --- | --- |
| actual_0 | 1551 | 724 |
| actual_1 | 139 | 286 |

## Top Feature Importance

| feature | importance |
| --- | --- |
| num__avg_vibration | 0.8114 |
| num__anomaly_signal | 0.4203 |
| num__quality_risk_index | 0.3493 |
| num__avg_temperature | 0.2816 |
| num__machine_age_years | 0.2088 |
| cat__shift_Evening | 0.1772 |
| num__baseline_health_score | 0.1552 |
| num__previous_downtime_minutes | 0.1365 |
| cat__line_id_L2 | 0.1138 |
| cat__shift_Day | 0.113 |

## Notes

- The dataset is synthetic and designed for manufacturing analytics prototyping rather than plant-validated deployment.
- XGBoost is optional and only evaluated if the dependency is installed.
- Outputs include metrics JSON, classification report JSON, confusion matrix CSV, feature importance, predictions, and a joblib model artifact.
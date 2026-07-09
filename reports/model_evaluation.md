# Defect Model Evaluation

This prototype compares baseline defect classification approaches using synthetic manufacturing data.

## Model Comparison

| model | roc_auc | precision | recall | f1 | tn | fp | fn | tp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LogisticRegression | 0.7286 | 0.2028 | 0.6352 | 0.3075 | 1588 | 794 | 116 | 202 |
| RandomForest | 0.7185 | 0.23 | 0.5252 | 0.3199 | 1823 | 559 | 151 | 167 |

## Selected Model

`LogisticRegression` was selected based on highest ROC-AUC on the holdout split.

## Top Feature Importance

| feature | importance |
| --- | --- |
| num__last_maintenance_days_ago | 0.516 |
| num__maintenance_recency_score | 0.4851 |
| num__quality_risk_index | 0.3765 |
| num__avg_temperature | 0.2535 |
| num__anomaly_signal | 0.2511 |
| cat__line_id_L1 | 0.1977 |
| num__pressure_instability | 0.1496 |
| num__machine_age_years | 0.1275 |
| num__avg_vibration | 0.1239 |
| cat__shift_Day | 0.1026 |

## Notes

- The dataset is synthetic and designed to simulate manufacturing relationships rather than represent plant truth.
- Thresholds are kept at 0.5 for simplicity in the prototype.
- XGBoost is optional; the script safely falls back to baseline models if it is unavailable.
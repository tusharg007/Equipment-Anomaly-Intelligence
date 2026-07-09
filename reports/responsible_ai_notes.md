# Responsible AI Notes

## Synthetic Data Limitations
This production-oriented prototype uses synthetic manufacturing data designed to simulate plausible relationships between process variables, quality outcomes, anomalies, and downtime. It is useful for workflow validation, analytics engineering discussion, and model experimentation, but it is not evidence of real plant behavior.

## False Positive And False Negative Risks
- False positives may trigger unnecessary inspection or maintenance review
- False negatives may delay escalation of real process instability in a future real-data version
- Thresholds should be calibrated carefully if the workflow is ever adapted to real data

## Monitoring Plan
- Track alert volume, predicted defect rates, anomaly counts, and risk-band distributions
- Monitor whether the same machines dominate outputs because of synthetic assumptions rather than operational evidence
- Revisit preprocessing, feature engineering, and dashboard definitions whenever the modeled process changes

## Bias And Governance Considerations
- Shift and operator fields are included for manufacturing realism, not workforce evaluation
- Outputs should remain explanatory and review-oriented
- Any move beyond synthetic data should include governance for access control, auditability, and decision ownership

## Human-In-The-Loop Decision Support
Predictions, anomaly flags, and downtime risk bands should support engineering judgment, not replace it.

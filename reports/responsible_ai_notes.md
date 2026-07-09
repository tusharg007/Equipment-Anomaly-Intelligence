# Responsible AI Notes

## Synthetic Data Limitations
This prototype uses synthetic manufacturing data designed to simulate plausible relationships between process variables, quality outcomes, and downtime. It is useful for workflow demonstration, analytics automation, feature engineering discussion, model validation practice, and dashboard prototyping, but it is not evidence of plant performance.

## False Positive and False Negative Risks
- False positives can trigger unnecessary inspections, maintenance work, or operator concern.
- False negatives can hide emerging process instability and delay intervention.
- Because this is a prototype, thresholds should be tuned cautiously even in a simulated environment.

## Monitoring Plan
- Track defect prediction rate, alert volume, and downstream investigation outcomes.
- Review whether high-risk scores cluster on certain machines due to synthetic assumptions instead of operational evidence.
- Re-train or recalibrate when process conditions, product mix, or maintenance policies change.
- Confirm that preprocessing logic, feature engineering assumptions, and dashboard definitions still match the manufacturing process being modeled.

## Bias and Governance Considerations
- Shift effects are modeled only as process variance and should not be interpreted as worker performance judgment.
- Operator team fields are included for workflow realism, not for ranking labor performance.
- Governance should document data lineage, review access, and decision ownership before any real deployment work.

## Decision Support Boundary
Predictions should support engineering judgment, not replace it. Shutdown decisions, quality holds, and maintenance prioritization should remain human-led.

# Project Status

## Overall State
The project is in a verified, runnable local prototype state for synthetic manufacturing analytics. The Python pipeline, PostgreSQL loading, dbt transformations/tests, FastAPI endpoints, Metabase dashboard workflow, and screenshot generation have all been exercised locally.

## Verified Components
- Synthetic manufacturing data generation for machines, batches, sensors, quality checks, downtime events, and maintenance logs
- Processed ML training dataset generation in `data/processed/ml_training_dataset.csv`
- Defect prediction training with Logistic Regression, RandomForest, and optional XGBoost fallback support
- Isolation Forest plus rule-based anomaly detection outputs
- Downtime risk scoring and maintenance priority outputs
- Local Python demo pipeline execution
- Smoke test execution
- `pytest` execution
- Docker PostgreSQL container startup
- PostgreSQL data loading through `python -m src.load_to_postgres`
- dbt validation:
  - `dbt debug` passed
  - `dbt run` passed with `PASS=14 WARN=0 ERROR=0`
  - `dbt test` passed with `PASS=31 WARN=0 ERROR=0`
- Verified dbt marts in schema `analytics`:
  - `mart_machine_health`
  - `mart_quality_risk`
  - `mart_oee_dashboard`
  - `mart_maintenance_priority`
- FastAPI docs capture saved at `assets/api_docs.png`
- Metabase running locally at `http://127.0.0.1:3000`
- Metabase connected to PostgreSQL using host `postgres`, port `5432`, database `manufacturing`
- Metabase dashboard created successfully
- Metabase dashboard screenshots saved at:
  - `assets/metabase_dashboard_top.png`
  - `assets/metabase_dashboard_bottom.png`

## What The Project Demonstrates
- AI/ML experimentation for manufacturing quality prediction
- Feature engineering and preprocessing on synthetic industrial-style data
- Unsupervised anomaly detection for equipment monitoring
- Heuristic downtime risk scoring and maintenance prioritization
- Analytics engineering with PostgreSQL and dbt
- API and dashboard delivery for local stakeholder-style review
- Reproducibility through scripts, tests, and local verification steps

## Honest Limitations
- All manufacturing data is synthetic
- This is a production-oriented prototype, not a real plant deployment
- No claim should be made that the system was used in a live GM or factory environment
- Downtime risk scoring is decision support logic and requires calibration against real plant history before operational use
- Dashboard and API flows are locally verified prototype workflows, not a production hosting setup

## Recommended Usage
Use this project for:
- portfolio demonstration
- interview walkthroughs
- manufacturing analytics discussion
- AI/ML pipeline storytelling
- analytics engineering and dashboarding examples

Do not use this project to claim:
- real plant deployment
- real business savings
- real maintenance or downtime reduction
- production-calibrated operating thresholds

## Next Practical Improvements
- Add calibration analysis for defect and downtime risk scores
- Add experiment tracking and run metadata logging
- Add database-backed API reads instead of relying primarily on local artifacts
- Add richer Metabase dashboard cards and drill-down filters
- Add deployment hardening only if the project scope expands beyond prototype use

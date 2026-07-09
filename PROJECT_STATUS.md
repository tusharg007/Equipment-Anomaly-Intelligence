# Project Status

## What Currently Works
- Synthetic manufacturing data generation for machines, batches, sensors, quality checks, downtime, and maintenance
- Processed ML training dataset generation in `data/processed/ml_training_dataset.csv`
- Defect prediction training with Logistic Regression, RandomForest, and optional XGBoost
- Isolation Forest plus rule-based anomaly detection
- Downtime risk scoring and maintenance priority outputs
- PostgreSQL loader with environment-variable configuration, rerun-safe replace logic, and index creation
- dbt staging, intermediate, and mart models for manufacturing analytics
- FastAPI endpoints for health, KPIs, machine health, anomalies, maintenance priority, and defect-risk inference
- Smoke test and pytest coverage for the core pipeline

## Partially Implemented
- Docker and docker-compose are ready, but full local service validation depends on installing Python/dbt dependencies and starting containers
- dbt tests are defined but were not executed in this environment because PostgreSQL/dbt services were not started here
- CI workflow is lightweight and GitHub-ready, but not exercised in this local sandbox

## What Was Broken And Fixed
- Added structured configuration via `.env` and `src/config.py`
- Reworked data generation to create `ml_training_dataset.csv` and stronger synthetic relationships
- Hardened training outputs to include metrics JSON, classification report JSON, confusion matrix CSV, and model artifacts
- Upgraded anomaly detection output to include timestamp-level anomaly scores, flags, and reasons
- Expanded downtime risk scoring to include explainability fields and a maintenance priority file
- Added API, tests, Dockerfile, GitHub Actions workflow, and documentation artifacts missing from the original MVP
- Updated Makefile commands so they map to real files and entrypoints

## How To Run End-To-End
1. `python -m pip install -r requirements.txt`
2. Optional: copy `.env.example` to `.env`
3. `make generate-data`
4. `make train`
5. `make anomalies`
6. `make risk`
7. `make smoke-test`
8. Optional database and analytics steps:
   - `make up`
   - `make load-db`
   - `make dbt-run`
   - `make api`

## Remaining Limitations
- The data is synthetic and cannot validate plant performance claims
- Risk scores and maintenance recommendations are heuristic decision-support logic
- API reads generated artifacts rather than a fully orchestrated online feature store
- No authentication or deployment orchestration is included

## Production-Oriented Next Improvements
- Add data versioning and richer logging for pipeline runs
- Add calibration analysis for defect probabilities
- Add scenario-based synthetic generation controls for more controlled experiments
- Add API pagination and database-backed query paths
- Add scheduled batch pipeline execution and artifact tracking

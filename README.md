# Manufacturing Quality & Equipment Anomaly Intelligence Platform

A focused manufacturing analytics prototype built for a General Motors AI/ML Intern-style project discussion. The project uses synthetic manufacturing data to demonstrate data preprocessing, feature engineering, quality prediction, equipment anomaly detection, downtime risk scoring, dashboarding, and local analytics automation using Python, PostgreSQL, dbt, and Metabase.

## Project Summary
This project simulates a manufacturing environment where machine sensor behavior, batch quality outcomes, maintenance activity, and downtime events can be analyzed together. The goal is not to claim plant-ready performance, but to show a practical end-to-end AI/ML and analytics workflow that is realistic enough to discuss in an internship interview.

## Business Problem
Manufacturing teams often need faster ways to identify process drift, prioritize machine inspections, and connect line performance with quality and downtime outcomes. This prototype demonstrates how machine telemetry and batch-level features can support:
- earlier identification of quality risk
- machine-level anomaly detection
- downtime risk prioritization
- operational dashboarding for efficiency review

## Synthetic Data Notice
All data in this repository is synthetic. It is intentionally designed to simulate realistic manufacturing relationships such as:
- higher vibration and temperature increasing defect probability
- pressure instability increasing quality risk
- cycle time drift contributing to defect likelihood
- older machines showing more anomaly-prone behavior
- recent maintenance lowering downtime probability
- night shift showing slightly higher process variance

This makes the project useful for experimentation, feature engineering, model validation, and dashboard prototyping, but not for measuring actual plant performance.

## Tech Stack
- Python
- Pandas and NumPy for preprocessing and synthetic data generation
- scikit-learn for Logistic Regression, RandomForest, Isolation Forest, and model validation
- XGBoost as an optional boosted-tree model if installed
- PostgreSQL for local data storage
- dbt for analytics modeling
- Metabase for dashboarding

## Architecture
- `src/generate_synthetic_data.py` creates synthetic machines, batches, sensors, quality, maintenance, and downtime datasets
- `src/load_to_postgres.py` loads raw, processed, and prediction CSVs into PostgreSQL
- `dbt_mfg/` transforms operational data into analytics-ready staging, intermediate, and mart layers
- `src/train_defect_model.py` trains defect prediction models and writes evaluation metrics plus predictions
- `src/detect_anomalies.py` scores machine behavior with Isolation Forest and z-score based anomaly logic
- `src/downtime_risk_scoring.py` generates heuristic downtime risk bands and maintenance recommendations
- `metabase/dashboard_queries.sql` supports manufacturing KPI, quality, machine health, and OEE-style dashboards

## GM Role Alignment
This prototype maps well to common General Motors AI/ML intern responsibilities around analytics, automation, manufacturing data, and model experimentation:
- `AI/ML and model experimentation`: compares Logistic Regression, RandomForest, and optional XGBoost for defect prediction, with ROC-AUC, precision, recall, F1, and confusion matrix reporting
- `Data preprocessing and feature engineering`: builds machine-batch features from sensor readings, maintenance history, cycle time drift, pressure instability, and downtime context
- `Manufacturing analytics`: focuses on quality risk, anomaly detection, downtime prioritization, and line-level efficiency signals instead of generic ML examples
- `Automation and reproducibility`: uses Python scripts, a Makefile, dbt models, and a smoke test to keep the local workflow structured and repeatable
- `Dashboarding and business communication`: prepares marts and SQL for Metabase so engineering or operations stakeholders can review machine health and operational KPIs
- `Model validation mindset`: documents that the dataset is synthetic, includes evaluation outputs, and positions predictions as decision support rather than automated plant control

## Project Structure
```text
manufacturing-quality-anomaly-platform/
|-- data/
|-- dbt_mfg/
|-- metabase/
|-- reports/
|-- src/
|-- docker-compose.yml
|-- Makefile
|-- README.md
`-- requirements.txt
```

## How To Run
1. Install Python dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
   Optional:
   ```bash
   python -m pip install xgboost
   ```
2. Start local services:
   ```bash
   docker compose up -d
   ```
3. Set PostgreSQL environment variables if you want values other than the defaults:
   - `POSTGRES_HOST=localhost`
   - `POSTGRES_PORT=5432`
   - `POSTGRES_DB=manufacturing`
   - `POSTGRES_USER=manufacturing`
   - `POSTGRES_PASSWORD=manufacturing`
4. Generate synthetic data:
   ```bash
   python src/generate_synthetic_data.py
   ```
5. Load CSVs to PostgreSQL:
   ```bash
   python src/load_to_postgres.py
   ```
6. Run dbt:
   ```bash
   dbt run --project-dir dbt_mfg --profiles-dir dbt_mfg --profile dbt_mfg
   ```
7. Train the defect model:
   ```bash
   python src/train_defect_model.py
   ```
8. Generate anomaly scores and downtime risk scores:
   ```bash
   python src/detect_anomalies.py
   python src/downtime_risk_scoring.py
   ```
9. Run the smoke test:
   ```bash
   python src/smoke_test.py
   ```

Or use the Makefile:
```bash
make setup
make up
make generate-data
make load-db
make dbt-run
make train
make anomalies
make risk
make smoke-test
make all
```

## ML and Analytics Workflow
- Data preprocessing standardizes synthetic manufacturing records into raw and processed datasets
- Feature engineering creates quality and reliability signals such as cycle time drift, pressure instability, maintenance recency, anomaly intensity, and previous downtime
- Defect prediction compares baseline and tree-based classifiers
- Anomaly detection combines Isolation Forest with rule-based statistical checks
- Downtime risk scoring converts operational indicators into machine-level prioritization bands
- Dashboard queries expose manufacturing KPIs, defect trends, machine health, and OEE-style metrics for review

## Interview Explanation
### 1. Problem Statement
I wanted to build a manufacturing analytics prototype that shows how machine telemetry and production context can support quality prediction, anomaly detection, and downtime prioritization in a local, interview-defensible workflow.

### 2. Data Pipeline
I generated synthetic manufacturing data for machines, production batches, sensor readings, quality checks, downtime events, and maintenance logs. Then I used Python for preprocessing, PostgreSQL for storage, and dbt to organize the analytics layer into staging, intermediate, and mart models.

### 3. ML Models
For quality prediction, I trained Logistic Regression and RandomForest models, with XGBoost included as an optional model when available. I evaluated models using ROC-AUC, precision, recall, F1, and confusion matrix results. For anomaly detection, I used Isolation Forest plus z-score based rules. For downtime prioritization, I created a transparent heuristic risk score using anomaly counts, sensor patterns, machine age, maintenance recency, and downtime history.

### 4. Dashboard and Business Value
The PostgreSQL, dbt, and Metabase setup supports dashboards for machine health, quality risk, downtime trends, maintenance priority, and OEE-style operational review. The prototype is meant to help teams surface higher-risk machines earlier and create a better daily discussion between operations, quality, and reliability stakeholders.

### 5. Limitations and Next Improvements
The dataset is synthetic, so the project demonstrates workflow design rather than plant-validated performance. A next step would be testing the pipeline on historical plant data, improving feature calibration, validating thresholds with engineers, and expanding the dashboard with more detailed line-level drill-downs.

## Dashboard Setup
- Connect Metabase to the local PostgreSQL container
- Use the curated SQL in `metabase/dashboard_queries.sql`
- Build dashboards for machine health, quality risk, OEE, and maintenance priority
- Re-run `python src/load_to_postgres.py` after training or scoring if you want prediction outputs refreshed in PostgreSQL

## Prototype Limitations
- Synthetic data is useful for demonstrating workflow, not validating plant performance
- Risk scores are heuristics, not calibrated maintenance policies
- The project is a local prototype, not a production deployment
- OEE is simplified and should be refined with plant-specific definitions and business rules

## Key Outputs
- Model evaluation: `reports/model_evaluation.md`
- Model card: `reports/model_card.md`
- Responsible AI notes: `reports/responsible_ai_notes.md`
- Business impact summary: `reports/business_impact_summary.md`
- Dashboard SQL: `metabase/dashboard_queries.sql`
- Smoke test: `src/smoke_test.py`

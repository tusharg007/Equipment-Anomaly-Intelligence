# Architecture

## Overview
This repository is a production-oriented prototype for manufacturing analytics, quality prediction, equipment anomaly detection, downtime risk scoring, and OEE-style operational KPI reporting.

## Components
- `src/generate_synthetic_data.py`: creates synthetic raw manufacturing datasets and the processed ML training dataset
- `src/load_to_postgres.py`: loads raw, processed, and prediction outputs into PostgreSQL with safe reruns and indexes
- `dbt_mfg/`: transforms operational tables into staging, intermediate, and mart models
- `src/train_defect_model.py`: trains and evaluates defect prediction models
- `src/detect_anomalies.py`: scores anomalous machine behavior using Isolation Forest and rule-based checks
- `src/downtime_risk_scoring.py`: converts sensor, anomaly, maintenance, and downtime signals into risk bands and maintenance recommendations
- `api/`: exposes CSV-backed or artifact-backed FastAPI endpoints for KPIs, machine health, anomalies, and batch defect prediction
- `metabase/`: stores dashboard SQL and setup instructions

## Data Flow
1. Synthetic raw manufacturing data is generated into `data/raw/`
2. Processed ML features are generated into `data/processed/`
3. Raw and processed tables can be loaded to PostgreSQL
4. dbt builds analytics-ready staging, intermediate, and mart models
5. ML scripts save predictions and reports under `data/predictions/` and `reports/`
6. FastAPI and Metabase consume those outputs for human-in-the-loop decision support

## Design Principles
- Keep claims honest: this is synthetic-data workflow validation, not plant deployment validation
- Prefer clean script boundaries over notebook-only logic
- Keep tests and CI lightweight enough for GitHub use
- Focus on manufacturing analytics and maintainable repo structure

# Demo

## Windows PowerShell Quick Start
From the project root:

### Local Demo Pipeline
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\scripts\run_demo.ps1
```

### Manual Pipeline Fallback
```powershell
python -m src.generate_synthetic_data
python -m src.data_quality_checks
python -m src.train_defect_model
python -m src.detect_anomalies
python -m src.downtime_risk_scoring
python -m src.smoke_test
pytest tests -q
```

### PostgreSQL And dbt Verification
```powershell
copy .env.example .env
docker compose up -d postgres
$env:PYTHONPATH = "$PWD\src;$PWD"
python -m src.load_to_postgres
Push-Location .\dbt_mfg
dbt debug --profiles-dir .
dbt run --profiles-dir . --no-partial-parse
dbt test --profiles-dir .
Pop-Location
```

### Run FastAPI Locally
```powershell
$env:PYTHONPATH = "$PWD\src;$PWD"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

FastAPI docs will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Metabase Setup
```powershell
docker compose up -d metabase
```

Then open [http://127.0.0.1:3000](http://127.0.0.1:3000) and connect PostgreSQL with:
- host: `postgres`
- port: `5432`
- database: `manufacturing`

Use `metabase/dashboard_queries.sql` to build cards for the local dashboard.

### Capture Screenshots
```powershell
python -m playwright install chromium
.\scripts\capture_screenshots.ps1
```

## Notes
- The scripts set `PYTHONPATH` so `python -m src...` works from the project root in PowerShell.
- `run_demo.ps1` runs the local non-Docker pipeline and test flow.
- `run_full_stack.ps1` starts Docker services, loads PostgreSQL tables, runs dbt, and prints the FastAPI and Metabase URLs.
- `capture_screenshots.ps1` creates dashboard-style screenshots from pipeline outputs and captures FastAPI docs when the API is already running.
- Keep local runtime and secret files out of version control, including `.env`, `.venv/`, `dbt_mfg/profiles.yml`, `dbt_mfg/logs/`, `dbt_mfg/target/`, `dbt_mfg/.user.yml`, and `.pytest_cache/`.

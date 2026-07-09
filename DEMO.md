# Demo

## Windows PowerShell Quick Start
From the project root:

### Local Demo Pipeline
```powershell
python -m pip install -r requirements.txt
.\scripts\run_demo.ps1
```

### Smoke Test And Pytest Verification
```powershell
python -m src.smoke_test
python -m pytest tests -q
```

### PostgreSQL And dbt Verification
```powershell
docker compose up -d postgres
python -m src.load_to_postgres
Push-Location .\dbt_mfg
dbt debug --profiles-dir .
dbt run --profiles-dir . --no-partial-parse
dbt test --profiles-dir .
Pop-Location
```

### Run FastAPI Locally
```powershell
.\scripts\run_api.ps1
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
- Do not commit local runtime or secret files such as `.env`, `.venv/`, `dbt_mfg/profiles.yml`, `dbt_mfg/logs/`, `dbt_mfg/target/`, `dbt_mfg/.user.yml`, or `.pytest_cache/`.

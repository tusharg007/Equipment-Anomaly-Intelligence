# Demo

## Windows PowerShell Quick Start
From the project root:

### Local Non-Docker Demo
```powershell
.\scripts\run_demo.ps1
```

### Verify Outputs
```powershell
.\scripts\verify_outputs.ps1
```

### Run API Only
```powershell
.\scripts\run_api.ps1
```

### Run Full Stack
```powershell
.\scripts\run_full_stack.ps1
```

## Notes
- The scripts set `PYTHONPATH` so `python -m src...` works in PowerShell.
- `run_demo.ps1` skips `src.data_quality_checks`, `src.model_monitoring`, and `src.smoke_test` only if those modules are missing.
- `run_full_stack.ps1` starts Docker services, loads PostgreSQL tables, runs dbt, and prints the FastAPI and Metabase URLs.

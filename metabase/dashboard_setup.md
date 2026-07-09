# Metabase Dashboard Setup

## Start Services
1. Copy `.env.example` to `.env` if you want to customize PostgreSQL or API settings.
2. Run:
   ```bash
   docker compose up -d
   ```
3. Open Metabase at `http://localhost:3000`.

## Connect Metabase to PostgreSQL
Use these connection settings:
- Host: `postgres` when running inside Docker, or `localhost` from your machine
- Port: `5432`
- Database: `manufacturing`
- Username: `manufacturing`
- Password: `manufacturing`

## Recommended SQL Cards
Use the queries in `dashboard_queries.sql` for:
- manufacturing overview KPIs
- defect rate by line
- defect rate by machine
- defect trend over time
- downtime by machine
- OEE-style KPI by line
- anomaly trend by day
- cycle time drift by machine
- high-risk machines
- maintenance priority list
- top defect drivers

## Suggested Dashboard Layout
1. Top row: overview KPIs, total downtime, overall defect rate
2. Second row: defect rate by line, OEE-style KPI by line, anomaly trend by day
3. Third row: high-risk machines, maintenance priority list, downtime by machine
4. Bottom row: defect trend over time, cycle time drift by machine, top defect drivers

## Data Refresh Note
Re-run:
```bash
python src/load_to_postgres.py
```
after generating predictions so Metabase reflects the latest prototype outputs.

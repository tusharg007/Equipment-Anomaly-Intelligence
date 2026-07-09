from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from config import settings
from utils import ensure_directories


TABLE_FILES = {
    "machines": settings.raw_data_dir / "machines.csv",
    "production_batches": settings.raw_data_dir / "production_batches.csv",
    "sensor_readings": settings.raw_data_dir / "sensor_readings.csv",
    "quality_checks": settings.raw_data_dir / "quality_checks.csv",
    "downtime_events": settings.raw_data_dir / "downtime_events.csv",
    "maintenance_logs": settings.raw_data_dir / "maintenance_logs.csv",
    "ml_training_dataset": settings.processed_data_dir / "ml_training_dataset.csv",
    "model_features": settings.processed_data_dir / "model_features.csv",
}

OPTIONAL_TABLE_FILES = {
    "defect_predictions": settings.predictions_dir / "defect_predictions.csv",
    "feature_importance": settings.predictions_dir / "feature_importance.csv",
    "anomaly_scores": settings.predictions_dir / "anomaly_scores.csv",
    "downtime_risk_scores": settings.predictions_dir / "downtime_risk_scores.csv",
    "maintenance_priority": settings.predictions_dir / "maintenance_priority.csv",
}

INDEX_STATEMENTS = {
    "sensor_readings": [
        "create index if not exists idx_sensor_machine_ts on public.sensor_readings (machine_id, timestamp)",
        "create index if not exists idx_sensor_line_ts on public.sensor_readings (line_id, timestamp)",
    ],
    "quality_checks": [
        "create index if not exists idx_quality_machine_ts on public.quality_checks (machine_id, timestamp)",
        "create index if not exists idx_quality_batch on public.quality_checks (batch_id)",
    ],
    "downtime_events": [
        "create index if not exists idx_downtime_machine_ts on public.downtime_events (machine_id, timestamp)",
    ],
    "maintenance_logs": [
        "create index if not exists idx_maintenance_machine_ts on public.maintenance_logs (machine_id, timestamp)",
    ],
    "ml_training_dataset": [
        "create index if not exists idx_training_machine_ts on public.ml_training_dataset (machine_id, timestamp)",
    ],
}


def infer_dates(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.columns:
        if column == "timestamp" or column.endswith("_at"):
            df[column] = pd.to_datetime(df[column])
    return df


def load_file(engine, table_name: str, file_path: Path) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"Missing required file: {file_path}")
    df = infer_dates(pd.read_csv(file_path))
    print(f"Loading {table_name} from {file_path.name}...")
    df.to_sql(
        table_name,
        engine,
        schema="public",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )
    with engine.begin() as connection:
        for statement in INDEX_STATEMENTS.get(table_name, []):
            connection.execute(text(statement))
        row_count = connection.execute(text(f"select count(*) from public.{table_name}")).scalar_one()
    print(f"Loaded {table_name}: csv_rows={len(df)}, db_rows={row_count}")


def main() -> None:
    ensure_directories()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            connection.execute(text("select 1"))
    except Exception as exc:
        raise ConnectionError(
            "Unable to connect to PostgreSQL. Start docker compose and verify the values in .env or your POSTGRES_* environment variables."
        ) from exc

    for table_name, file_path in TABLE_FILES.items():
        load_file(engine, table_name, file_path)

    for table_name, file_path in OPTIONAL_TABLE_FILES.items():
        if file_path.exists():
            load_file(engine, table_name, file_path)

    print("PostgreSQL load complete.")


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from utils import DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR, ensure_directories, get_engine


TABLE_FILES = {
    "machines": RAW_DATA_DIR / "machines.csv",
    "production_batches": RAW_DATA_DIR / "production_batches.csv",
    "sensor_readings": RAW_DATA_DIR / "sensor_readings.csv",
    "quality_checks": RAW_DATA_DIR / "quality_checks.csv",
    "downtime_events": RAW_DATA_DIR / "downtime_events.csv",
    "maintenance_logs": RAW_DATA_DIR / "maintenance_logs.csv",
    "model_features": PROCESSED_DATA_DIR / "model_features.csv",
}

OPTIONAL_TABLE_FILES = {
    "defect_predictions": DATA_DIR / "predictions" / "defect_predictions.csv",
    "feature_importance": DATA_DIR / "predictions" / "feature_importance.csv",
    "anomaly_scores": DATA_DIR / "predictions" / "anomaly_scores.csv",
    "downtime_risk_scores": DATA_DIR / "predictions" / "downtime_risk_scores.csv",
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
    df.to_sql(
        table_name,
        engine,
        schema="public",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )
    print(f"Loaded {table_name}: {len(df)} rows")


def main() -> None:
    ensure_directories()
    engine = get_engine()
    try:
        with engine.begin() as connection:
            connection.execute(text("select 1"))
    except Exception as exc:
        raise ConnectionError(
            "Unable to connect to PostgreSQL. Start docker compose and verify POSTGRES_* environment variables."
        ) from exc
    for table_name, file_path in TABLE_FILES.items():
        load_file(engine, table_name, file_path)
    for table_name, file_path in OPTIONAL_TABLE_FILES.items():
        if file_path.exists():
            load_file(engine, table_name, file_path)
    print(f"Loaded datasets into PostgreSQL from {DATA_DIR}")


if __name__ == "__main__":
    main()

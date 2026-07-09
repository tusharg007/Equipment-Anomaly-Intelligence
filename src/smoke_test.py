from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from utils import MODELS_DIR, PREDICTIONS_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_FILES = {
    "machines.csv": {"machine_id", "line_id", "machine_age_years", "maintenance_status"},
    "production_batches.csv": {"batch_id", "line_id", "timestamp", "shift", "product_type"},
    "sensor_readings.csv": {"machine_id", "line_id", "timestamp", "temperature", "vibration", "pressure", "cycle_time"},
    "quality_checks.csv": {"quality_check_id", "batch_id", "machine_id", "defect_flag", "defect_type"},
    "downtime_events.csv": {"downtime_event_id", "machine_id", "timestamp", "downtime_minutes"},
    "maintenance_logs.csv": {"maintenance_id", "machine_id", "timestamp", "maintenance_type"},
}
PREDICTION_FILES = {
    PREDICTIONS_DIR / "defect_predictions.csv": {"machine_id", "predicted_defect_probability", "predicted_defect_flag"},
    PREDICTIONS_DIR / "feature_importance.csv": {"feature", "importance"},
    PREDICTIONS_DIR / "anomaly_scores.csv": {"machine_id", "anomaly_score", "anomaly_count"},
    PREDICTIONS_DIR / "downtime_risk_scores.csv": {"machine_id", "downtime_risk_score", "risk_band"},
}


def run_script(script_name: str) -> None:
    subprocess.run([sys.executable, str(PROJECT_ROOT / "src" / script_name)], check=True, cwd=PROJECT_ROOT)


def assert_columns(file_path: Path, required_columns: set[str]) -> None:
    if not file_path.exists():
        raise AssertionError(f"Missing expected file: {file_path}")
    df = pd.read_csv(file_path)
    missing = required_columns - set(df.columns)
    if missing:
        raise AssertionError(f"Missing required columns in {file_path.name}: {sorted(missing)}")
    if df.empty:
        raise AssertionError(f"Expected rows in {file_path.name}, but the file is empty.")


def cleanup_outputs() -> None:
    for file_path in [PROCESSED_DATA_DIR / "model_features.csv", *PREDICTION_FILES.keys(), MODELS_DIR / "best_defect_model.joblib"]:
        if file_path.exists():
            file_path.unlink()


def main() -> None:
    cleanup_outputs()

    run_script("generate_synthetic_data.py")
    for file_name, required_columns in RAW_FILES.items():
        assert_columns(RAW_DATA_DIR / file_name, required_columns)
    assert_columns(PROCESSED_DATA_DIR / "model_features.csv", {"machine_id", "line_id", "timestamp", "defect_flag", "anomaly_signal"})

    run_script("train_defect_model.py")
    run_script("detect_anomalies.py")
    run_script("downtime_risk_scoring.py")

    for file_path, required_columns in PREDICTION_FILES.items():
        assert_columns(file_path, required_columns)

    print("Smoke test passed.")


if __name__ == "__main__":
    main()

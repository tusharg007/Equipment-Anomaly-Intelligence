from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from src.config import settings


PROJECT_ROOT = settings.project_root
RAW_FILES = {
    "machines.csv": {"machine_id", "line_id", "machine_type", "machine_age_years", "baseline_health_score"},
    "production_batches.csv": {"batch_id", "line_id", "timestamp", "shift", "product_type"},
    "sensor_readings.csv": {"machine_id", "timestamp", "temperature", "vibration", "pressure", "cycle_time", "energy_consumption"},
    "quality_checks.csv": {"quality_check_id", "batch_id", "machine_id", "defect_flag", "defect_type"},
    "downtime_events.csv": {"downtime_event_id", "machine_id", "timestamp", "downtime_minutes"},
    "maintenance_logs.csv": {"maintenance_id", "machine_id", "timestamp", "maintenance_type"},
}
PREDICTION_FILES = {
    settings.predictions_dir / "defect_predictions.csv": {"machine_id", "predicted_defect_probability", "predicted_defect_flag"},
    settings.predictions_dir / "feature_importance.csv": {"feature", "importance"},
    settings.predictions_dir / "anomaly_scores.csv": {"machine_id", "timestamp", "anomaly_score", "anomaly_flag", "anomaly_reason"},
    settings.predictions_dir / "downtime_risk_scores.csv": {"machine_id", "downtime_risk_score", "risk_band", "top_risk_driver"},
    settings.predictions_dir / "maintenance_priority.csv": {"machine_id", "maintenance_priority_recommendation"},
}


def run_script(script_name: str) -> None:
    subprocess.run([sys.executable, "-m", f"src.{Path(script_name).stem}"], check=True, cwd=PROJECT_ROOT)


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
    for file_path in [
        settings.processed_data_dir / "ml_training_dataset.csv",
        settings.processed_data_dir / "model_features.csv",
        settings.reports_dir / "metrics.json",
        settings.reports_dir / "classification_report.json",
        settings.reports_dir / "confusion_matrix.csv",
        *PREDICTION_FILES.keys(),
        settings.defect_model_dir / "best_defect_model.joblib",
        settings.anomaly_model_dir / "isolation_forest.joblib",
    ]:
        if file_path.exists():
            file_path.unlink()


def main() -> None:
    cleanup_outputs()
    run_script("generate_synthetic_data.py")
    run_script("data_quality_checks.py")
    for file_name, required_columns in RAW_FILES.items():
        assert_columns(settings.raw_data_dir / file_name, required_columns)
    assert_columns(settings.processed_data_dir / "ml_training_dataset.csv", {"machine_id", "timestamp", "defect_flag", "quality_risk_index"})

    run_script("train_defect_model.py")
    run_script("detect_anomalies.py")
    run_script("downtime_risk_scoring.py")
    run_script("batch_inference.py")

    for file_path, required_columns in PREDICTION_FILES.items():
        assert_columns(file_path, required_columns)
    assert_columns(settings.reports_dir / "confusion_matrix.csv", {"predicted_0", "predicted_1"})
    print("Smoke test passed.")


if __name__ == "__main__":
    main()



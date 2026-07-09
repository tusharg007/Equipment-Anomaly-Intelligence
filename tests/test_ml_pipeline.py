from __future__ import annotations

import pandas as pd

from src.config import settings
from src.detect_anomalies import main as run_anomalies
from src.generate_synthetic_data import main as generate_data
from src.train_defect_model import main as train_model


def test_ml_pipeline_outputs():
    generate_data()
    train_model()
    run_anomalies()

    metrics_file = settings.reports_dir / "metrics.json"
    predictions_file = settings.predictions_dir / "defect_predictions.csv"
    anomaly_file = settings.predictions_dir / "anomaly_scores.csv"

    assert metrics_file.exists()
    assert predictions_file.exists()
    assert anomaly_file.exists()
    assert {"predicted_defect_probability", "predicted_defect_flag"}.issubset(pd.read_csv(predictions_file).columns)
    assert {"anomaly_score", "anomaly_flag", "anomaly_reason"}.issubset(pd.read_csv(anomaly_file).columns)


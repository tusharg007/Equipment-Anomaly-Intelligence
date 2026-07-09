from __future__ import annotations

import pandas as pd

from config import settings
from generate_synthetic_data import main as generate_data


def test_data_generation_outputs():
    generate_data()
    required_files = {
        settings.raw_data_dir / "machines.csv": {"machine_id", "line_id", "machine_type", "baseline_health_score"},
        settings.raw_data_dir / "sensor_readings.csv": {"machine_id", "timestamp", "temperature", "vibration", "energy_consumption"},
        settings.processed_data_dir / "ml_training_dataset.csv": {"machine_id", "timestamp", "defect_flag", "quality_risk_index"},
    }
    for file_path, required_columns in required_files.items():
        assert file_path.exists()
        df = pd.read_csv(file_path)
        assert required_columns.issubset(df.columns)
        assert not df.empty

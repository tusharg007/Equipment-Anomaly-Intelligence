from __future__ import annotations

import pandas as pd

from config import settings
from utils import ensure_directories, save_json


REQUIRED_FILES = {
    settings.raw_data_dir / "machines.csv": ["machine_id", "line_id", "machine_type", "machine_age_years"],
    settings.raw_data_dir / "sensor_readings.csv": ["machine_id", "timestamp", "temperature", "vibration", "pressure", "cycle_time"],
    settings.processed_data_dir / "ml_training_dataset.csv": ["machine_id", "timestamp", "defect_flag", "quality_risk_index"],
}


def main() -> None:
    ensure_directories()
    results = {"checks": []}
    for file_path, columns in REQUIRED_FILES.items():
        if not file_path.exists():
            results["checks"].append({"file": file_path.name, "status": "missing"})
            continue
        df = pd.read_csv(file_path)
        missing_columns = sorted(set(columns) - set(df.columns))
        results["checks"].append(
            {
                "file": file_path.name,
                "status": "pass" if not missing_columns and not df.empty else "fail",
                "rows": int(len(df)),
                "missing_columns": missing_columns,
            }
        )
    save_json(results, settings.reports_dir / "data_quality_report.json")
    print("Saved data quality report.")


if __name__ == "__main__":
    main()

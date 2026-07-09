from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from utils import PREDICTIONS_DIR, PROCESSED_DATA_DIR, ensure_directories


FEATURE_FILE = PROCESSED_DATA_DIR / "model_features.csv"
ANOMALY_FEATURES = [
    "avg_temperature",
    "avg_vibration",
    "avg_pressure",
    "avg_cycle_time",
    "pressure_instability",
    "anomaly_signal",
    "machine_age_years",
    "previous_downtime_minutes",
]


def main() -> None:
    ensure_directories()
    data = pd.read_csv(FEATURE_FILE)

    isolation_forest = IsolationForest(
        n_estimators=250, contamination=0.06, random_state=42
    )
    isolation_forest.fit(data[ANOMALY_FEATURES])
    data["iforest_score"] = -isolation_forest.score_samples(data[ANOMALY_FEATURES])
    data["iforest_anomaly_flag"] = (isolation_forest.predict(data[ANOMALY_FEATURES]) == -1).astype(int)

    z_scores = (
        data[ANOMALY_FEATURES]
        .apply(lambda column: (column - column.mean()) / column.std(ddof=0))
        .abs()
    )
    data["zscore_anomaly_flag"] = (z_scores.max(axis=1) >= 3.0).astype(int)
    data["combined_anomaly_flag"] = ((data["iforest_anomaly_flag"] + data["zscore_anomaly_flag"]) > 0).astype(int)
    data["anomaly_score"] = (
        60 * data["iforest_score"].rank(pct=True)
        + 40 * z_scores.max(axis=1).clip(upper=5).div(5)
    ).round(2)

    machine_scores = (
        data.groupby(["machine_id", "line_id"], as_index=False)
        .agg(
            anomaly_score=("anomaly_score", "mean"),
            anomaly_count=("combined_anomaly_flag", "sum"),
            latest_temperature=("avg_temperature", "last"),
            latest_vibration=("avg_vibration", "last"),
            latest_cycle_time=("avg_cycle_time", "last"),
        )
        .sort_values(["anomaly_score", "anomaly_count"], ascending=False)
    )
    machine_scores.to_csv(PREDICTIONS_DIR / "anomaly_scores.csv", index=False)
    print(machine_scores.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

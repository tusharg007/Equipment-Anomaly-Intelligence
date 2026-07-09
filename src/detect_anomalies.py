from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

from config import settings
from utils import ensure_directories, save_joblib


FEATURE_FILE = settings.processed_data_dir / "ml_training_dataset.csv"
ANOMALY_FEATURES = [
    "avg_temperature",
    "avg_vibration",
    "avg_pressure",
    "avg_cycle_time",
    "avg_energy_consumption",
    "pressure_instability",
    "anomaly_signal",
    "previous_downtime_minutes",
]
RULE_FEATURES = ["avg_temperature", "avg_vibration", "avg_pressure", "avg_cycle_time", "avg_energy_consumption"]


def build_rule_reason(row: pd.Series) -> str:
    reasons = []
    if row["avg_temperature_zscore"] >= 3:
        reasons.append("temperature_zscore")
    if row["avg_vibration_zscore"] >= 3:
        reasons.append("vibration_zscore")
    if row["avg_pressure_zscore"] >= 3:
        reasons.append("pressure_zscore")
    if row["avg_cycle_time_zscore"] >= 3:
        reasons.append("cycle_time_zscore")
    if row["avg_energy_consumption_zscore"] >= 3:
        reasons.append("energy_zscore")
    if row["iforest_anomaly_flag"] == 1:
        reasons.append("iforest_outlier")
    return ",".join(reasons) if reasons else "none"


def main() -> None:
    ensure_directories()
    data = pd.read_csv(FEATURE_FILE)

    isolation_forest = IsolationForest(n_estimators=250, contamination=0.06, random_state=42)
    isolation_forest.fit(data[ANOMALY_FEATURES])
    data["iforest_score"] = -isolation_forest.score_samples(data[ANOMALY_FEATURES])
    data["iforest_anomaly_flag"] = (isolation_forest.predict(data[ANOMALY_FEATURES]) == -1).astype(int)

    for feature in RULE_FEATURES:
        zscore_column = f"{feature}_zscore"
        data[zscore_column] = ((data[feature] - data[feature].mean()) / data[feature].std(ddof=0)).abs()

    data["rule_anomaly_flag"] = (
        data[[f"{feature}_zscore" for feature in RULE_FEATURES]].max(axis=1) >= 3.0
    ).astype(int)
    data["anomaly_flag"] = ((data["iforest_anomaly_flag"] + data["rule_anomaly_flag"]) > 0).astype(int)
    data["anomaly_score"] = (
        60 * data["iforest_score"].rank(pct=True)
        + 40 * data[[f"{feature}_zscore" for feature in RULE_FEATURES]].max(axis=1).clip(upper=5) / 5
    ).round(2)
    data["anomaly_reason"] = data.apply(build_rule_reason, axis=1)

    output_columns = [
        "machine_id",
        "line_id",
        "timestamp",
        "shift",
        "anomaly_score",
        "anomaly_flag",
        "anomaly_reason",
        "avg_temperature",
        "avg_vibration",
        "avg_pressure",
        "avg_cycle_time",
        "avg_energy_consumption",
    ]
    anomaly_scores = data[output_columns].sort_values(["anomaly_flag", "anomaly_score"], ascending=[False, False])
    anomaly_scores.to_csv(settings.predictions_dir / "anomaly_scores.csv", index=False)
    save_joblib(isolation_forest, settings.anomaly_model_dir / "isolation_forest.joblib")
    print(anomaly_scores.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import settings
from src.utils import ensure_directories


FEATURE_FILE = settings.processed_data_dir / "ml_training_dataset.csv"
ANOMALY_FILE = settings.predictions_dir / "anomaly_scores.csv"


def normalize(series: pd.Series) -> pd.Series:
    span = series.max() - series.min()
    if span == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.min()) / span


def main() -> None:
    ensure_directories()
    features = pd.read_csv(FEATURE_FILE)
    anomalies = pd.read_csv(ANOMALY_FILE) if ANOMALY_FILE.exists() else pd.DataFrame(columns=["machine_id", "timestamp", "anomaly_flag"])

    if not anomalies.empty:
        anomalies["timestamp"] = pd.to_datetime(anomalies["timestamp"])
        anomalies["date"] = anomalies["timestamp"].dt.date
        anomaly_daily = anomalies.groupby(["machine_id", "date"], as_index=False).agg(
            anomaly_count_24h=("anomaly_flag", "sum")
        )
    else:
        anomaly_daily = pd.DataFrame(columns=["machine_id", "date", "anomaly_count_24h"])

    features["timestamp"] = pd.to_datetime(features["timestamp"])
    features["date"] = features["timestamp"].dt.date
    grouped = (
        features.groupby(["machine_id", "line_id"], as_index=False)
        .agg(
            avg_temperature=("avg_temperature", "mean"),
            avg_vibration=("avg_vibration", "mean"),
            avg_cycle_time=("avg_cycle_time", "mean"),
            cycle_time_drift=("cycle_time_drift", lambda values: values.abs().mean()),
            previous_downtime_minutes=("previous_downtime_minutes", "sum"),
            machine_age_years=("machine_age_years", "max"),
            maintenance_recency_score=("maintenance_recency_score", "mean"),
            quality_risk_index=("quality_risk_index", "mean"),
            days_since_maintenance=("days_since_maintenance", "min"),
        )
    )
    grouped = grouped.merge(
        anomaly_daily.groupby("machine_id", as_index=False).agg(anomaly_count_24h=("anomaly_count_24h", "sum")),
        on="machine_id",
        how="left",
    )
    grouped["anomaly_count_24h"] = grouped["anomaly_count_24h"].fillna(0)

    grouped["vibration_risk"] = normalize(grouped["avg_vibration"]) * 100
    grouped["temperature_risk"] = normalize(grouped["avg_temperature"]) * 100
    grouped["cycle_time_risk"] = normalize(grouped["cycle_time_drift"]) * 100
    grouped["previous_downtime_risk"] = normalize(grouped["previous_downtime_minutes"]) * 100
    grouped["maintenance_recency_factor"] = (1 - normalize(grouped["maintenance_recency_score"])) * 100

    grouped["downtime_risk_score"] = (
        0.24 * grouped["vibration_risk"]
        + 0.18 * grouped["temperature_risk"]
        + 0.17 * grouped["cycle_time_risk"]
        + 0.16 * grouped["previous_downtime_risk"]
        + 0.12 * normalize(grouped["anomaly_count_24h"]) * 100
        + 0.08 * normalize(grouped["machine_age_years"]) * 100
        + 0.05 * grouped["maintenance_recency_factor"]
    ).clip(lower=0, upper=100)
    grouped["risk_band"] = pd.cut(
        grouped["downtime_risk_score"],
        bins=[-1, 30, 55, 75, 100],
        labels=["Low", "Medium", "High", "Critical"],
    )

    driver_columns = {
        "vibration_risk": "Vibration",
        "temperature_risk": "Temperature",
        "cycle_time_risk": "Cycle time drift",
        "previous_downtime_risk": "Previous downtime",
        "maintenance_recency_factor": "Maintenance recency",
    }
    grouped["top_risk_driver"] = grouped[list(driver_columns.keys())].idxmax(axis=1).map(driver_columns)
    grouped["maintenance_priority_recommendation"] = np.select(
        [
            grouped["risk_band"] == "Critical",
            grouped["risk_band"] == "High",
            grouped["risk_band"] == "Medium",
        ],
        [
            "Urgent maintenance review",
            "Preventive maintenance",
            "Schedule inspection",
        ],
        default="Monitor",
    )
    grouped = grouped.sort_values("downtime_risk_score", ascending=False)
    grouped["downtime_risk_score"] = grouped["downtime_risk_score"].round(2)

    output_columns = [
        "machine_id",
        "line_id",
        "downtime_risk_score",
        "risk_band",
        "top_risk_driver",
        "anomaly_count_24h",
        "vibration_risk",
        "temperature_risk",
        "cycle_time_risk",
        "previous_downtime_risk",
        "maintenance_recency_factor",
        "maintenance_priority_recommendation",
    ]
    grouped[output_columns].to_csv(settings.predictions_dir / "downtime_risk_scores.csv", index=False)
    grouped[["machine_id", "line_id", "risk_band", "maintenance_priority_recommendation", "top_risk_driver"]].to_csv(
        settings.predictions_dir / "maintenance_priority.csv",
        index=False,
    )
    print(grouped[output_columns].head(10).to_string(index=False))


if __name__ == "__main__":
    main()


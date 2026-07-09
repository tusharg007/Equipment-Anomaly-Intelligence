from __future__ import annotations

import numpy as np
import pandas as pd

from utils import PREDICTIONS_DIR, PROCESSED_DATA_DIR, ensure_directories


FEATURE_FILE = PROCESSED_DATA_DIR / "model_features.csv"


def normalize(series: pd.Series) -> pd.Series:
    span = series.max() - series.min()
    if span == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.min()) / span


def main() -> None:
    ensure_directories()
    features = pd.read_csv(FEATURE_FILE)

    grouped = (
        features.groupby(["machine_id", "line_id"], as_index=False)
        .agg(
            anomaly_count=("anomaly_signal", lambda values: int((values > 2.5).sum())),
            avg_temperature=("avg_temperature", "mean"),
            avg_vibration=("avg_vibration", "mean"),
            cycle_time_drift=("cycle_time_drift", lambda values: values.abs().mean()),
            previous_downtime_minutes=("previous_downtime_minutes", "sum"),
            machine_age_years=("machine_age_years", "max"),
            maintenance_recency_score=("maintenance_recency_score", "mean"),
            quality_risk_index=("quality_risk_index", "mean"),
        )
    )

    grouped["risk_score"] = (
        18 * normalize(grouped["anomaly_count"])
        + 17 * normalize(grouped["avg_temperature"])
        + 20 * normalize(grouped["avg_vibration"])
        + 14 * normalize(grouped["cycle_time_drift"])
        + 12 * normalize(grouped["previous_downtime_minutes"])
        + 11 * normalize(grouped["machine_age_years"])
        + 8 * normalize(grouped["quality_risk_index"])
        - 10 * normalize(grouped["maintenance_recency_score"])
    ).clip(lower=0, upper=100)

    grouped["risk_band"] = pd.cut(
        grouped["risk_score"],
        bins=[-1, 35, 65, 100],
        labels=["Low", "Medium", "High"],
    )
    grouped["maintenance_priority_recommendation"] = np.select(
        [
            grouped["risk_band"] == "High",
            grouped["risk_band"] == "Medium",
        ],
        [
            "Inspect within 24 hours and review recent anomaly pattern.",
            "Schedule maintenance in next production window.",
        ],
        default="Continue routine inspection cadence.",
    )

    grouped = grouped.sort_values("risk_score", ascending=False)
    grouped.rename(columns={"risk_score": "downtime_risk_score"}, inplace=True)
    grouped["downtime_risk_score"] = grouped["downtime_risk_score"].round(2)
    grouped.to_csv(PREDICTIONS_DIR / "downtime_risk_scores.csv", index=False)
    print(grouped.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

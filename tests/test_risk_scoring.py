from __future__ import annotations

import pandas as pd

from src.config import settings
from src.detect_anomalies import main as run_anomalies
from src.downtime_risk_scoring import main as run_risk
from src.generate_synthetic_data import main as generate_data


def test_risk_scores_are_bounded():
    generate_data()
    run_anomalies()
    run_risk()
    risk_scores = pd.read_csv(settings.predictions_dir / "downtime_risk_scores.csv")
    assert ((risk_scores["downtime_risk_score"] >= 0) & (risk_scores["downtime_risk_score"] <= 100)).all()
    assert {"Low", "Medium", "High", "Critical"}.issuperset(set(risk_scores["risk_band"].dropna().unique()))


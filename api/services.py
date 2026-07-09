from __future__ import annotations

from pathlib import Path

import pandas as pd
from joblib import load

from config import settings


def _load_csv(file_path: Path) -> pd.DataFrame | None:
    if not file_path.exists():
        return None
    return pd.read_csv(file_path)


def health_payload() -> dict:
    generated = (settings.processed_data_dir / "ml_training_dataset.csv").exists()
    trained = (settings.defect_model_dir / "best_defect_model.joblib").exists()
    return {
        "status": "ok",
        "message": "Production-oriented prototype API is available.",
        "data_ready": generated,
        "model_ready": trained,
    }


def get_kpis_overview() -> dict:
    batches = _load_csv(settings.raw_data_dir / "production_batches.csv")
    quality = _load_csv(settings.raw_data_dir / "quality_checks.csv")
    downtime = _load_csv(settings.raw_data_dir / "downtime_events.csv")
    if batches is None or quality is None:
        return {"message": "Generate data first to compute overview KPIs."}
    return {
        "total_batches": int(len(batches)),
        "avg_defect_rate": float(quality["defect_flag"].mean()),
        "total_defect_count": int(quality["defect_count"].sum()),
        "total_downtime_minutes": int(downtime["downtime_minutes"].sum()) if downtime is not None and not downtime.empty else 0,
    }


def get_machine_health() -> dict:
    risk_scores = _load_csv(settings.predictions_dir / "downtime_risk_scores.csv")
    if risk_scores is None:
        return {"message": "Run downtime_risk_scoring.py to populate machine health outputs."}
    return {"records": risk_scores.sort_values("downtime_risk_score", ascending=False).head(20).to_dict(orient="records")}


def get_high_risk_machines() -> dict:
    risk_scores = _load_csv(settings.predictions_dir / "downtime_risk_scores.csv")
    if risk_scores is None:
        return {"message": "No risk score output found yet."}
    return {
        "records": risk_scores[risk_scores["risk_band"].isin(["High", "Critical"])].to_dict(orient="records")
    }


def get_defect_trends() -> dict:
    quality = _load_csv(settings.raw_data_dir / "quality_checks.csv")
    if quality is None:
        return {"message": "No quality checks found yet."}
    quality["timestamp"] = pd.to_datetime(quality["timestamp"])
    trends = (
        quality.groupby(quality["timestamp"].dt.date, as_index=False)
        .agg(defect_rate=("defect_flag", "mean"), defect_count=("defect_count", "sum"))
        .rename(columns={"timestamp": "date"})
    )
    return {"records": trends.to_dict(orient="records")}


def get_recent_anomalies() -> dict:
    anomalies = _load_csv(settings.predictions_dir / "anomaly_scores.csv")
    if anomalies is None:
        return {"message": "Run detect_anomalies.py to populate anomaly outputs."}
    anomalies["timestamp"] = pd.to_datetime(anomalies["timestamp"])
    recent = anomalies.sort_values("timestamp", ascending=False).head(25)
    return {"records": recent.to_dict(orient="records")}


def get_maintenance_priority() -> dict:
    maintenance = _load_csv(settings.predictions_dir / "maintenance_priority.csv")
    if maintenance is None:
        return {"message": "Run downtime_risk_scoring.py to populate maintenance recommendations."}
    return {"records": maintenance.to_dict(orient="records")}


def predict_defect_risk(records: list[dict]) -> dict:
    model_path = settings.defect_model_dir / "best_defect_model.joblib"
    if not model_path.exists():
        return {"message": "Defect model artifact is missing. Run train_defect_model.py first."}
    if not records:
        return {"message": "No records supplied."}
    model = load(model_path)
    frame = pd.DataFrame(records)
    probabilities = model.predict_proba(frame)[:, 1]
    frame["predicted_defect_probability"] = probabilities
    frame["predicted_defect_flag"] = (probabilities >= 0.5).astype(int)
    return {"records": frame.to_dict(orient="records")}

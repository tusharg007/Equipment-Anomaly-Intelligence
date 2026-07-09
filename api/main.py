from __future__ import annotations

from fastapi import FastAPI, HTTPException

from api.schemas import DefectRiskRequest
from api import services


app = FastAPI(title="Manufacturing Quality & Equipment Anomaly Intelligence Platform API")


@app.get("/health")
def health():
    return services.health_payload()


@app.get("/kpis/overview")
def kpis_overview():
    return services.get_kpis_overview()


@app.get("/machines/health")
def machines_health():
    return services.get_machine_health()


@app.get("/machines/high-risk")
def machines_high_risk():
    return services.get_high_risk_machines()


@app.get("/quality/defect-trends")
def defect_trends():
    return services.get_defect_trends()


@app.get("/anomalies/recent")
def recent_anomalies():
    return services.get_recent_anomalies()


@app.get("/maintenance/priority")
def maintenance_priority():
    return services.get_maintenance_priority()


@app.post("/predict/defect-risk")
def predict_defect_risk(request: DefectRiskRequest):
    response = services.predict_defect_risk([record.model_dump() for record in request.records])
    if "message" in response and response["message"].startswith("Defect model artifact is missing"):
        raise HTTPException(status_code=400, detail=response["message"])
    return response

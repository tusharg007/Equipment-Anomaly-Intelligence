from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app
from src.generate_synthetic_data import main as generate_data
from src.train_defect_model import main as train_model


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_key_endpoints_return_payloads():
    generate_data()
    train_model()
    assert client.get("/kpis/overview").status_code == 200
    assert client.get("/machines/health").status_code == 200
    assert client.get("/maintenance/priority").status_code == 200


def test_predict_defect_risk_endpoint():
    generate_data()
    train_model()
    payload = {
        "records": [
            {
                "line_id": "L1",
                "shift": "Day",
                "avg_temperature": 78.5,
                "avg_vibration": 2.9,
                "avg_pressure": 99.1,
                "avg_cycle_time": 61.2,
                "avg_energy_consumption": 162.0,
                "pressure_instability": 4.1,
                "anomaly_signal": 2.7,
                "machine_age_years": 10,
                "days_since_maintenance": 14,
                "previous_downtime_minutes": 60,
                "downtime_event_count": 1,
                "cycle_time_drift": 2.4,
                "pressure_deviation": 1.8,
                "maintenance_recency_score": 16,
                "quality_risk_index": 5.5,
                "anomaly_count_24h": 3,
                "baseline_health_score": 0.71,
            }
        ]
    }
    response = client.post("/predict/defect-risk", json=payload)
    assert response.status_code == 200
    assert "records" in response.json()


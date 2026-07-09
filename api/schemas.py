from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class DefectRiskRecord(BaseModel):
    line_id: str
    shift: str
    avg_temperature: float
    avg_vibration: float
    avg_pressure: float
    avg_cycle_time: float
    avg_energy_consumption: float
    pressure_instability: float
    anomaly_signal: float
    machine_age_years: float
    days_since_maintenance: float
    previous_downtime_minutes: float = 0
    downtime_event_count: float = 0
    cycle_time_drift: float = 0
    pressure_deviation: float = 0
    maintenance_recency_score: float = 0
    quality_risk_index: float = 0
    anomaly_count_24h: float = 0
    baseline_health_score: float = 0.8


class DefectRiskRequest(BaseModel):
    records: List[DefectRiskRecord] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    message: str

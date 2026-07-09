from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.config import settings
from src.utils import ensure_directories, safe_divide


SEED = 42
NUM_MACHINES = 30
NUM_LINES = 3
NUM_DAYS = 60
START_DATE = pd.Timestamp("2026-01-01 00:00:00")
PRODUCT_TYPES = ["SUV Frame", "Battery Module", "Steering Column"]
DEFECT_TYPES = ["Surface", "Dimensional", "Assembly", "Electrical"]
OPERATOR_TEAMS = ["Team A", "Team B", "Team C", "Team D"]
MACHINE_TYPES = ["Weld", "Paint", "Assembly", "Inspection"]


@dataclass(frozen=True)
class ShiftConfig:
    name: str
    vibration_bias: float
    temperature_bias: float
    variance_multiplier: float


SHIFT_CONFIGS = {
    "Night": ShiftConfig("Night", 0.16, 1.9, 1.20),
    "Day": ShiftConfig("Day", 0.00, 0.0, 1.00),
    "Evening": ShiftConfig("Evening", 0.08, 0.8, 1.10),
}


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-values))


def assign_shift(hour: int) -> str:
    if 0 <= hour < 8:
        return "Night"
    if 8 <= hour < 16:
        return "Day"
    return "Evening"


def build_machines(rng: np.random.Generator) -> pd.DataFrame:
    machine_rows = []
    for idx in range(1, NUM_MACHINES + 1):
        machine_age = int(rng.integers(2, 16))
        machine_type = MACHINE_TYPES[(idx - 1) % len(MACHINE_TYPES)]
        baseline_health = round(float(np.clip(0.9 - 0.03 * machine_age + rng.normal(0, 0.04), 0.35, 0.96)), 3)
        line_id = f"L{((idx - 1) % NUM_LINES) + 1}"
        machine_rows.append(
            {
                "machine_id": f"M{idx:03d}",
                "line_id": line_id,
                "machine_type": machine_type,
                "machine_age_years": machine_age,
                "installation_year": 2026 - machine_age,
                "baseline_health_score": baseline_health,
                "baseline_cycle_time_seconds": round(float(rng.normal(57, 4.5)), 2),
                "baseline_temperature": round(float(rng.normal(73, 3.8)), 2),
                "baseline_vibration": round(float(rng.normal(2.1, 0.35)), 3),
                "baseline_pressure": round(float(rng.normal(99, 4.5)), 2),
            }
        )
    return pd.DataFrame(machine_rows)


def build_maintenance_logs(machines: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    maintenance_rows = []
    for machine in machines.itertuples(index=False):
        num_events = int(rng.integers(2, 5))
        candidate_days = sorted(rng.choice(np.arange(2, NUM_DAYS - 1), size=num_events, replace=False).tolist())
        for i, offset_day in enumerate(candidate_days):
            event_ts = START_DATE + pd.Timedelta(days=int(offset_day), hours=int(rng.integers(6, 19)))
            maintenance_type = "Preventive" if i < num_events - 1 else rng.choice(["Preventive", "Corrective"], p=[0.6, 0.4])
            downtime_minutes = int(max(20, rng.normal(48 if maintenance_type == "Preventive" else 78, 14)))
            maintenance_rows.append(
                {
                    "maintenance_id": f"MT_{machine.machine_id}_{offset_day}",
                    "machine_id": machine.machine_id,
                    "line_id": machine.line_id,
                    "timestamp": event_ts,
                    "maintenance_type": maintenance_type,
                    "technician_team": rng.choice(["Mech-1", "Mech-2", "Elec-1"]),
                    "parts_replaced": rng.choice(["Bearing", "Seal", "Valve", "Sensor", "Filter"]),
                    "downtime_minutes": downtime_minutes,
                    "maintenance_status_after": "recent",
                }
            )
    maintenance_logs = pd.DataFrame(maintenance_rows).sort_values(["machine_id", "timestamp"]).reset_index(drop=True)
    return maintenance_logs


def build_sensor_readings(
    machines: pd.DataFrame,
    maintenance_logs: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    timestamps = pd.date_range(START_DATE, periods=NUM_DAYS * 24, freq="h")
    maintenance_lookup = {
        machine_id: list(group["timestamp"])
        for machine_id, group in maintenance_logs.groupby("machine_id")
    }
    records: list[dict] = []

    # The synthetic logic intentionally links older machines and prolonged time since maintenance
    # to noisier sensors, more anomalies, and slower cycle times.
    for machine in machines.itertuples(index=False):
        maintenance_events = maintenance_lookup.get(machine.machine_id, [])
        next_event_idx = 0
        last_maintenance_ts = START_DATE - pd.Timedelta(days=int(machine.machine_age_years))

        for timestamp in timestamps:
            while next_event_idx < len(maintenance_events) and maintenance_events[next_event_idx] <= timestamp:
                last_maintenance_ts = maintenance_events[next_event_idx]
                next_event_idx += 1

            shift_name = assign_shift(timestamp.hour)
            shift_cfg = SHIFT_CONFIGS[shift_name]
            age_factor = machine.machine_age_years / 15
            days_since_maintenance = max((timestamp - last_maintenance_ts).days, 0)
            maintenance_relief = np.clip((10 - days_since_maintenance) / 10, 0, 1)
            seasonal = np.sin(timestamp.hour / 24 * 2 * np.pi)
            cycle_drift = 0.015 * ((timestamp - timestamps[0]).days) + 0.06 * age_factor
            baseline_health_penalty = 1 - machine.baseline_health_score

            temperature = (
                machine.baseline_temperature
                + 1.8 * seasonal
                + 4.6 * age_factor
                + 2.2 * baseline_health_penalty
                + shift_cfg.temperature_bias
                + rng.normal(0, 1.15 * shift_cfg.variance_multiplier)
                - 1.5 * maintenance_relief
            )
            vibration = (
                machine.baseline_vibration
                + 0.52 * age_factor
                + 0.18 * cycle_drift * 10
                + 0.24 * baseline_health_penalty
                + shift_cfg.vibration_bias
                + rng.normal(0, 0.16 * shift_cfg.variance_multiplier)
                - 0.12 * maintenance_relief
            )
            pressure = (
                machine.baseline_pressure
                + 2.3 * seasonal
                - 1.9 * cycle_drift
                + rng.normal(0, 1.55 * shift_cfg.variance_multiplier)
            )
            cycle_time = (
                machine.baseline_cycle_time_seconds
                * (1 + cycle_drift / 10)
                + 4.5 * baseline_health_penalty
                + rng.normal(0, 1.7 * shift_cfg.variance_multiplier)
                - 1.0 * maintenance_relief
            )
            pressure_instability = abs(pressure - machine.baseline_pressure)
            energy_consumption = (
                110
                + 0.72 * cycle_time
                + 2.9 * vibration
                + 0.18 * temperature
                + rng.normal(0, 2.2)
            )
            anomaly_signal = (
                0.22 * max(temperature - 80, 0)
                + 1.0 * max(vibration - 2.8, 0)
                + 0.10 * pressure_instability
                + 0.09 * max(cycle_time - machine.baseline_cycle_time_seconds - 5, 0)
                + 0.42 * age_factor
                + 0.16 * max(days_since_maintenance - 12, 0) / 12
            )

            records.append(
                {
                    "machine_id": machine.machine_id,
                    "line_id": machine.line_id,
                    "timestamp": timestamp,
                    "shift": shift_name,
                    "temperature": round(float(temperature), 2),
                    "vibration": round(float(vibration), 3),
                    "pressure": round(float(pressure), 2),
                    "cycle_time": round(float(cycle_time), 2),
                    "energy_consumption": round(float(energy_consumption), 2),
                    "machine_age_years": machine.machine_age_years,
                    "machine_type": machine.machine_type,
                    "baseline_health_score": machine.baseline_health_score,
                    "days_since_maintenance": days_since_maintenance,
                    "maintenance_status": "recent" if days_since_maintenance <= 7 else "scheduled" if days_since_maintenance <= 21 else "overdue",
                    "pressure_instability": round(float(pressure_instability), 2),
                    "sensor_anomaly_signal": round(float(anomaly_signal), 3),
                }
            )

    return pd.DataFrame(records)


def build_production_batches(sensor_readings: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    sensor_batches = sensor_readings.copy()
    sensor_batches["batch_slot"] = sensor_batches["timestamp"].dt.floor("4h")
    grouped = sensor_batches.groupby(["line_id", "batch_slot", "shift"], as_index=False).agg(
        avg_temperature=("temperature", "mean"),
        avg_vibration=("vibration", "mean"),
        avg_pressure=("pressure", "mean"),
        avg_cycle_time=("cycle_time", "mean"),
        avg_energy_consumption=("energy_consumption", "mean"),
        avg_pressure_instability=("pressure_instability", "mean"),
        avg_anomaly_signal=("sensor_anomaly_signal", "mean"),
    )

    batch_rows = []
    for row in grouped.itertuples(index=False):
        batch_id = f"B{row.batch_slot.strftime('%Y%m%d%H')}_{row.line_id}"
        planned_units = int(rng.integers(175, 245))
        actual_units = int(max(planned_units - row.avg_anomaly_signal * 4 - max(row.avg_cycle_time - 58, 0), 90))
        good_units = int(max(actual_units - max(row.avg_anomaly_signal * 2 + rng.normal(5, 2), 0), 0))
        batch_rows.append(
            {
                "batch_id": batch_id,
                "line_id": row.line_id,
                "timestamp": row.batch_slot,
                "shift": row.shift,
                "product_type": PRODUCT_TYPES[(int(row.line_id[-1]) + row.batch_slot.day) % len(PRODUCT_TYPES)],
                "material_batch": f"MAT-{row.batch_slot.strftime('%m%d')}-{row.line_id}",
                "operator_team": OPERATOR_TEAMS[(row.batch_slot.hour // 4 + int(row.line_id[-1])) % len(OPERATOR_TEAMS)],
                "planned_units": planned_units,
                "actual_units": actual_units,
                "good_units": min(good_units, actual_units),
                "avg_temperature": round(float(row.avg_temperature), 2),
                "avg_vibration": round(float(row.avg_vibration), 3),
                "avg_pressure": round(float(row.avg_pressure), 2),
                "avg_cycle_time": round(float(row.avg_cycle_time), 2),
                "avg_energy_consumption": round(float(row.avg_energy_consumption), 2),
                "avg_pressure_instability": round(float(row.avg_pressure_instability), 2),
                "avg_anomaly_signal": round(float(row.avg_anomaly_signal), 3),
            }
        )
    return pd.DataFrame(batch_rows)


def build_quality_checks(
    machines: pd.DataFrame,
    production_batches: pd.DataFrame,
    sensor_readings: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    sensor_features = (
        sensor_readings.assign(batch_slot=sensor_readings["timestamp"].dt.floor("4h"))
        .groupby(["machine_id", "line_id", "batch_slot", "shift"], as_index=False)
        .agg(
            avg_temperature=("temperature", "mean"),
            avg_vibration=("vibration", "mean"),
            avg_pressure=("pressure", "mean"),
            avg_cycle_time=("cycle_time", "mean"),
            avg_energy_consumption=("energy_consumption", "mean"),
            avg_pressure_instability=("pressure_instability", "mean"),
            avg_anomaly_signal=("sensor_anomaly_signal", "mean"),
            days_since_maintenance=("days_since_maintenance", "max"),
            machine_age_years=("machine_age_years", "max"),
            baseline_health_score=("baseline_health_score", "max"),
        )
    )
    features = sensor_features.merge(
        production_batches,
        left_on=["line_id", "batch_slot", "shift"],
        right_on=["line_id", "timestamp", "shift"],
        how="left",
        suffixes=("", "_batch"),
    )

    quality_rows = []
    for row in features.itertuples(index=False):
        cycle_time_drift = row.avg_cycle_time - row.avg_cycle_time_batch
        logit = (
            -4.1
            + 0.08 * (row.avg_temperature - 76)
            + 1.18 * (row.avg_vibration - 2.2)
            + 0.06 * row.avg_pressure_instability
            + 0.05 * max(cycle_time_drift, 0)
            + 0.08 * row.machine_age_years / 5
            + 0.20 * row.avg_anomaly_signal
            + (0.22 if row.shift == "Night" else 0.0)
        )
        defect_probability = float(sigmoid(np.array([logit]))[0])
        defect_flag = int(rng.random() < defect_probability)
        if defect_flag:
            if row.avg_vibration > 2.9:
                defect_type = "Assembly"
            elif row.avg_temperature > 80:
                defect_type = "Surface"
            elif row.avg_pressure_instability > 4:
                defect_type = "Dimensional"
            else:
                defect_type = "Electrical"
        else:
            defect_type = "None"

        quality_rows.append(
            {
                "quality_check_id": f"QC_{row.machine_id}_{row.batch_slot.strftime('%Y%m%d%H')}",
                "batch_id": row.batch_id,
                "machine_id": row.machine_id,
                "line_id": row.line_id,
                "timestamp": row.batch_slot,
                "shift": row.shift,
                "temperature": round(float(row.avg_temperature), 2),
                "vibration": round(float(row.avg_vibration), 3),
                "pressure": round(float(row.avg_pressure), 2),
                "cycle_time": round(float(row.avg_cycle_time), 2),
                "energy_consumption": round(float(row.avg_energy_consumption), 2),
                "machine_age_years": row.machine_age_years,
                "maintenance_status": "recent" if row.days_since_maintenance <= 7 else "scheduled" if row.days_since_maintenance <= 21 else "overdue",
                "product_type": row.product_type,
                "material_batch": row.material_batch,
                "operator_team": row.operator_team,
                "pressure_instability": round(float(row.avg_pressure_instability), 2),
                "defect_probability": round(defect_probability, 4),
                "defect_flag": defect_flag,
                "defect_type": defect_type,
                "defect_count": int(max(0, rng.poisson(lam=max(defect_probability * 5, 0.1)))),
            }
        )
    return pd.DataFrame(quality_rows)


def build_downtime_events(
    machines: pd.DataFrame,
    maintenance_logs: pd.DataFrame,
    sensor_readings: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    maintenance_lookup = (
        maintenance_logs.assign(date=maintenance_logs["timestamp"].dt.floor("D"))
        .groupby(["machine_id", "date"], as_index=False)
        .size()
        .rename(columns={"size": "maintenance_events"})
    )
    daily_features = (
        sensor_readings.assign(date=sensor_readings["timestamp"].dt.floor("D"))
        .groupby(["machine_id", "line_id", "date"], as_index=False)
        .agg(
            max_temperature=("temperature", "max"),
            max_vibration=("vibration", "max"),
            avg_cycle_time=("cycle_time", "mean"),
            avg_pressure_instability=("pressure_instability", "mean"),
            avg_anomaly_signal=("sensor_anomaly_signal", "mean"),
            repeated_anomaly_hours=("sensor_anomaly_signal", lambda values: int((values > 2.6).sum())),
            days_since_maintenance=("days_since_maintenance", "min"),
            machine_age_years=("machine_age_years", "max"),
        )
        .merge(maintenance_lookup, on=["machine_id", "date"], how="left")
    )
    daily_features["maintenance_events"] = daily_features["maintenance_events"].fillna(0)

    event_rows = []
    for row in daily_features.itertuples(index=False):
        maintenance_relief = 0.18 if row.days_since_maintenance <= 5 or row.maintenance_events > 0 else 0.0
        risk_logit = (
            -3.6
            + 0.14 * max(row.max_temperature - 81, 0)
            + 1.05 * max(row.max_vibration - 2.9, 0)
            + 0.06 * row.avg_pressure_instability
            + 0.11 * max(row.avg_cycle_time - 60, 0)
            + 0.15 * row.avg_anomaly_signal
            + 0.10 * row.repeated_anomaly_hours
            + 0.05 * row.machine_age_years
            - maintenance_relief
        )
        probability = float(sigmoid(np.array([risk_logit]))[0])
        if rng.random() < probability:
            event_timestamp = row.date + pd.Timedelta(hours=int(rng.integers(0, 24)))
            event_rows.append(
                {
                    "downtime_event_id": f"DT_{row.machine_id}_{row.date.strftime('%Y%m%d')}",
                    "machine_id": row.machine_id,
                    "line_id": row.line_id,
                    "timestamp": event_timestamp,
                    "shift": assign_shift(event_timestamp.hour),
                    "root_cause": rng.choice(["Bearing wear", "Pressure instability", "Overheating", "Sensor drift"]),
                    "temperature": round(float(row.max_temperature), 2),
                    "vibration": round(float(row.max_vibration), 3),
                    "cycle_time": round(float(row.avg_cycle_time), 2),
                    "pressure_instability": round(float(row.avg_pressure_instability), 2),
                    "repeated_anomaly_hours": row.repeated_anomaly_hours,
                    "downtime_minutes": int(max(15, rng.normal(50 + row.avg_anomaly_signal * 12 + row.repeated_anomaly_hours * 4, 16))),
                }
            )
    return pd.DataFrame(event_rows).sort_values(["machine_id", "timestamp"]).reset_index(drop=True)


def build_ml_training_dataset(
    sensor_readings: pd.DataFrame,
    quality_checks: pd.DataFrame,
    downtime_events: pd.DataFrame,
) -> pd.DataFrame:
    sensor_features = (
        sensor_readings.assign(batch_slot=sensor_readings["timestamp"].dt.floor("4h"))
        .groupby(["machine_id", "line_id", "batch_slot", "shift"], as_index=False)
        .agg(
            avg_temperature=("temperature", "mean"),
            avg_vibration=("vibration", "mean"),
            avg_pressure=("pressure", "mean"),
            avg_cycle_time=("cycle_time", "mean"),
            avg_energy_consumption=("energy_consumption", "mean"),
            pressure_instability=("pressure_instability", "mean"),
            anomaly_signal=("sensor_anomaly_signal", "mean"),
            machine_age_years=("machine_age_years", "max"),
            days_since_maintenance=("days_since_maintenance", "min"),
            baseline_health_score=("baseline_health_score", "max"),
        )
        .rename(columns={"batch_slot": "timestamp"})
    )
    sensor_features["cycle_time_drift"] = (
        sensor_features["avg_cycle_time"] - sensor_features.groupby("machine_id")["avg_cycle_time"].transform("median")
    )
    sensor_features["pressure_deviation"] = (
        sensor_features["avg_pressure"] - sensor_features.groupby("machine_id")["avg_pressure"].transform("median")
    ).abs()
    sensor_features["night_shift_flag"] = (sensor_features["shift"] == "Night").astype(int)
    sensor_features["maintenance_recency_score"] = np.clip(30 - sensor_features["days_since_maintenance"], 0, 30)

    downtime_daily = downtime_events.copy()
    if downtime_daily.empty:
        downtime_daily = pd.DataFrame(columns=["machine_id", "date", "downtime_minutes"])
    else:
        downtime_daily["date"] = pd.to_datetime(downtime_daily["timestamp"]).dt.date
        downtime_daily = downtime_daily.groupby(["machine_id", "date"], as_index=False).agg(
            previous_downtime_minutes=("downtime_minutes", "sum"),
            downtime_event_count=("downtime_event_id", "count"),
        )

    quality_agg = quality_checks.groupby(["machine_id", "timestamp"], as_index=False).agg(
        defect_flag=("defect_flag", "max"),
        defect_count=("defect_count", "sum"),
        defect_probability=("defect_probability", "mean"),
    )

    dataset = sensor_features.merge(quality_agg, on=["machine_id", "timestamp"], how="left")
    dataset["date"] = pd.to_datetime(dataset["timestamp"]).dt.date
    dataset = dataset.merge(downtime_daily, on=["machine_id", "date"], how="left")
    dataset["previous_downtime_minutes"] = dataset["previous_downtime_minutes"].fillna(0)
    dataset["downtime_event_count"] = dataset["downtime_event_count"].fillna(0)
    dataset["defect_flag"] = dataset["defect_flag"].fillna(0).astype(int)
    dataset["defect_count"] = dataset["defect_count"].fillna(0).astype(int)
    dataset["defect_probability"] = dataset["defect_probability"].fillna(0.0)
    dataset["quality_risk_index"] = (
        0.32 * np.maximum(dataset["avg_temperature"] - 76, 0)
        + 5.6 * np.maximum(dataset["avg_vibration"] - 2.3, 0)
        + 0.55 * np.maximum(dataset["cycle_time_drift"], 0)
        + 0.55 * dataset["pressure_instability"]
    )
    dataset["anomaly_count_24h"] = (
        dataset.sort_values("timestamp")
        .groupby("machine_id")["anomaly_signal"]
        .transform(lambda values: values.rolling(window=6, min_periods=1).apply(lambda x: float((x > 2.5).sum())))
    )
    dataset["yield_rate"] = safe_divide(100 - dataset["defect_count"], np.repeat(100, len(dataset)))
    return dataset.drop(columns=["date"])


def main() -> None:
    """Generate the synthetic manufacturing data used by the production-oriented prototype."""
    ensure_directories()
    rng = np.random.default_rng(SEED)

    machines = build_machines(rng)
    maintenance_logs = build_maintenance_logs(machines, rng)
    sensor_readings = build_sensor_readings(machines, maintenance_logs, rng)
    production_batches = build_production_batches(sensor_readings, rng)
    quality_checks = build_quality_checks(machines, production_batches, sensor_readings, rng)
    downtime_events = build_downtime_events(machines, maintenance_logs, sensor_readings, rng)
    ml_training_dataset = build_ml_training_dataset(sensor_readings, quality_checks, downtime_events)

    machines.to_csv(settings.raw_data_dir / "machines.csv", index=False)
    production_batches.to_csv(settings.raw_data_dir / "production_batches.csv", index=False)
    sensor_readings.to_csv(settings.raw_data_dir / "sensor_readings.csv", index=False)
    quality_checks.to_csv(settings.raw_data_dir / "quality_checks.csv", index=False)
    downtime_events.to_csv(settings.raw_data_dir / "downtime_events.csv", index=False)
    maintenance_logs.to_csv(settings.raw_data_dir / "maintenance_logs.csv", index=False)
    ml_training_dataset.to_csv(settings.processed_data_dir / "ml_training_dataset.csv", index=False)
    ml_training_dataset.to_csv(settings.processed_data_dir / "model_features.csv", index=False)

    print("Synthetic manufacturing data generated for the production-oriented prototype.")
    print(f"Machines: {len(machines)}")
    print(f"Sensor readings: {len(sensor_readings)}")
    print(f"Quality checks: {len(quality_checks)}")
    print(f"Downtime events: {len(downtime_events)}")


if __name__ == "__main__":
    main()


from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from utils import PROCESSED_DATA_DIR, RAW_DATA_DIR, ensure_directories, safe_divide


SEED = 42
NUM_MACHINES = 30
NUM_LINES = 3
NUM_DAYS = 60
START_DATE = pd.Timestamp("2026-01-01 00:00:00")
PRODUCT_TYPES = ["SUV Frame", "Battery Module", "Steering Column"]
DEFECT_TYPES = ["Surface", "Dimensional", "Assembly", "Electrical"]
OPERATOR_TEAMS = ["Team A", "Team B", "Team C", "Team D"]


@dataclass
class ShiftConfig:
    name: str
    vibration_bias: float
    temperature_bias: float
    variance_multiplier: float


SHIFT_CONFIGS = {
    0: ShiftConfig("Night", 0.14, 1.8, 1.18),
    1: ShiftConfig("Day", 0.00, 0.0, 1.00),
    2: ShiftConfig("Evening", 0.08, 0.9, 1.08),
}


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-values))


def assign_shift(hour: int) -> str:
    if 0 <= hour < 8:
        return SHIFT_CONFIGS[0].name
    if 8 <= hour < 16:
        return SHIFT_CONFIGS[1].name
    return SHIFT_CONFIGS[2].name


def build_machines(rng: np.random.Generator) -> pd.DataFrame:
    machine_ids = [f"M{idx:03d}" for idx in range(1, NUM_MACHINES + 1)]
    line_ids = [f"L{((idx - 1) % NUM_LINES) + 1}" for idx in range(1, NUM_MACHINES + 1)]
    machine_age = rng.integers(2, 16, size=NUM_MACHINES)
    last_maintenance_gap = rng.integers(3, 35, size=NUM_MACHINES)
    maintenance_status = np.where(last_maintenance_gap <= 10, "recent", np.where(last_maintenance_gap <= 20, "scheduled", "overdue"))

    machines = pd.DataFrame(
        {
            "machine_id": machine_ids,
            "line_id": line_ids,
            "machine_age_years": machine_age,
            "machine_type": rng.choice(["Weld", "Paint", "Assembly", "Inspection"], size=NUM_MACHINES),
            "installation_year": 2026 - machine_age,
            "baseline_cycle_time_seconds": np.round(rng.normal(57, 5, size=NUM_MACHINES), 2),
            "baseline_temperature": np.round(rng.normal(73, 4, size=NUM_MACHINES), 2),
            "baseline_vibration": np.round(rng.normal(2.2, 0.4, size=NUM_MACHINES), 3),
            "baseline_pressure": np.round(rng.normal(99, 5, size=NUM_MACHINES), 2),
            "last_maintenance_days_ago": last_maintenance_gap,
            "maintenance_status": maintenance_status,
        }
    )
    return machines


def build_sensor_readings(machines: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    timestamps = pd.date_range(START_DATE, periods=NUM_DAYS * 24, freq="h")
    records = []

    for machine in machines.itertuples(index=False):
        age_factor = machine.machine_age_years / 12
        maintenance_relief = max(0, (18 - machine.last_maintenance_days_ago) / 18)

        for timestamp in timestamps:
            shift_name = assign_shift(timestamp.hour)
            shift_cfg = next(config for config in SHIFT_CONFIGS.values() if config.name == shift_name)
            day_index = (timestamp - timestamps[0]).days
            drift = 0.01 * day_index + 0.04 * age_factor
            seasonal = np.sin(timestamp.hour / 24 * 2 * np.pi)
            line_load = 1 + (int(machine.line_id[-1]) - 2) * 0.03

            temperature = (
                machine.baseline_temperature
                + 1.6 * seasonal
                + 4.0 * age_factor
                + shift_cfg.temperature_bias
                + rng.normal(0, 1.3 * shift_cfg.variance_multiplier)
                - 1.2 * maintenance_relief
            )
            vibration = (
                machine.baseline_vibration
                + 0.14 * day_index / 7
                + 0.45 * age_factor
                + shift_cfg.vibration_bias
                + rng.normal(0, 0.18 * shift_cfg.variance_multiplier)
                - 0.08 * maintenance_relief
            )
            pressure = (
                machine.baseline_pressure
                + 2.4 * seasonal
                - 2.0 * drift
                + rng.normal(0, 1.7 * shift_cfg.variance_multiplier)
            )
            cycle_time = (
                machine.baseline_cycle_time_seconds
                * line_load
                * (1 + drift / 9)
                + rng.normal(0, 1.9 * shift_cfg.variance_multiplier)
                - 0.9 * maintenance_relief
            )
            pressure_instability = abs(pressure - machine.baseline_pressure)
            anomaly_signal = (
                0.18 * max(temperature - 80, 0)
                + 0.9 * max(vibration - 2.8, 0)
                + 0.12 * pressure_instability
                + 0.08 * max(cycle_time - machine.baseline_cycle_time_seconds - 5, 0)
                + 0.45 * age_factor
            )
            energy_consumption = (
                108
                + 0.65 * cycle_time
                + 2.8 * vibration
                + 0.22 * temperature
                + rng.normal(0, 2.5)
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
                    "maintenance_status": machine.maintenance_status,
                    "last_maintenance_days_ago": machine.last_maintenance_days_ago,
                    "pressure_instability": round(float(pressure_instability), 2),
                    "sensor_anomaly_signal": round(float(anomaly_signal), 3),
                }
            )

    return pd.DataFrame(records)


def build_batches(sensor_readings: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    batched = sensor_readings.copy()
    batched["batch_slot"] = batched["timestamp"].dt.floor("4h")

    batch_rows = []
    for row in (
        batched.groupby(["line_id", "batch_slot", "shift"], as_index=False)
        .agg(
            avg_temperature=("temperature", "mean"),
            avg_vibration=("vibration", "mean"),
            avg_pressure=("pressure", "mean"),
            avg_cycle_time=("cycle_time", "mean"),
            avg_energy=("energy_consumption", "mean"),
            sensor_anomaly_signal=("sensor_anomaly_signal", "mean"),
        )
        .itertuples(index=False)
    ):
        batch_id = f"B{row.batch_slot.strftime('%Y%m%d%H')}_{row.line_id}"
        product_type = PRODUCT_TYPES[(int(row.line_id[-1]) - 1 + row.batch_slot.day) % len(PRODUCT_TYPES)]
        material_batch = f"MAT-{row.batch_slot.strftime('%m%d')}-{row.line_id}"
        operator_team = OPERATOR_TEAMS[(row.batch_slot.hour // 4 + int(row.line_id[-1])) % len(OPERATOR_TEAMS)]
        planned_units = int(rng.integers(180, 240))
        cycle_penalty = max(row.avg_cycle_time - 58, 0) * 0.7
        actual_units = int(max(planned_units - cycle_penalty - row.sensor_anomaly_signal * 4 + rng.normal(0, 5), 90))
        good_units = int(actual_units - max(row.sensor_anomaly_signal * 2 + rng.normal(6, 3), 0))

        batch_rows.append(
            {
                "batch_id": batch_id,
                "line_id": row.line_id,
                "timestamp": row.batch_slot,
                "shift": row.shift,
                "product_type": product_type,
                "material_batch": material_batch,
                "operator_team": operator_team,
                "planned_units": planned_units,
                "actual_units": actual_units,
                "good_units": max(min(good_units, actual_units), 0),
                "avg_temperature": round(float(row.avg_temperature), 2),
                "avg_vibration": round(float(row.avg_vibration), 3),
                "avg_pressure": round(float(row.avg_pressure), 2),
                "avg_cycle_time": round(float(row.avg_cycle_time), 2),
                "avg_energy_consumption": round(float(row.avg_energy), 2),
            }
        )

    return pd.DataFrame(batch_rows)


def build_quality_checks(
    production_batches: pd.DataFrame,
    machines: pd.DataFrame,
    sensor_readings: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    batch_machine_features = (
        sensor_readings.assign(batch_slot=sensor_readings["timestamp"].dt.floor("4h"))
        .groupby(["line_id", "batch_slot", "machine_id"], as_index=False)
        .agg(
            avg_temperature=("temperature", "mean"),
            avg_vibration=("vibration", "mean"),
            avg_pressure=("pressure", "mean"),
            avg_cycle_time=("cycle_time", "mean"),
            pressure_instability=("pressure_instability", "mean"),
            anomaly_signal=("sensor_anomaly_signal", "mean"),
        )
    )
    machine_age = machines[["machine_id", "machine_age_years", "last_maintenance_days_ago"]]
    batch_machine_features = batch_machine_features.merge(machine_age, on="machine_id", how="left")

    quality_rows = []
    for row in batch_machine_features.itertuples(index=False):
        cycle_drift = row.avg_cycle_time - 58
        logit = (
            -4.3
            + 0.075 * (row.avg_temperature - 76)
            + 1.10 * (row.avg_vibration - 2.3)
            + 0.045 * max(cycle_drift, 0)
            + 0.05 * row.pressure_instability
            + 0.06 * row.machine_age_years
            + 0.18 * row.anomaly_signal
            + (0.28 if row.batch_slot.hour < 8 else 0.0)
        )
        defect_probability = float(sigmoid(np.array([logit]))[0])
        defect_flag = int(rng.random() < defect_probability)
        if defect_flag:
            if row.avg_vibration > 2.8:
                defect_type = "Assembly"
            elif row.avg_temperature > 80:
                defect_type = "Surface"
            elif row.pressure_instability > 4:
                defect_type = "Dimensional"
            else:
                defect_type = rng.choice(DEFECT_TYPES)
        else:
            defect_type = "None"

        defect_count = int(max(0, rng.poisson(lam=defect_probability * 6)))
        quality_rows.append(
            {
                "quality_check_id": f"QC_{row.machine_id}_{row.batch_slot.strftime('%Y%m%d%H')}",
                "batch_id": f"B{row.batch_slot.strftime('%Y%m%d%H')}_{row.line_id}",
                "machine_id": row.machine_id,
                "line_id": row.line_id,
                "timestamp": row.batch_slot,
                "shift": assign_shift(row.batch_slot.hour),
                "temperature": round(float(row.avg_temperature), 2),
                "vibration": round(float(row.avg_vibration), 3),
                "pressure": round(float(row.avg_pressure), 2),
                "cycle_time": round(float(row.avg_cycle_time), 2),
                "machine_age_years": row.machine_age_years,
                "maintenance_status": "recent" if row.last_maintenance_days_ago <= 10 else "scheduled" if row.last_maintenance_days_ago <= 20 else "overdue",
                "product_type": production_batches.loc[production_batches["batch_id"] == f"B{row.batch_slot.strftime('%Y%m%d%H')}_{row.line_id}", "product_type"].iloc[0],
                "material_batch": production_batches.loc[production_batches["batch_id"] == f"B{row.batch_slot.strftime('%Y%m%d%H')}_{row.line_id}", "material_batch"].iloc[0],
                "operator_team": production_batches.loc[production_batches["batch_id"] == f"B{row.batch_slot.strftime('%Y%m%d%H')}_{row.line_id}", "operator_team"].iloc[0],
                "pressure_instability": round(float(row.pressure_instability), 2),
                "defect_probability": round(defect_probability, 4),
                "defect_flag": defect_flag,
                "defect_type": defect_type,
                "defect_count": defect_count,
            }
        )
    return pd.DataFrame(quality_rows)


def build_maintenance_logs(machines: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    log_rows = []
    for machine in machines.itertuples(index=False):
        event_count = int(rng.integers(2, 5))
        for offset_days in sorted(rng.choice(np.arange(1, NUM_DAYS + 20), size=event_count, replace=False)):
            event_timestamp = START_DATE + pd.Timedelta(days=int(offset_days), hours=int(rng.integers(6, 18)))
            maintenance_type = "Preventive" if offset_days >= machine.last_maintenance_days_ago else "Corrective"
            log_rows.append(
                {
                    "maintenance_id": f"MT_{machine.machine_id}_{offset_days}",
                    "machine_id": machine.machine_id,
                    "line_id": machine.line_id,
                    "timestamp": event_timestamp,
                    "maintenance_type": maintenance_type,
                    "technician_team": rng.choice(["Mech-1", "Mech-2", "Elec-1"]),
                    "parts_replaced": rng.choice(["Bearing", "Seal", "Valve", "Sensor", "None"]),
                    "downtime_minutes": int(max(20, rng.normal(75 if maintenance_type == 'Corrective' else 45, 15))),
                    "maintenance_status_after": "recent",
                }
            )
    return pd.DataFrame(log_rows).sort_values("timestamp")


def build_downtime_events(
    sensor_readings: pd.DataFrame,
    machines: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    event_rows = []
    sensor_with_keys = sensor_readings.copy()
    sensor_with_keys["date"] = sensor_with_keys["timestamp"].dt.date
    daily_candidates = sensor_with_keys.groupby(["machine_id", "date"], as_index=False).agg(
        max_temperature=("temperature", "max"),
        max_vibration=("vibration", "max"),
        avg_cycle_time=("cycle_time", "mean"),
        avg_anomaly_signal=("sensor_anomaly_signal", "mean"),
        max_pressure_instability=("pressure_instability", "max"),
    )
    machines_lookup = machines.set_index("machine_id")

    for row in daily_candidates.itertuples(index=False):
        machine = machines_lookup.loc[row.machine_id]
        maintenance_modifier = -0.07 if machine.last_maintenance_days_ago <= 10 else 0.08
        risk_logit = (
            -3.4
            + 0.12 * max(row.max_temperature - 81, 0)
            + 1.05 * max(row.max_vibration - 2.9, 0)
            + 0.10 * max(row.avg_cycle_time - machine.baseline_cycle_time_seconds - 4, 0)
            + 0.05 * row.max_pressure_instability
            + 0.12 * row.avg_anomaly_signal
            + 0.05 * machine.machine_age_years
            + maintenance_modifier
        )
        probability = float(sigmoid(np.array([risk_logit]))[0])
        if rng.random() < probability:
            event_timestamp = pd.Timestamp(row.date) + pd.Timedelta(hours=int(rng.integers(0, 24)))
            downtime_minutes = int(max(15, rng.normal(65 + row.avg_anomaly_signal * 10, 18)))
            event_rows.append(
                {
                    "downtime_event_id": f"DT_{row.machine_id}_{pd.Timestamp(row.date).strftime('%Y%m%d')}",
                    "machine_id": row.machine_id,
                    "line_id": machine.line_id,
                    "timestamp": event_timestamp,
                    "shift": assign_shift(event_timestamp.hour),
                    "root_cause": rng.choice(["Bearing wear", "Pressure instability", "Overheating", "Sensor drift"]),
                    "temperature": round(float(row.max_temperature), 2),
                    "vibration": round(float(row.max_vibration), 3),
                    "cycle_time": round(float(row.avg_cycle_time), 2),
                    "pressure_instability": round(float(row.max_pressure_instability), 2),
                    "downtime_minutes": downtime_minutes,
                }
            )

    return pd.DataFrame(event_rows).sort_values("timestamp")


def build_processed_features(
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
            last_maintenance_days_ago=("last_maintenance_days_ago", "max"),
        )
        .rename(columns={"batch_slot": "timestamp"})
    )

    quality_agg = quality_checks.groupby(["machine_id", "timestamp"], as_index=False).agg(
        defect_flag=("defect_flag", "max"),
        defect_count=("defect_count", "sum"),
    )
    downtime_events = downtime_events.copy()
    downtime_events["date"] = downtime_events["timestamp"].dt.date
    daily_downtime = downtime_events.groupby(["machine_id", "date"], as_index=False).agg(
        previous_downtime_minutes=("downtime_minutes", "sum")
    )

    features = sensor_features.merge(quality_agg, on=["machine_id", "timestamp"], how="left")
    features["date"] = features["timestamp"].dt.date
    features = features.merge(daily_downtime, on=["machine_id", "date"], how="left")
    features["previous_downtime_minutes"] = features["previous_downtime_minutes"].fillna(0)
    features["cycle_time_drift"] = features["avg_cycle_time"] - features.groupby("machine_id")["avg_cycle_time"].transform("median")
    features["pressure_deviation"] = (features["avg_pressure"] - features.groupby("machine_id")["avg_pressure"].transform("median")).abs()
    features["night_shift_flag"] = (features["shift"] == "Night").astype(int)
    features["maintenance_recency_score"] = np.clip(30 - features["last_maintenance_days_ago"], 0, 30)
    features["quality_risk_index"] = (
        0.35 * np.maximum(features["avg_temperature"] - 76, 0)
        + 6.0 * np.maximum(features["avg_vibration"] - 2.3, 0)
        + 0.6 * np.maximum(features["cycle_time_drift"], 0)
        + 0.5 * features["pressure_instability"]
    )
    features["defect_flag"] = features["defect_flag"].fillna(0).astype(int)
    features["defect_count"] = features["defect_count"].fillna(0).astype(int)
    features["yield_rate"] = safe_divide(features["defect_count"].rsub(100), np.repeat(100, len(features)))
    return features.drop(columns=["date"])


def main() -> None:
    ensure_directories()
    rng = np.random.default_rng(SEED)

    machines = build_machines(rng)
    sensor_readings = build_sensor_readings(machines, rng)
    production_batches = build_batches(sensor_readings, rng)
    quality_checks = build_quality_checks(production_batches, machines, sensor_readings, rng)
    downtime_events = build_downtime_events(sensor_readings, machines, rng)
    maintenance_logs = build_maintenance_logs(machines, rng)
    processed_features = build_processed_features(sensor_readings, quality_checks, downtime_events)

    machines.to_csv(RAW_DATA_DIR / "machines.csv", index=False)
    production_batches.to_csv(RAW_DATA_DIR / "production_batches.csv", index=False)
    sensor_readings.to_csv(RAW_DATA_DIR / "sensor_readings.csv", index=False)
    quality_checks.to_csv(RAW_DATA_DIR / "quality_checks.csv", index=False)
    downtime_events.to_csv(RAW_DATA_DIR / "downtime_events.csv", index=False)
    maintenance_logs.to_csv(RAW_DATA_DIR / "maintenance_logs.csv", index=False)
    processed_features.to_csv(PROCESSED_DATA_DIR / "model_features.csv", index=False)

    print("Synthetic manufacturing prototype data generated.")
    print(f"Machines: {len(machines)}")
    print(f"Sensor readings: {len(sensor_readings)}")
    print(f"Quality checks: {len(quality_checks)}")
    print(f"Downtime events: {len(downtime_events)}")


if __name__ == "__main__":
    main()

select
    machine_id,
    line_id,
    cast(timestamp as timestamp) as timestamp,
    shift,
    temperature,
    vibration,
    pressure,
    cycle_time,
    energy_consumption,
    machine_age_years,
    machine_type,
    baseline_health_score,
    days_since_maintenance,
    maintenance_status,
    pressure_instability,
    sensor_anomaly_signal
from {{ source('ops_raw', 'sensor_readings') }}

select
    machine_id,
    line_id,
    machine_type,
    machine_age_years,
    installation_year,
    baseline_health_score,
    baseline_cycle_time_seconds,
    baseline_temperature,
    baseline_vibration,
    baseline_pressure
from {{ source('ops_raw', 'machines') }}

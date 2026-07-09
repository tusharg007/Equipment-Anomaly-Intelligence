with sensor as (
    select * from {{ ref('stg_sensor_readings') }}
)
select
    machine_id,
    line_id,
    date_trunc('day', timestamp) as metric_day,
    avg(temperature) as avg_temperature,
    avg(vibration) as avg_vibration,
    avg(pressure) as avg_pressure,
    avg(cycle_time) as avg_cycle_time,
    avg(energy_consumption) as avg_energy_consumption,
    avg(sensor_anomaly_signal) as avg_sensor_anomaly_signal,
    max(machine_age_years) as machine_age_years,
    max(last_maintenance_days_ago) as last_maintenance_days_ago
from sensor
group by 1, 2, 3

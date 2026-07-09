with sensor as (
    select * from {{ ref('stg_sensor_readings') }}
),
downtime as (
    select
        machine_id,
        date_trunc('day', timestamp) as event_day,
        sum(downtime_minutes) as downtime_minutes_day
    from {{ ref('stg_downtime_events') }}
    group by 1, 2
)
select
    sensor.machine_id,
    sensor.line_id,
    date_trunc('hour', sensor.timestamp) as metric_hour,
    sensor.shift,
    avg(sensor.temperature) as avg_temperature,
    avg(sensor.vibration) as avg_vibration,
    avg(sensor.pressure) as avg_pressure,
    avg(sensor.cycle_time) as avg_cycle_time,
    avg(sensor.energy_consumption) as avg_energy_consumption,
    avg(sensor.pressure_instability) as avg_pressure_instability,
    avg(sensor.sensor_anomaly_signal) as avg_sensor_anomaly_signal,
    max(sensor.machine_age_years) as machine_age_years,
    max(sensor.days_since_maintenance) as days_since_maintenance,
    max(sensor.baseline_health_score) as baseline_health_score,
    coalesce(max(downtime.downtime_minutes_day), 0) as downtime_minutes_day
from sensor
left join downtime
    on sensor.machine_id = downtime.machine_id
   and date_trunc('day', sensor.timestamp) = downtime.event_day
group by 1, 2, 3, 4

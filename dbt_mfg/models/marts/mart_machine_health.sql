with hourly as (
    select * from {{ ref('int_machine_hourly_metrics') }}
),
maintenance as (
    select
        machine_id,
        max(timestamp) as latest_maintenance_ts
    from {{ ref('stg_maintenance_logs') }}
    group by 1
)
select
    hourly.machine_id,
    hourly.line_id,
    avg(hourly.avg_temperature) as avg_temperature,
    avg(hourly.avg_vibration) as avg_vibration,
    avg(hourly.avg_cycle_time) as avg_cycle_time,
    avg(hourly.avg_sensor_anomaly_signal) as avg_anomaly_signal,
    sum(case when hourly.avg_sensor_anomaly_signal > 2.5 then 1 else 0 end) as high_anomaly_hours,
    sum(hourly.downtime_minutes_day) as total_downtime_minutes,
    max(hourly.machine_age_years) as machine_age_years,
    max(hourly.days_since_maintenance) as days_since_maintenance,
    max(hourly.baseline_health_score) as baseline_health_score,
    max(maintenance.latest_maintenance_ts) as latest_maintenance_ts
from hourly
left join maintenance
    on hourly.machine_id = maintenance.machine_id
group by 1, 2

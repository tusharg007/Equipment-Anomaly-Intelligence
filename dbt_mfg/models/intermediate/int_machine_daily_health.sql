with sensor_daily as (
    select
        machine_id,
        line_id,
        cast(date_trunc('day', timestamp) as date) as metric_day,
        avg(temperature) as daily_avg_temperature,
        avg(vibration) as daily_avg_vibration,
        avg(pressure) as daily_avg_pressure,
        avg(cycle_time) as daily_avg_cycle_time,
        avg(energy_consumption) as daily_avg_energy_consumption,
        count(*) filter (where sensor_anomaly_signal > 2.5) as daily_anomaly_count
    from {{ ref('stg_sensor_readings') }}
    group by 1, 2, 3
),
downtime_daily as (
    select
        machine_id,
        cast(date_trunc('day', timestamp) as date) as metric_day,
        sum(downtime_minutes) as downtime_minutes
    from {{ ref('stg_downtime_events') }}
    group by 1, 2
),
maintenance_daily as (
    select
        sensor.machine_id,
        sensor.metric_day,
        max(maintenance.timestamp) as latest_maintenance_ts
    from sensor_daily as sensor
    left join {{ ref('stg_maintenance_logs') }} as maintenance
        on sensor.machine_id = maintenance.machine_id
       and maintenance.timestamp < sensor.metric_day + interval '1 day'
    group by 1, 2
)
select
    sensor.machine_id,
    sensor.line_id,
    sensor.metric_day,
    sensor.daily_avg_temperature,
    sensor.daily_avg_vibration,
    sensor.daily_avg_pressure,
    sensor.daily_avg_cycle_time,
    sensor.daily_avg_energy_consumption,
    sensor.daily_anomaly_count,
    coalesce(downtime.downtime_minutes, 0) as downtime_minutes,
    case
        when maintenance.latest_maintenance_ts is null then null
        else sensor.metric_day - cast(maintenance.latest_maintenance_ts as date)
    end as last_maintenance_days_ago
from sensor_daily as sensor
left join downtime_daily as downtime
    on sensor.machine_id = downtime.machine_id
   and sensor.metric_day = downtime.metric_day
left join maintenance_daily as maintenance
    on sensor.machine_id = maintenance.machine_id
   and sensor.metric_day = maintenance.metric_day

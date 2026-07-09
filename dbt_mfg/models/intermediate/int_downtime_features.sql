with downtime as (
    select * from {{ ref('stg_downtime_events') }}
)
select
    machine_id,
    line_id,
    date_trunc('day', timestamp) as metric_day,
    count(*) as downtime_event_count,
    sum(downtime_minutes) as downtime_minutes,
    avg(temperature) as avg_temperature,
    avg(vibration) as avg_vibration,
    avg(cycle_time) as avg_cycle_time,
    avg(pressure_instability) as avg_pressure_instability
from downtime
group by 1, 2, 3

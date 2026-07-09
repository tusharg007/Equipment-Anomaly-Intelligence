select
    downtime_event_id,
    machine_id,
    line_id,
    cast(timestamp as timestamp) as timestamp,
    shift,
    root_cause,
    temperature,
    vibration,
    cycle_time,
    pressure_instability,
    downtime_minutes
from {{ source('ops_raw', 'downtime_events') }}

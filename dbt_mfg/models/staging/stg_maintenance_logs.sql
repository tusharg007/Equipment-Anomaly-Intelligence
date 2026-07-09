select
    maintenance_id,
    machine_id,
    line_id,
    cast(timestamp as timestamp) as timestamp,
    maintenance_type,
    technician_team,
    parts_replaced,
    downtime_minutes,
    maintenance_status_after
from {{ source('ops_raw', 'maintenance_logs') }}

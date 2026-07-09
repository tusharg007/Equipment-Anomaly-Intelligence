select
    quality_check_id,
    batch_id,
    machine_id,
    line_id,
    cast(timestamp as timestamp) as timestamp,
    shift,
    temperature,
    vibration,
    pressure,
    cycle_time,
    machine_age_years,
    maintenance_status,
    product_type,
    material_batch,
    operator_team,
    pressure_instability,
    defect_probability,
    defect_flag,
    case
        when coalesce(defect_flag, 0) = 0 then 'No Defect'
        when nullif(trim(defect_type), '') is null then 'No Defect'
        else defect_type
    end as defect_type,
    defect_count
from {{ source('ops_raw', 'quality_checks') }}

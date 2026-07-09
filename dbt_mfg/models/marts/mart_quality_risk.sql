with features as (
    select * from {{ ref('int_batch_quality_features') }}
)
select
    batch_id,
    machine_id,
    line_id,
    timestamp,
    shift,
    product_type,
    material_batch,
    operator_team,
    avg_temperature,
    avg_vibration,
    avg_pressure,
    avg_cycle_time,
    avg_pressure_instability,
    machine_age_years,
    avg_defect_probability,
    defect_units,
    defect_count,
    case
        when avg_defect_probability >= 0.45 then 'High'
        when avg_defect_probability >= 0.25 then 'Medium'
        else 'Low'
    end as quality_risk_band
from features

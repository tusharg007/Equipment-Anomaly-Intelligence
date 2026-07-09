with quality as (
    select * from {{ ref('stg_quality_checks') }}
),
batches as (
    select * from {{ source('ops_raw', 'production_batches') }}
)
select
    quality.batch_id,
    quality.machine_id,
    quality.line_id,
    quality.timestamp,
    quality.shift,
    batches.product_type,
    batches.material_batch,
    batches.operator_team,
    avg(quality.temperature) as avg_temperature,
    avg(quality.vibration) as avg_vibration,
    avg(quality.pressure) as avg_pressure,
    avg(quality.cycle_time) as avg_cycle_time,
    avg(quality.pressure_instability) as avg_pressure_instability,
    max(quality.machine_age_years) as machine_age_years,
    avg(quality.defect_probability) as avg_defect_probability,
    sum(quality.defect_flag) as defect_units,
    sum(quality.defect_count) as defect_count
from quality
left join batches
    on quality.batch_id = batches.batch_id
group by 1, 2, 3, 4, 5, 6, 7, 8

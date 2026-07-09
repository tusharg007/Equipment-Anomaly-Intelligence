select
    batch_id,
    line_id,
    cast(timestamp as timestamp) as timestamp,
    shift,
    product_type,
    material_batch,
    operator_team,
    planned_units,
    actual_units,
    good_units,
    avg_temperature,
    avg_vibration,
    avg_pressure,
    avg_cycle_time,
    avg_energy_consumption,
    avg_pressure_instability,
    avg_anomaly_signal
from {{ source('ops_raw', 'production_batches') }}

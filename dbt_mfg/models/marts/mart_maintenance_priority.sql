with machine_health as (
    select * from {{ ref('mart_machine_health') }}
),
downtime as (
    select * from {{ ref('int_downtime_features') }}
)
select
    machine_health.machine_id,
    machine_health.line_id,
    machine_health.avg_temperature,
    machine_health.avg_vibration,
    machine_health.high_anomaly_hours,
    coalesce(sum(downtime.downtime_minutes), 0) as total_downtime_minutes,
    case
        when machine_health.high_anomaly_hours >= 40 then 'Critical'
        when machine_health.high_anomaly_hours >= 20 then 'High'
        when machine_health.high_anomaly_hours >= 8 then 'Medium'
        else 'Low'
    end as maintenance_risk_band,
    case
        when machine_health.high_anomaly_hours >= 40 then 'Urgent maintenance review'
        when machine_health.high_anomaly_hours >= 20 then 'Preventive maintenance'
        when machine_health.high_anomaly_hours >= 8 then 'Schedule inspection'
        else 'Monitor'
    end as maintenance_priority_recommendation
from machine_health
left join downtime
    on machine_health.machine_id = downtime.machine_id
group by 1, 2, 3, 4, 5
